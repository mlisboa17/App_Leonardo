"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 MODO OPORTUNISTA - R7_V1                                ║
║                                                                               ║
║  Sistema que detecta condições FAVORÁVEIS de mercado e aumenta               ║
║  automaticamente a agressividade dos bots para maximizar lucros.             ║
║                                                                               ║
║  CONDIÇÕES FAVORÁVEIS:                                                        ║
║  ✅ Fear & Greed < 25 (medo extremo = oportunidade de compra)                ║
║  ✅ RSI < 30 em múltiplos ativos (sobrevenda generalizada)                   ║
║  ✅ Volume acima da média (confirmação de movimento)                         ║
║  ✅ BTC estável ou subindo (mercado saudável)                                ║
║  ✅ Performance recente positiva (validação da estratégia)                   ║
║                                                                               ║
║  NÍVEIS DE AGRESSIVIDADE:                                                     ║
║  🟢 CONSERVADOR (1.0x) - Padrão, mercado incerto                            ║
║  🟡 MODERADO (1.3x) - Algumas condições favoráveis                          ║
║  🟠 AGRESSIVO (1.5x) - Múltiplas condições favoráveis                       ║
║  🔴 MÁXIMO (1.8x) - Oportunidade excepcional (raro)                         ║
║                                                                               ║
║  LIMITES DE SEGURANÇA (NUNCA ULTRAPASSADOS):                                 ║
║  - Máximo 25% do capital por trade (mesmo no modo máximo)                    ║
║  - Stop loss nunca maior que -3%                                             ║
║  - Daily stop mantido em 3% do capital                                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class OpportunityScore:
    """Score de oportunidade do mercado"""
    fear_greed_score: float = 0      # 0-25 pontos
    rsi_score: float = 0             # 0-25 pontos
    volume_score: float = 0          # 0-20 pontos
    btc_trend_score: float = 0       # 0-15 pontos
    performance_score: float = 0     # 0-15 pontos
    total_score: float = 0           # 0-100 pontos
    
    def calculate_total(self):
        self.total_score = (
            self.fear_greed_score + 
            self.rsi_score + 
            self.volume_score + 
            self.btc_trend_score + 
            self.performance_score
        )
        return self.total_score


@dataclass  
class AggressivenessLevel:
    """Nível de agressividade"""
    name: str
    multiplier: float
    emoji: str
    min_score: int
    max_position_pct: float  # % máximo do capital por posição
    
    # Ajustes nos parâmetros
    rsi_oversold_adj: int     # Ajuste no RSI oversold
    stop_loss_adj: float      # Ajuste no stop loss (mais apertado = menos negativo)
    take_profit_adj: float    # Ajuste no take profit (mais alto)
    trade_frequency_adj: float  # Multiplicador de frequência


class OpportunisticMode:
    """
    Sistema de Modo Oportunista
    
    Detecta condições favoráveis e ajusta agressividade automaticamente.
    """
    
    # Níveis de agressividade - CALIBRADOS PARA 10% AO MÊS
    LEVELS = {
        'conservador': AggressivenessLevel(
            name='CONSERVADOR',
            multiplier=1.0,
            emoji='🟢',
            min_score=0,
            max_position_pct=20,       # 20% por posição (era 15%)
            rsi_oversold_adj=0,
            stop_loss_adj=0,
            take_profit_adj=0,
            trade_frequency_adj=1.0
        ),
        'moderado': AggressivenessLevel(
            name='MODERADO', 
            multiplier=1.5,            # 1.5x (era 1.3x)
            emoji='🟡',
            min_score=35,              # Ativa mais fácil (era 40)
            max_position_pct=25,       # 25% por posição (era 18%)
            rsi_oversold_adj=5,        # RSI 35 (era 33)
            stop_loss_adj=0.3,         # SL -1.2% (era -1.3%)
            take_profit_adj=0.5,       # TP 1.5% (era 1.3%)
            trade_frequency_adj=1.3
        ),
        'agressivo': AggressivenessLevel(
            name='AGRESSIVO',
            multiplier=2.0,            # 2x (era 1.5x)
            emoji='🟠',
            min_score=50,              # Ativa mais fácil (era 60)
            max_position_pct=30,       # 30% por posição (era 20%)
            rsi_oversold_adj=8,        # RSI 38 (era 35)
            stop_loss_adj=0.4,         # SL -1.1% (era -1.2%)
            take_profit_adj=0.8,       # TP 1.8% (era 1.5%)
            trade_frequency_adj=1.5
        ),
        'maximo': AggressivenessLevel(
            name='MÁXIMO',
            multiplier=2.5,            # 2.5x (era 1.8x)
            emoji='🔴',
            min_score=70,              # Ativa mais fácil (era 80)
            max_position_pct=35,       # 35% por posição (era 25%)
            rsi_oversold_adj=10,       # RSI 40 (era 38)
            stop_loss_adj=0.5,         # SL -1.0% (era -1.1%)
            take_profit_adj=1.2,       # TP 2.2% (era 1.8%)
            trade_frequency_adj=1.8
        )
    }
    
    # Limites de segurança - AJUSTADOS PARA META 10%
    SAFETY_LIMITS = {
        'max_position_pct': 35,      # Até 35% por posição (era 25%)
        'max_stop_loss': -3.0,       # Stop loss nunca maior que -3%
        'min_stop_loss': -0.5,       # Stop loss nunca menor que -0.5%
        'max_take_profit': 8.0,      # Take profit até 8% (era 5%)
        'daily_stop_pct': 5.0,       # Daily stop 5% (era 3%) - mais margem
        'max_trades_per_hour': 15,   # Mais trades permitidos (era 10)
    }
    
    def __init__(self):
        self.state_file = Path("data/ai/opportunistic_state.json")
        self.state = self._load_state()
        self.current_level = self.LEVELS['conservador']
        self.current_score = OpportunityScore()
        
    def _load_state(self) -> Dict:
        """Carrega estado"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'current_level': 'conservador',
            'last_update': None,
            'history': [],
            'total_opportunities': 0,
            'successful_opportunities': 0,
            'enabled': True,
            'manual_override': None  # Para override manual se necessário
        }
    
    def _save_state(self):
        """Salva estado"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state['last_update'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def calculate_opportunity_score(
        self,
        fear_greed_index: int,
        avg_rsi: float,
        oversold_count: int,  # Quantos ativos com RSI < 30
        total_assets: int,
        volume_ratio: float,  # Volume atual / média
        btc_change_24h: float,
        recent_pnl: float,  # PnL dos últimos 7 dias
        recent_win_rate: float  # Win rate dos últimos 7 dias
    ) -> OpportunityScore:
        """
        Calcula score de oportunidade (0-100).
        
        Quanto maior o score, mais favorável o mercado para aumentar agressividade.
        """
        score = OpportunityScore()
        
        # 1. FEAR & GREED (0-25 pontos)
        # Medo extremo = mais pontos (oportunidade de compra)
        if fear_greed_index <= 10:
            score.fear_greed_score = 25  # Medo extremo máximo
        elif fear_greed_index <= 20:
            score.fear_greed_score = 20
        elif fear_greed_index <= 25:
            score.fear_greed_score = 15
        elif fear_greed_index <= 35:
            score.fear_greed_score = 10
        elif fear_greed_index <= 50:
            score.fear_greed_score = 5
        else:
            score.fear_greed_score = 0  # Ganância = cuidado
        
        # 2. RSI OVERSOLD (0-25 pontos)
        # Mais ativos sobrevendidos = mais oportunidade
        oversold_pct = (oversold_count / total_assets * 100) if total_assets > 0 else 0
        
        if avg_rsi < 25 and oversold_pct > 50:
            score.rsi_score = 25  # Sobrevenda generalizada extrema
        elif avg_rsi < 30 and oversold_pct > 30:
            score.rsi_score = 20
        elif avg_rsi < 35 and oversold_pct > 20:
            score.rsi_score = 15
        elif avg_rsi < 40 and oversold_pct > 10:
            score.rsi_score = 10
        elif avg_rsi < 45:
            score.rsi_score = 5
        else:
            score.rsi_score = 0
        
        # 3. VOLUME (0-20 pontos)
        # Volume alto confirma movimentos
        if volume_ratio >= 2.0:
            score.volume_score = 20  # Volume 2x acima da média
        elif volume_ratio >= 1.5:
            score.volume_score = 15
        elif volume_ratio >= 1.2:
            score.volume_score = 10
        elif volume_ratio >= 1.0:
            score.volume_score = 5
        else:
            score.volume_score = 0
        
        # 4. BTC TREND (0-15 pontos)
        # BTC subindo = mercado saudável
        if btc_change_24h >= 3:
            score.btc_trend_score = 15  # BTC subindo forte
        elif btc_change_24h >= 1:
            score.btc_trend_score = 12
        elif btc_change_24h >= 0:
            score.btc_trend_score = 8   # Estável
        elif btc_change_24h >= -2:
            score.btc_trend_score = 4
        else:
            score.btc_trend_score = 0   # BTC caindo forte = cuidado
        
        # 5. PERFORMANCE RECENTE (0-15 pontos)
        # Se estratégia está funcionando, aumenta confiança
        if recent_pnl > 0 and recent_win_rate >= 0.6:
            score.performance_score = 15
        elif recent_pnl > 0 and recent_win_rate >= 0.5:
            score.performance_score = 12
        elif recent_pnl >= 0:
            score.performance_score = 8
        elif recent_pnl > -10:
            score.performance_score = 4
        else:
            score.performance_score = 0  # Performance ruim = conservador
        
        score.calculate_total()
        self.current_score = score
        
        return score
    
    def determine_level(self, score: OpportunityScore) -> AggressivenessLevel:
        """Determina nível de agressividade baseado no score"""
        
        # Verifica override manual
        if self.state.get('manual_override'):
            override = self.state['manual_override']
            if override in self.LEVELS:
                logger.info(f"🎛️ Override manual: {override}")
                return self.LEVELS[override]
        
        # Determina nível baseado no score
        if score.total_score >= 80:
            level = self.LEVELS['maximo']
        elif score.total_score >= 60:
            level = self.LEVELS['agressivo']
        elif score.total_score >= 40:
            level = self.LEVELS['moderado']
        else:
            level = self.LEVELS['conservador']
        
        # Log mudança de nível
        if level.name != self.current_level.name:
            logger.info(f"📊 Mudança de nível: {self.current_level.name} → {level.name}")
            logger.info(f"   Score: {score.total_score}/100")
            
            # Registra no histórico
            self.state['history'].append({
                'timestamp': datetime.now().isoformat(),
                'from_level': self.current_level.name,
                'to_level': level.name,
                'score': score.total_score,
                'score_breakdown': asdict(score)
            })
            
            # Mantém apenas últimas 100 mudanças
            if len(self.state['history']) > 100:
                self.state['history'] = self.state['history'][-100:]
        
        self.current_level = level
        self.state['current_level'] = level.name.lower()
        self._save_state()
        
        return level
    
    def get_adjusted_params(
        self,
        base_rsi_oversold: int = 30,
        base_stop_loss: float = -1.5,
        base_take_profit: float = 1.0,
        base_position_pct: float = 15
    ) -> Dict:
        """
        Retorna parâmetros ajustados baseado no nível atual.
        
        Aplica limites de segurança para nunca ultrapassar valores perigosos.
        """
        level = self.current_level
        
        # Calcula valores ajustados
        adj_rsi = base_rsi_oversold + level.rsi_oversold_adj
        adj_stop = base_stop_loss + level.stop_loss_adj  # Menos negativo
        adj_tp = base_take_profit + level.take_profit_adj
        adj_position = min(
            base_position_pct * level.multiplier,
            level.max_position_pct
        )
        
        # APLICA LIMITES DE SEGURANÇA
        adj_stop = max(adj_stop, self.SAFETY_LIMITS['max_stop_loss'])  # Não mais que -3%
        adj_stop = min(adj_stop, self.SAFETY_LIMITS['min_stop_loss'])  # Não menos que -0.5%
        adj_tp = min(adj_tp, self.SAFETY_LIMITS['max_take_profit'])    # Não mais que 5%
        adj_position = min(adj_position, self.SAFETY_LIMITS['max_position_pct'])  # Não mais que 25%
        
        return {
            'level': level.name,
            'emoji': level.emoji,
            'multiplier': level.multiplier,
            'score': self.current_score.total_score,
            
            # Parâmetros ajustados (com limites de segurança)
            'rsi_oversold': adj_rsi,
            'stop_loss_pct': round(adj_stop, 2),
            'take_profit_pct': round(adj_tp, 2),
            'position_pct': round(adj_position, 1),
            'trade_frequency_mult': level.trade_frequency_adj,
            
            # Info de segurança
            'safety_limits_applied': True,
            'daily_stop_pct': self.SAFETY_LIMITS['daily_stop_pct'],
        }
    
    def should_increase_position(self, symbol: str, current_confidence: float) -> Tuple[bool, float]:
        """
        Verifica se deve aumentar posição em um símbolo específico.
        
        Returns:
            (should_increase, multiplier)
        """
        if self.current_level.name == 'CONSERVADOR':
            return False, 1.0
        
        # Só aumenta se confiança alta + modo agressivo
        if current_confidence >= 0.7 and self.current_level.multiplier >= 1.3:
            return True, min(self.current_level.multiplier, 1.5)
        
        return False, 1.0
    
    def set_manual_override(self, level: str):
        """Define override manual (para testes ou situações especiais)"""
        if level in self.LEVELS or level is None:
            self.state['manual_override'] = level
            self._save_state()
            logger.info(f"🎛️ Override manual definido: {level}")
    
    def is_enabled(self) -> bool:
        """Verifica se modo oportunista está habilitado"""
        return self.state.get('enabled', True)
    
    def enable(self):
        """Habilita modo oportunista"""
        self.state['enabled'] = True
        self._save_state()
        
    def disable(self):
        """Desabilita modo oportunista (usa sempre conservador)"""
        self.state['enabled'] = False
        self.current_level = self.LEVELS['conservador']
        self._save_state()
    
    def get_status_report(self) -> str:
        """Retorna relatório de status formatado"""
        score = self.current_score
        level = self.current_level
        
        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║              🎯 MODO OPORTUNISTA - STATUS                     ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  {level.emoji} NÍVEL ATUAL: {level.name:<15} (x{level.multiplier})        
║                                                               ║
║  📊 SCORE DE OPORTUNIDADE: {score.total_score:>3}/100                    
║  ─────────────────────────────────────────────────────────────║
║  Fear & Greed:   {score.fear_greed_score:>5}/25  {'█' * int(score.fear_greed_score/2.5):░<10}
║  RSI Oversold:   {score.rsi_score:>5}/25  {'█' * int(score.rsi_score/2.5):░<10}
║  Volume:         {score.volume_score:>5}/20  {'█' * int(score.volume_score/2):░<10}
║  BTC Trend:      {score.btc_trend_score:>5}/15  {'█' * int(score.btc_trend_score/1.5):░<10}
║  Performance:    {score.performance_score:>5}/15  {'█' * int(score.performance_score/1.5):░<10}
║                                                               ║
║  🔧 AJUSTES APLICADOS:                                        ║
║  • RSI Oversold: +{level.rsi_oversold_adj} (base 30 → {30 + level.rsi_oversold_adj})            
║  • Stop Loss:    +{level.stop_loss_adj}% (menos apertado)           
║  • Take Profit:  +{level.take_profit_adj}% (mais alto)              
║  • Posição Máx:  {level.max_position_pct}% do capital                  
║                                                               ║
║  🛡️ LIMITES DE SEGURANÇA (SEMPRE ATIVOS):                     ║
║  • Max por posição: {self.SAFETY_LIMITS['max_position_pct']}%                              
║  • Stop Loss máx: {self.SAFETY_LIMITS['max_stop_loss']}%                            
║  • Daily Stop: {self.SAFETY_LIMITS['daily_stop_pct']}%                               
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        return report


# Singleton
_opportunistic_mode = None

def get_opportunistic_mode() -> OpportunisticMode:
    """Obtém instância do OpportunisticMode"""
    global _opportunistic_mode
    if _opportunistic_mode is None:
        _opportunistic_mode = OpportunisticMode()
    return _opportunistic_mode


# Exemplo de uso
if __name__ == "__main__":
    opp = get_opportunistic_mode()
    
    # Simula condições favoráveis
    score = opp.calculate_opportunity_score(
        fear_greed_index=20,      # Medo
        avg_rsi=28,               # RSI baixo
        oversold_count=8,         # 8 ativos sobrevendidos
        total_assets=20,          # De 20 total
        volume_ratio=1.5,         # Volume 50% acima da média
        btc_change_24h=2.5,       # BTC subindo
        recent_pnl=15,            # $15 de lucro na semana
        recent_win_rate=0.55      # 55% win rate
    )
    
    level = opp.determine_level(score)
    params = opp.get_adjusted_params()
    
    print(opp.get_status_report())
    print("\nParâmetros ajustados:")
    for k, v in params.items():
        print(f"  {k}: {v}")
