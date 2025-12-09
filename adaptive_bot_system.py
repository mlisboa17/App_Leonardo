"""
SISTEMA DE BOT ADAPTATIVO (Bot Único)
- Alterna entre diferentes estratégias conforme condições de mercado
- Mantém margens mínimas de lucro mesmo em situações extremas
- Ajusta % de venda quando saldo USDT é muito baixo
"""

import json
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdaptiveBotSystem:
    """Sistema que gerencia adaptações dinâmicas do bot híbrido"""
    
    def __init__(self, config_path: str = "config/bots_config.yaml"):
        """Inicializa o sistema adaptativo"""
        import yaml
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.bot_unico_config = self.config.get('bot_unico', {})
        self.adaptive_rules = self.bot_unico_config.get('adaptive_rules', {})
        self.state_file = Path("data/adaptive_bot_state.json")
        self.state = self._load_state()
    
    def _load_config(self):
        """Carrega configuração dos bots"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            return {}
    
    def _load_state(self):
        """Carrega estado anterior do bot adaptativo"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'consecutive_losses': 0,
            'daily_pnl': 0.0,
            'current_adjustments': {},
            'last_update': None
        }
    
    def _save_state(self):
        """Salva estado do bot adaptativo"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar estado: {e}")
    
    def calculate_adaptive_parameters(self, market_data: dict, account_data: dict) -> dict:
        """
        Calcula parâmetros adaptativos baseado em:
        - Saldo USDT atual
        - Volatilidade do mercado
        - PnL do dia
        - Histórico de perdas consecutivas
        
        Returns: dict com adjustments de RSI, Take Profit, etc
        """
        
        adjustments = {
            'rsi_oversold': self.bot_unico_config['rsi']['oversold'],
            'rsi_overbought': self.bot_unico_config['rsi']['overbought'],
            'take_profit': self.bot_unico_config['risk']['take_profit'],
            'stop_loss': self.bot_unico_config['risk']['stop_loss'],
            'sell_increase_pct': 0.0,
            'reason': []
        }
        
        # 1. VERIFICAR SALDO USDT BAIXO
        usdt_balance = account_data.get('usdt_balance', 0)
        low_threshold = self.adaptive_rules.get('low_balance_threshold', 50)
        
        if usdt_balance < low_threshold and usdt_balance > 0:
            increase = self.adaptive_rules.get('low_balance_sell_increase', 0.5)
            adjustments['sell_increase_pct'] += increase
            adjustments['reason'].append(
                f"🔴 SALDO BAIXO: ${usdt_balance:.2f} < ${low_threshold} "
                f"→ Aumentando venda em +{increase}% "
                f"(novo target: {self.bot_unico_config['risk']['take_profit'] + increase}%)"
            )
            logger.warning(f"Saldo USDT crítico: ${usdt_balance:.2f} - Ativando modo recuperação")
        
        # 2. VERIFICAR VOLATILIDADE
        volatility = market_data.get('volatility', 0)
        high_vol_threshold = self.adaptive_rules.get('high_volatility_threshold', 5.0)
        
        if volatility > high_vol_threshold:
            # Reduz TP em volatilidade alta (sai mais cedo)
            adjustment = self.adaptive_rules.get('high_volatility_adjustment', -0.3)
            adjustments['take_profit'] += adjustment
            adjustments['reason'].append(
                f"⚡ ALTA VOLATILIDADE: {volatility:.2f}% "
                f"→ Reduzindo TP em {adjustment}% "
                f"(novo: {adjustments['take_profit']:.2f}%)"
            )
        
        elif volatility < 1.0:
            # Aumenta TP em volatilidade baixa (deixa correr mais)
            adjustment = self.adaptive_rules.get('low_volatility_adjustment', 0.2)
            adjustments['take_profit'] += adjustment
            adjustments['reason'].append(
                f"😴 BAIXA VOLATILIDADE: {volatility:.2f}% "
                f"→ Aumentando TP em {adjustment}% "
                f"(novo: {adjustments['take_profit']:.2f}%)"
            )
        
        # 3. VERIFICAR PnL DO DIA
        daily_pnl = account_data.get('daily_pnl', 0)
        self.state['daily_pnl'] = daily_pnl
        profit_lock_threshold = self.adaptive_rules.get('profit_lock_on_daily_pnl', 100)
        
        if daily_pnl > profit_lock_threshold:
            # Se ganhou muito hoje, trava os ganhos (reduz TP)
            lock_reduction = 0.5  # Reduz TP para travar ganhos
            adjustments['take_profit'] = min(
                adjustments['take_profit'] - lock_reduction,
                0.8  # Mínimo de 0.8%
            )
            adjustments['reason'].append(
                f"💰 GANHO SIGNIFICATIVO: ${daily_pnl:.2f} > ${profit_lock_threshold} "
                f"→ Travando ganhos (TP: {adjustments['take_profit']:.2f}%)"
            )
        
        # 4. VERIFICAR PERDAS CONSECUTIVAS
        if self.state.get('consecutive_losses', 0) > self.adaptive_rules.get('consecutive_losses_threshold', 3):
            # Ativa modo recuperação
            recovery_increase = self.adaptive_rules.get('recovery_sell_increase', 0.7)
            adjustments['sell_increase_pct'] += recovery_increase
            adjustments['reason'].append(
                f"📉 MODO RECUPERAÇÃO: {self.state['consecutive_losses']} perdas consecutivas "
                f"→ Aumentando venda em +{recovery_increase}% "
                f"(novo target: {self.bot_unico_config['risk']['take_profit'] + adjustments['sell_increase_pct']:.2f}%)"
            )
        
        # 5. GARANTIR MARGENS MÍNIMAS
        # Nunca deixa TP abaixo de 0.5% (margem de segurança)
        min_tp = 0.5
        if adjustments['take_profit'] < min_tp:
            adjustments['take_profit'] = min_tp
            adjustments['reason'].append(
                f"⚠️ MARGEM MÍNIMA: Garantindo TP de pelo menos {min_tp}% "
                f"(antes estava: {self.bot_unico_config['risk']['take_profit']:.2f}%)"
            )
        
        # Nunca deixa SL acima de -0.5% (stop muito apertado)
        max_sl = -0.5
        if adjustments['stop_loss'] > max_sl:
            adjustments['stop_loss'] = max_sl
            adjustments['reason'].append(
                f"⚠️ STOP LOSS: Garantindo SL de no máximo {max_sl}% "
                f"(antes estava: {self.bot_unico_config['risk']['stop_loss']:.2f}%)"
            )
        
        adjustments['timestamp'] = datetime.now().isoformat()
        self.state['current_adjustments'] = adjustments
        self.state['last_update'] = datetime.now().isoformat()
        self._save_state()
        
        return adjustments
    
    def update_consecutive_losses(self, trade_result: dict):
        """Atualiza contador de perdas consecutivas"""
        if trade_result.get('pnl_usd', 0) < 0:
            self.state['consecutive_losses'] += 1
        else:
            self.state['consecutive_losses'] = 0
        
        self._save_state()
    
    def get_current_configuration(self, market_data: dict, account_data: dict) -> dict:
        """
        Retorna a configuração completa do bot com todos os ajustes aplicados
        """
        
        # Calcula ajustes adaptativos
        adjustments = self.calculate_adaptive_parameters(market_data, account_data)
        
        # Cria cópia da config original
        current_config = dict(self.bot_unico_config)
        
        # Aplica ajustes
        current_config['risk']['take_profit'] = adjustments['take_profit']
        current_config['risk']['stop_loss'] = adjustments['stop_loss']
        current_config['rsi']['oversold'] = int(adjustments['rsi_oversold'])
        current_config['rsi']['overbought'] = int(adjustments['rsi_overbought'])
        
        # Adiciona metadados
        current_config['_adaptive_adjustments'] = adjustments
        
        return current_config
    
    def get_status_report(self) -> str:
        """Gera relatório do estado adaptativo atual"""
        
        adjustments = self.state.get('current_adjustments', {})
        reasons = adjustments.get('reason', [])
        
        report = "📊 SISTEMA ADAPTATIVO BOT UNICO\n"
        report += "=" * 50 + "\n\n"
        
        report += f"📈 PnL do Dia: ${self.state.get('daily_pnl', 0):.2f}\n"
        report += f"⚠️ Perdas Consecutivas: {self.state.get('consecutive_losses', 0)}\n"
        report += f"🕐 Última Atualização: {self.state.get('last_update', 'N/A')}\n\n"
        
        report += "🔧 AJUSTES APLICADOS:\n"
        report += "-" * 50 + "\n"
        
        if reasons:
            for reason in reasons:
                report += f"• {reason}\n"
        else:
            report += "• Nenhum ajuste necessário (mercado normal)\n"
        
        report += "\n" + "=" * 50
        
        return report


def test_adaptive_system():
    """Testa o sistema adaptativo"""
    
    # Dados de teste: saldo baixo
    market_data = {
        'volatility': 3.5,  # 3.5% volatilidade
    }
    
    account_data = {
        'usdt_balance': 30,  # $30 USDT (baixo!)
        'daily_pnl': 5.0,    # $5 de lucro hoje
    }
    
    system = AdaptiveBotSystem()
    config = system.get_current_configuration(market_data, account_data)
    
    print(system.get_status_report())
    print(f"\n✅ TP Adaptativo: {config['risk']['take_profit']:.2f}%")
    print(f"✅ SL Adaptativo: {config['risk']['stop_loss']:.2f}%")


if __name__ == "__main__":
    test_adaptive_system()
