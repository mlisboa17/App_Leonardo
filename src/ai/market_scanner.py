# -*- coding: utf-8 -*-
"""
App Leonardo v3.0 - Scanner de Mercado e Notícias
=================================================

Scanner que busca informações relevantes de mercado:
- Notícias de criptomoedas
- Análise de sentimento
- Eventos importantes
- Fear & Greed Index
- Dados de dominância BTC

Features FREE usadas:
- RSS feeds de sites de crypto
- CoinGecko API (gratuita)
- Alternative.me Fear & Greed API
- Análise de sentimento com TextBlob
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import requests_cache
import feedparser
from textblob import TextBlob

logger = logging.getLogger('MarketScanner')

# Configurar cache de requests (5 minutos)
requests_cache.install_cache(
    'market_scanner_cache',
    expire_after=300,  # 5 minutos
    backend='memory'
)


class MarketScanner:
    """
    Scanner de mercado que busca informações relevantes.
    
    Funcionalidades:
    - Busca notícias de crypto via RSS
    - Análise de sentimento das notícias
    - Fear & Greed Index
    - Preços e dominância via CoinGecko
    - Detecção de eventos importantes
    """
    
    # RSS Feeds gratuitos de crypto
    RSS_FEEDS = {
        'cointelegraph': 'https://cointelegraph.com/rss',
        'coindesk': 'https://www.coindesk.com/arc/outboundfeeds/rss/',
        'bitcoin_magazine': 'https://bitcoinmagazine.com/.rss/full/',
        'decrypt': 'https://decrypt.co/feed',
        'cryptoslate': 'https://cryptoslate.com/feed/',
    }
    
    # Palavras-chave importantes
    BULLISH_KEYWORDS = [
        'bullish', 'surge', 'rally', 'soars', 'jumps', 'gains', 'breakout',
        'all-time high', 'ath', 'moon', 'pump', 'adoption', 'approval',
        'etf approved', 'institutional', 'partnership', 'upgrade'
    ]
    
    BEARISH_KEYWORDS = [
        'bearish', 'crash', 'dump', 'plunge', 'drops', 'falls', 'selloff',
        'sell-off', 'fear', 'panic', 'hack', 'exploit', 'ban', 'regulation',
        'sec', 'lawsuit', 'fraud', 'scam', 'rug pull', 'liquidation'
    ]
    
    # Cryptos que monitoramos
    MONITORED_CRYPTOS = [
        'bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'sol', 'xrp', 'ripple',
        'cardano', 'ada', 'dogecoin', 'doge', 'shiba', 'shib', 'avalanche',
        'avax', 'polkadot', 'dot', 'chainlink', 'link', 'uniswap', 'uni',
        'litecoin', 'ltc', 'polygon', 'matic', 'atom', 'cosmos'
    ]
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.cache_dir = os.path.join(data_dir, "market_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Cache de notícias já processadas
        self.processed_news = set()
        self._load_processed_news()
        
        # Último scan
        self.last_scan = None
        self.scan_results = {}
        
        # Fear & Greed histórico
        self.fear_greed_history = []
        
    def _load_processed_news(self):
        """Carrega IDs de notícias já processadas"""
        try:
            cache_file = os.path.join(self.cache_dir, "processed_news.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.processed_news = set(json.load(f))
        except Exception as e:
            logger.warning(f"Erro ao carregar cache: {e}")
    
    def _save_processed_news(self):
        """Salva IDs de notícias processadas"""
        try:
            cache_file = os.path.join(self.cache_dir, "processed_news.json")
            # Manter apenas últimas 1000
            recent = list(self.processed_news)[-1000:]
            with open(cache_file, 'w') as f:
                json.dump(recent, f)
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def _generate_news_id(self, title: str, source: str) -> str:
        """Gera ID único para notícia"""
        content = f"{title}_{source}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def fetch_fear_greed_index(self) -> Dict:
        """
        Busca o Fear & Greed Index da Alternative.me API (gratuita).
        
        Returns:
            Dict com valor atual, classificação e histórico
        """
        try:
            url = "https://api.alternative.me/fng/?limit=7"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                current = data['data'][0]
                history = data['data'][1:] if len(data['data']) > 1 else []
                
                value = int(current['value'])
                classification = current['value_classification']
                
                # Determinar trend
                if history:
                    prev_value = int(history[0]['value'])
                    if value > prev_value + 5:
                        trend = 'improving'
                    elif value < prev_value - 5:
                        trend = 'worsening'
                    else:
                        trend = 'stable'
                else:
                    trend = 'unknown'
                
                result = {
                    'value': value,
                    'classification': classification,
                    'trend': trend,
                    'timestamp': datetime.fromtimestamp(int(current['timestamp'])).isoformat(),
                    'history': [
                        {'value': int(h['value']), 'date': datetime.fromtimestamp(int(h['timestamp'])).strftime('%Y-%m-%d')}
                        for h in history
                    ],
                    'interpretation': self._interpret_fear_greed(value)
                }
                
                self.fear_greed_history.append({
                    'value': value,
                    'timestamp': datetime.now().isoformat()
                })
                
                return result
            
        except Exception as e:
            logger.error(f"Erro ao buscar Fear & Greed: {e}")
        
        return {'value': 50, 'classification': 'Neutral', 'trend': 'unknown', 
                'interpretation': 'Não foi possível obter dados'}
    
    def _interpret_fear_greed(self, value: int) -> str:
        """Interpreta o valor do Fear & Greed para trading"""
        if value <= 20:
            return "🔴 MEDO EXTREMO - Possível oportunidade de compra (contrarian)"
        elif value <= 35:
            return "🟠 MEDO - Mercado pessimista, cuidado com posições"
        elif value <= 55:
            return "🟡 NEUTRO - Mercado indeciso, operar com cautela"
        elif value <= 75:
            return "🟢 GANÂNCIA - Mercado otimista, atenção a correções"
        else:
            return "🔴 GANÂNCIA EXTREMA - Possível topo, cuidado com FOMO"
    
    def fetch_global_market_data(self) -> Dict:
        """
        Busca dados globais do mercado via CoinGecko (gratuito).
        
        Returns:
            Dict com market cap, dominância BTC, volume 24h
        """
        try:
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()['data']
            
            return {
                'total_market_cap': data['total_market_cap'].get('usd', 0),
                'total_volume_24h': data['total_volume'].get('usd', 0),
                'btc_dominance': round(data['market_cap_percentage'].get('btc', 0), 2),
                'eth_dominance': round(data['market_cap_percentage'].get('eth', 0), 2),
                'market_cap_change_24h': round(data.get('market_cap_change_percentage_24h_usd', 0), 2),
                'active_cryptos': data.get('active_cryptocurrencies', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao buscar dados globais: {e}")
            return {}
    
    def fetch_trending_cryptos(self) -> List[Dict]:
        """
        Busca cryptos em tendência via CoinGecko.
        
        Returns:
            Lista de cryptos trending
        """
        try:
            url = "https://api.coingecko.com/api/v3/search/trending"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            trending = []
            for coin in data.get('coins', [])[:10]:
                item = coin.get('item', {})
                trending.append({
                    'name': item.get('name'),
                    'symbol': item.get('symbol', '').upper(),
                    'market_cap_rank': item.get('market_cap_rank'),
                    'score': item.get('score', 0)
                })
            
            return trending
        except Exception as e:
            logger.error(f"Erro ao buscar trending: {e}")
            return []
    
    def fetch_crypto_news(self, max_items: int = 20) -> List[Dict]:
        """
        Busca notícias de crypto via RSS feeds.
        
        Args:
            max_items: Número máximo de notícias
            
        Returns:
            Lista de notícias com análise de sentimento
        """
        all_news = []
        
        def fetch_feed(source: str, url: str) -> List[Dict]:
            """Fetch individual RSS feed"""
            try:
                feed = feedparser.parse(url)
                news_items = []
                
                for entry in feed.entries[:5]:  # 5 por fonte
                    title = entry.get('title', '')
                    summary = entry.get('summary', entry.get('description', ''))
                    link = entry.get('link', '')
                    published = entry.get('published', entry.get('updated', ''))
                    
                    # Gerar ID único
                    news_id = self._generate_news_id(title, source)
                    
                    # Pular se já processada
                    if news_id in self.processed_news:
                        continue
                    
                    # Análise de sentimento
                    sentiment = self._analyze_sentiment(title + " " + summary)
                    
                    # Detectar cryptos mencionadas
                    mentioned = self._detect_mentioned_cryptos(title + " " + summary)
                    
                    # Detectar keywords importantes
                    signals = self._detect_signals(title + " " + summary)
                    
                    news_items.append({
                        'id': news_id,
                        'source': source,
                        'title': title,
                        'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                        'link': link,
                        'published': published,
                        'sentiment': sentiment,
                        'mentioned_cryptos': mentioned,
                        'signals': signals,
                        'fetched_at': datetime.now().isoformat()
                    })
                    
                    self.processed_news.add(news_id)
                
                return news_items
            except Exception as e:
                logger.warning(f"Erro ao buscar {source}: {e}")
                return []
        
        # Buscar feeds em paralelo
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_feed, source, url): source
                for source, url in self.RSS_FEEDS.items()
            }
            
            for future in as_completed(futures):
                news_items = future.result()
                all_news.extend(news_items)
        
        # Salvar cache
        self._save_processed_news()
        
        # Ordenar por relevância (sentimento mais extremo primeiro)
        all_news.sort(key=lambda x: abs(x['sentiment']['score']), reverse=True)
        
        return all_news[:max_items]
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """
        Analisa o sentimento de um texto usando TextBlob.
        
        Args:
            text: Texto para análise
            
        Returns:
            Dict com score (-1 a 1), classificação e confiança
        """
        try:
            # Limpar texto
            clean_text = text.replace('<p>', ' ').replace('</p>', ' ')
            clean_text = clean_text.replace('<br>', ' ').replace('<br/>', ' ')
            
            blob = TextBlob(clean_text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Ajustar com keywords específicas de crypto
            keyword_adjustment = 0
            text_lower = text.lower()
            
            for keyword in self.BULLISH_KEYWORDS:
                if keyword in text_lower:
                    keyword_adjustment += 0.1
            
            for keyword in self.BEARISH_KEYWORDS:
                if keyword in text_lower:
                    keyword_adjustment -= 0.1
            
            # Score final (limitado a -1 a 1)
            final_score = max(-1, min(1, polarity + keyword_adjustment))
            
            # Classificação
            if final_score >= 0.3:
                classification = 'BULLISH'
                emoji = '🟢'
            elif final_score <= -0.3:
                classification = 'BEARISH'
                emoji = '🔴'
            else:
                classification = 'NEUTRAL'
                emoji = '🟡'
            
            return {
                'score': round(final_score, 3),
                'classification': classification,
                'emoji': emoji,
                'subjectivity': round(subjectivity, 2),
                'confidence': 'high' if abs(final_score) > 0.5 else 'medium' if abs(final_score) > 0.2 else 'low'
            }
        except Exception as e:
            logger.warning(f"Erro na análise de sentimento: {e}")
            return {'score': 0, 'classification': 'NEUTRAL', 'emoji': '🟡', 
                    'subjectivity': 0.5, 'confidence': 'low'}
    
    def _detect_mentioned_cryptos(self, text: str) -> List[str]:
        """Detecta quais cryptos são mencionadas no texto"""
        mentioned = []
        text_lower = text.lower()
        
        # Mapeamento para símbolos
        crypto_map = {
            'bitcoin': 'BTC', 'btc': 'BTC',
            'ethereum': 'ETH', 'eth': 'ETH',
            'solana': 'SOL', 'sol': 'SOL',
            'ripple': 'XRP', 'xrp': 'XRP',
            'cardano': 'ADA', 'ada': 'ADA',
            'dogecoin': 'DOGE', 'doge': 'DOGE',
            'shiba': 'SHIB', 'shib': 'SHIB',
            'avalanche': 'AVAX', 'avax': 'AVAX',
            'polkadot': 'DOT', 'dot': 'DOT',
            'chainlink': 'LINK', 'link': 'LINK',
            'uniswap': 'UNI', 'uni': 'UNI',
            'litecoin': 'LTC', 'ltc': 'LTC',
            'polygon': 'MATIC', 'matic': 'MATIC',
            'cosmos': 'ATOM', 'atom': 'ATOM'
        }
        
        for keyword, symbol in crypto_map.items():
            if keyword in text_lower and symbol not in mentioned:
                mentioned.append(symbol)
        
        return mentioned
    
    def _detect_signals(self, text: str) -> Dict:
        """Detecta sinais importantes no texto"""
        text_lower = text.lower()
        signals = {
            'bullish_signals': [],
            'bearish_signals': [],
            'importance': 'low'
        }
        
        for keyword in self.BULLISH_KEYWORDS:
            if keyword in text_lower:
                signals['bullish_signals'].append(keyword)
        
        for keyword in self.BEARISH_KEYWORDS:
            if keyword in text_lower:
                signals['bearish_signals'].append(keyword)
        
        # Determinar importância
        total_signals = len(signals['bullish_signals']) + len(signals['bearish_signals'])
        if total_signals >= 3:
            signals['importance'] = 'high'
        elif total_signals >= 1:
            signals['importance'] = 'medium'
        
        return signals
    
    def get_market_summary(self) -> Dict:
        """
        Gera um resumo completo do mercado.
        
        Returns:
            Dict com Fear & Greed, dados globais, news resumidas
        """
        logger.info("📡 Iniciando scan completo do mercado...")
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'fear_greed': {},
            'global_data': {},
            'trending': [],
            'news_summary': {},
            'overall_sentiment': 'NEUTRAL',
            'recommendations': []
        }
        
        # Fear & Greed
        summary['fear_greed'] = self.fetch_fear_greed_index()
        
        # Dados globais
        summary['global_data'] = self.fetch_global_market_data()
        
        # Trending
        summary['trending'] = self.fetch_trending_cryptos()
        
        # Notícias
        news = self.fetch_crypto_news(max_items=15)
        
        # Resumir sentimento das notícias
        if news:
            sentiments = [n['sentiment']['score'] for n in news]
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            bullish_count = sum(1 for n in news if n['sentiment']['classification'] == 'BULLISH')
            bearish_count = sum(1 for n in news if n['sentiment']['classification'] == 'BEARISH')
            
            summary['news_summary'] = {
                'total_news': len(news),
                'avg_sentiment': round(avg_sentiment, 3),
                'bullish_count': bullish_count,
                'bearish_count': bearish_count,
                'neutral_count': len(news) - bullish_count - bearish_count,
                'top_mentioned': self._get_top_mentioned(news),
                'recent_headlines': [n['title'] for n in news[:5]]
            }
        
        # Determinar sentimento geral
        fg_value = summary['fear_greed'].get('value', 50)
        news_sentiment = summary['news_summary'].get('avg_sentiment', 0)
        market_change = summary['global_data'].get('market_cap_change_24h', 0)
        
        score = (fg_value - 50) / 50 + news_sentiment + market_change / 10
        
        if score > 0.3:
            summary['overall_sentiment'] = 'BULLISH'
        elif score < -0.3:
            summary['overall_sentiment'] = 'BEARISH'
        else:
            summary['overall_sentiment'] = 'NEUTRAL'
        
        # Gerar recomendações
        summary['recommendations'] = self._generate_recommendations(summary)
        
        self.last_scan = datetime.now()
        self.scan_results = summary
        
        # Salvar resultado
        self._save_scan_result(summary)
        
        logger.info(f"✅ Scan concluído: {summary['overall_sentiment']}")
        return summary
    
    def _get_top_mentioned(self, news: List[Dict]) -> List[Dict]:
        """Retorna cryptos mais mencionadas nas notícias"""
        mentions = {}
        for n in news:
            for crypto in n.get('mentioned_cryptos', []):
                mentions[crypto] = mentions.get(crypto, 0) + 1
        
        sorted_mentions = sorted(mentions.items(), key=lambda x: x[1], reverse=True)
        return [{'symbol': m[0], 'count': m[1]} for m in sorted_mentions[:5]]
    
    def _generate_recommendations(self, summary: Dict) -> List[str]:
        """Gera recomendações baseadas no resumo"""
        recs = []
        
        # Fear & Greed
        fg_value = summary['fear_greed'].get('value', 50)
        if fg_value <= 25:
            recs.append("🔵 Fear & Greed em MEDO EXTREMO - Considere compras graduais (DCA)")
        elif fg_value >= 75:
            recs.append("🔴 Fear & Greed em GANÂNCIA EXTREMA - Considere realizar lucros")
        
        # Market cap change
        change = summary['global_data'].get('market_cap_change_24h', 0)
        if change < -5:
            recs.append("📉 Mercado caiu >5% em 24h - Possíveis oportunidades de compra")
        elif change > 5:
            recs.append("📈 Mercado subiu >5% em 24h - Cuidado com FOMO")
        
        # News sentiment
        news_sentiment = summary['news_summary'].get('avg_sentiment', 0)
        if news_sentiment < -0.3:
            recs.append("📰 Notícias predominantemente negativas - Mercado pode continuar em baixa")
        elif news_sentiment > 0.3:
            recs.append("📰 Notícias predominantemente positivas - Momentum favorável")
        
        # BTC dominance
        btc_dom = summary['global_data'].get('btc_dominance', 50)
        if btc_dom > 55:
            recs.append("₿ Dominância BTC alta - Altcoins podem underperformar")
        elif btc_dom < 45:
            recs.append("🎯 Dominância BTC baixa - Altcoin season possível")
        
        # Trending
        trending = summary.get('trending', [])
        if trending:
            top_trending = [t['symbol'] for t in trending[:3]]
            recs.append(f"🔥 Trending: {', '.join(top_trending)}")
        
        return recs
    
    def _save_scan_result(self, summary: Dict):
        """Salva resultado do scan em arquivo"""
        try:
            scan_file = os.path.join(self.cache_dir, "last_scan.json")
            with open(scan_file, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar scan: {e}")
    
    def get_crypto_sentiment(self, symbol: str) -> Dict:
        """
        Retorna sentimento específico para uma crypto.
        
        Args:
            symbol: Símbolo da crypto (ex: BTC, ETH)
            
        Returns:
            Dict com sentimento e notícias relacionadas
        """
        symbol = symbol.upper().replace('USDT', '')
        
        news = self.fetch_crypto_news(max_items=30)
        related_news = [n for n in news if symbol in n.get('mentioned_cryptos', [])]
        
        if not related_news:
            return {
                'symbol': symbol,
                'sentiment': 'UNKNOWN',
                'score': 0,
                'news_count': 0,
                'message': f'Nenhuma notícia recente sobre {symbol}'
            }
        
        avg_sentiment = sum(n['sentiment']['score'] for n in related_news) / len(related_news)
        
        if avg_sentiment > 0.2:
            sentiment = 'BULLISH'
        elif avg_sentiment < -0.2:
            sentiment = 'BEARISH'
        else:
            sentiment = 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'sentiment': sentiment,
            'score': round(avg_sentiment, 3),
            'news_count': len(related_news),
            'headlines': [n['title'] for n in related_news[:3]],
            'signals': {
                'bullish': sum(len(n['signals']['bullish_signals']) for n in related_news),
                'bearish': sum(len(n['signals']['bearish_signals']) for n in related_news)
            }
        }
    
    def should_trade_now(self) -> Dict:
        """
        Determina se é um bom momento para trading baseado em todos os indicadores.
        
        Returns:
            Dict com recomendação e razões
        """
        if not self.scan_results:
            self.get_market_summary()
        
        reasons = []
        score = 0
        
        # Fear & Greed (não muito extremo é bom)
        fg = self.scan_results.get('fear_greed', {}).get('value', 50)
        if 30 <= fg <= 70:
            score += 1
            reasons.append(f"✅ Fear & Greed em zona neutra ({fg})")
        else:
            score -= 1
            reasons.append(f"⚠️ Fear & Greed extremo ({fg})")
        
        # News sentiment
        news_sent = self.scan_results.get('news_summary', {}).get('avg_sentiment', 0)
        if news_sent > 0:
            score += 1
            reasons.append("✅ Sentimento de notícias positivo")
        elif news_sent < -0.2:
            score -= 1
            reasons.append("⚠️ Sentimento de notícias negativo")
        
        # Market trend
        change = self.scan_results.get('global_data', {}).get('market_cap_change_24h', 0)
        if -3 < change < 5:
            score += 1
            reasons.append("✅ Mercado estável/moderado")
        elif change < -5:
            score -= 1
            reasons.append("⚠️ Mercado em queda forte")
        
        # Resultado
        if score >= 2:
            recommendation = 'TRADE'
            message = '🟢 Condições favoráveis para trading'
        elif score <= -1:
            recommendation = 'WAIT'
            message = '🔴 Condições desfavoráveis - aguardar'
        else:
            recommendation = 'CAUTION'
            message = '🟡 Operar com cautela'
        
        return {
            'recommendation': recommendation,
            'message': message,
            'score': score,
            'reasons': reasons,
            'last_update': self.last_scan.isoformat() if self.last_scan else None
        }


# Teste standalone
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scanner = MarketScanner()
    
    print("\n📡 Buscando resumo do mercado...")
    summary = scanner.get_market_summary()
    
    print(f"\n📊 Fear & Greed: {summary['fear_greed'].get('value')} - {summary['fear_greed'].get('classification')}")
    print(f"📈 Market Cap Change 24h: {summary['global_data'].get('market_cap_change_24h')}%")
    print(f"₿ BTC Dominance: {summary['global_data'].get('btc_dominance')}%")
    print(f"📰 News Sentiment: {summary['news_summary'].get('avg_sentiment')}")
    print(f"🎯 Overall: {summary['overall_sentiment']}")
    
    print("\n💡 Recomendações:")
    for rec in summary.get('recommendations', []):
        print(f"  {rec}")
    
    print("\n🔮 Devo operar agora?")
    should = scanner.should_trade_now()
    print(f"  {should['message']}")
    for reason in should['reasons']:
        print(f"    {reason}")
