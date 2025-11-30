"""
Script de teste para analisar perfis adaptativos de cada moeda
Descobre RSI mínimo/máximo histórico e thresholds ideais
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from src.strategies.adaptive_strategy import AdaptiveStrategy
from backend.config import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class SimpleExchangeClient:
    """Cliente simples usando API pública da Binance"""
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', since: int = None, limit: int = 1000):
        """Busca velas históricas via API pública"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {
                'symbol': symbol.replace('/', ''),
                'interval': timeframe,
                'limit': limit
            }
            
            if since:
                params['startTime'] = since
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Converte formato Binance para CCXT
            candles = [
                [k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])]
                for k in data
            ]
            
            return candles
            
        except Exception as e:
            logger.error(f"Erro ao buscar OHLCV de {symbol}: {e}")
            return None


def test_adaptive_strategy():
    """
    Testa a estratégia adaptativa:
    1. Analisa histórico de 7 dias
    2. Mostra perfil de cada moeda
    3. Mostra thresholds personalizados
    """
    
    print("=" * 80)
    print("ANÁLISE DE PERFIS ADAPTATIVOS - 8 CRIPTOMOEDAS")
    print("=" * 80)
    print()
    
    # Cria exchange client
    exchange = SimpleExchangeClient()
    
    # Cria configuração
    config = settings
    
    # Cria estratégia adaptativa (vai analisar histórico automaticamente)
    print("Analisando histórico de 7 dias de cada moeda...")
    print("Isso pode levar 1-2 minutos...\n")
    
    strategy = AdaptiveStrategy(exchange, config)
    
    # Mostra perfis
    print("\n" + "=" * 80)
    print("PERFIS DESCOBERTOS")
    print("=" * 80)
    
    for symbol in config.SYMBOLS:
        profile = strategy.crypto_profiles.get(symbol)
        
        if not profile:
            print(f"\n❌ {symbol}: Perfil não encontrado")
            continue
        
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║ {symbol:^76} ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  📊 HISTÓRICO 7 DIAS:                                                        ║
║     RSI Mínimo:        {profile['rsi_min']:6.1f}  (5% mais baixo)                          ║
║     RSI Máximo:        {profile['rsi_max']:6.1f}  (5% mais alto)                           ║
║                                                                              ║
║  🎯 THRESHOLDS ADAPTATIVOS:                                                  ║
║     Compra em RSI:     {profile['buy_rsi_threshold']:6.1f}  (personalizado para {symbol:8})            ║
║     Vende em RSI:      {profile['sell_rsi_threshold']:6.1f}  (personalizado para {symbol:8})            ║
║                                                                              ║
║  📈 CARACTERÍSTICAS:                                                         ║
║     Volatilidade:      {profile['volatility']:6.2f}%                                             ║
║     Volume Médio:      ${profile['avg_volume']:13,.0f}                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Comparação
    print("\n" + "=" * 80)
    print("COMPARAÇÃO DE THRESHOLDS")
    print("=" * 80)
    print(f"{'Moeda':<12} {'RSI Compra':<12} {'RSI Venda':<12} {'Volatilidade':<15} {'Volume/dia'}")
    print("-" * 80)
    
    for symbol in config.SYMBOLS:
        profile = strategy.crypto_profiles.get(symbol)
        if profile:
            print(f"{symbol:<12} {profile['buy_rsi_threshold']:>6.1f}        {profile['sell_rsi_threshold']:>6.1f}        {profile['volatility']:>5.2f}%          ${profile['avg_volume']:>12,.0f}")
    
    print("-" * 80)
    
    # Simulação de ajuste dinâmico
    print("\n" + "=" * 80)
    print("SIMULAÇÃO: AJUSTE DINÂMICO (quando fica sem trades)")
    print("=" * 80)
    
    test_symbol = "BTC/USDT"
    profile = strategy.crypto_profiles.get(test_symbol)
    
    if profile:
        base_threshold = profile['buy_rsi_threshold']
        
        print(f"\n{test_symbol} - RSI Compra Base: {base_threshold:.1f}")
        print()
        print(f"{'Situação':<30} {'RSI Threshold':<15} {'Explicação'}")
        print("-" * 80)
        print(f"{'Normal (trading ativo)':<30} {base_threshold:>6.1f}          Threshold padrão da moeda")
        print(f"{'Sem trades há 30 min':<30} {base_threshold + 2:>6.1f}          Relaxa +2 pontos")
        print(f"{'Sem trades há 1 hora':<30} {base_threshold + 4:>6.1f}          Relaxa +4 pontos")
        print(f"{'Sem trades há 2 horas':<30} {min(base_threshold + 6, 45):>6.1f}          Relaxa +6 pontos (max 45)")
        print("-" * 80)
        
        print("""
💡 EXPLICAÇÃO:
   - Se a moeda não atinge RSI muito baixo, o bot relaxa entrada
   - Garante que sempre tem oportunidades de trade
   - Limite máximo: RSI 45 (não compra em overbought)
""")
    
    # Melhores moedas para operar agora
    print("\n" + "=" * 80)
    print("MELHORES MOEDAS PARA OPERAR (simulação)")
    print("=" * 80)
    
    best = strategy.get_best_symbols_to_trade(n=4)
    
    print("\nTop 4 moedas priorizadas:")
    for i, symbol in enumerate(best, 1):
        profile = strategy.crypto_profiles.get(symbol)
        print(f"  {i}. {symbol:<12} (Vol: {profile['volatility']:.2f}%, Volume: ${profile['avg_volume']:,.0f})")
    
    print("\n💡 Priorização baseada em: volatilidade, volume, tempo sem operar")
    
    print("\n" + "=" * 80)
    print("✅ ANÁLISE COMPLETA!")
    print("=" * 80)
    print("""
PRÓXIMOS PASSOS:
1. Integrar adaptive_strategy.py no trading engine
2. Bot vai operar cada moeda com seu próprio threshold
3. Meta: $100/dia através de trades adaptativos

VANTAGENS:
✅ Não fica parado (relaxa threshold se sem trades)
✅ Cada moeda tem estratégia personalizada
✅ Aprende comportamento histórico real
✅ Segura posições em tendência de alta
✅ Vende quando tendência vira queda
""")


if __name__ == "__main__":
    test_adaptive_strategy()
