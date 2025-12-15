"""
Modulo de Seguranca - Sistema Anti-Alucinacao BLINDADO
Implementa Kill Switch, validacoes e protecoes MAXIMAS
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================
# LIMITES ABSOLUTOS - NUNCA ULTRAPASSAR
# ============================================
ABSOLUTE_LIMITS = {
    # Limites de perda
    'MAX_LOSS_PER_TRADE_PCT': 3.0,      # Max 3% por trade
    'MAX_LOSS_DAILY_PCT': 20.0,          # Max 20% por dia (ajustado para permitir maiores perdas)
    'MAX_DRAWDOWN_PCT': 25.0,            # Max 25% drawdown (ajustado)
    'EMERGENCY_STOP_PCT': 30.0,          # Para TUDO se perder 30% (ajustado)
    
    # Limites de ordem
    'MIN_ORDER_SIZE': 10.0,              # Minimo $10 por ordem
    'MAX_ORDER_SIZE': 100.0,             # Maximo $100 por ordem (para $1000 capital)
    'MAX_ORDER_PCT_BALANCE': 10.0,       # Max 10% do saldo por ordem
    
    # Limites de posicao
    'MAX_POSITIONS_TOTAL': 10,           # Max 10 posicoes no total
    'MAX_POSITIONS_PER_SYMBOL': 1,       # Max 1 posicao por moeda
    'MAX_EXPOSURE_PCT': 80.0,            # Max 80% do capital exposto
    
    # Limites de preco
    'MAX_PRICE_DEVIATION_PCT': 5.0,      # Rejeita se preco variar >5% repentino
    'MAX_SPREAD_PCT': 1.0,               # Max 1% de spread
    
    # Limites de frequencia
    'MIN_TIME_BETWEEN_TRADES_SEC': 10,   # Min 10s entre trades
    'MAX_TRADES_PER_MINUTE': 3,          # Max 3 trades por minuto
    'MAX_TRADES_PER_HOUR': 30,           # Max 30 trades por hora
    
    # Limites da IA
    'AI_MIN_CONFIDENCE': 0.6,            # IA precisa ter 60%+ confianca
    'AI_MAX_ADJUSTMENT_PCT': 20.0,       # IA so pode ajustar 20% dos params
    'AI_REQUIRE_CONFIRMATION': True,     # IA precisa de confirmacao humana para grandes mudancas
}


class KillSwitch:
    """Sistema de parada de emergencia BLINDADO"""
    
    def __init__(self, max_daily_loss: float, max_drawdown_pct: float):
        # Usa o MENOR entre config e limite absoluto
        self.max_daily_loss = min(max_daily_loss, ABSOLUTE_LIMITS['MAX_LOSS_DAILY_PCT'])
        self.max_drawdown_pct = min(max_drawdown_pct, ABSOLUTE_LIMITS['MAX_DRAWDOWN_PCT'])
        self.emergency_stop_pct = ABSOLUTE_LIMITS['EMERGENCY_STOP_PCT']
        
        self.daily_pnl = 0.0
        self.peak_balance = 0.0
        self.initial_balance = 0.0
        self.is_active = False
        self.last_reset = datetime.now()
        self.activation_reason = ""
        
    def set_initial_balance(self, balance: float):
        """Define saldo inicial para calculos"""
        self.initial_balance = balance
        self.peak_balance = balance
        
    def check_daily_loss(self, current_pnl: float) -> bool:
        """Verifica se atingiu limite de perda diaria"""
        # Reset diario
        if datetime.now() - self.last_reset > timedelta(days=1):
            self.daily_pnl = 0.0
            self.last_reset = datetime.now()
            
        self.daily_pnl = current_pnl
        
        # Calcula % de perda
        if self.initial_balance > 0:
            loss_pct = abs(current_pnl) / self.initial_balance * 100
            
            if current_pnl < 0 and loss_pct >= self.max_daily_loss:
                self.activate(f"PERDA DIARIA: {loss_pct:.2f}% (limite: {self.max_daily_loss}%)")
                return True
        
        return False
    
    def check_drawdown(self, current_balance: float) -> bool:
        """Verifica drawdown maximo"""
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
            
        if self.peak_balance > 0:
            drawdown_pct = ((self.peak_balance - current_balance) / self.peak_balance) * 100
            
            # Emergencia total
            if drawdown_pct >= self.emergency_stop_pct:
                self.activate(f"EMERGENCIA: Drawdown {drawdown_pct:.2f}% >= {self.emergency_stop_pct}%")
                return True
            
            # Drawdown normal
            if drawdown_pct >= self.max_drawdown_pct:
                self.activate(f"DRAWDOWN: {drawdown_pct:.2f}% (limite: {self.max_drawdown_pct}%)")
                return True
                
        return False
    
    def activate(self, reason: str = ""):
        """Ativa o kill switch"""
        self.is_active = True
        self.activation_reason = reason
        logger.critical(f"[KILL SWITCH ATIVADO] {reason}")
        
    def deactivate(self):
        """Desativa manualmente (requer intervencao)"""
        self.is_active = False
        self.activation_reason = ""
        logger.warning("[Kill Switch] Desativado manualmente")


class PriceValidator:
    """Valida sanidade dos precos - Anti-Flash Crash"""
    
    def __init__(self, max_deviation_pct: float = 5.0):
        self.max_deviation_pct = min(max_deviation_pct, ABSOLUTE_LIMITS['MAX_PRICE_DEVIATION_PCT'])
        self.last_prices: Dict[str, float] = {}
        self.price_history: Dict[str, list] = {}  # Historico para detectar anomalias
        
    def validate_price(self, new_price: float, symbol: str) -> bool:
        """Valida se o preco e sano"""
        if new_price <= 0:
            logger.error(f"[PRECO INVALIDO] {symbol}: preco <= 0")
            return False
        
        # Primeira vez
        if symbol not in self.last_prices:
            self.last_prices[symbol] = new_price
            self.price_history[symbol] = [new_price]
            return True
        
        last_price = self.last_prices[symbol]
        deviation_pct = abs((new_price - last_price) / last_price * 100)
        
        if deviation_pct > self.max_deviation_pct:
            logger.warning(
                f"[PRECO SUSPEITO] {symbol}: "
                f"Variacao de {deviation_pct:.2f}% "
                f"({last_price:.6f} -> {new_price:.6f}) - REJEITADO"
            )
            return False
        
        # Atualiza historico
        self.last_prices[symbol] = new_price
        self.price_history[symbol].append(new_price)
        if len(self.price_history[symbol]) > 100:
            self.price_history[symbol] = self.price_history[symbol][-100:]
            
        return True


class OrderValidator:
    """Valida ordens antes de enviar - BLINDADO"""
    
    def __init__(self):
        self.recent_trades: list = []  # [(timestamp, symbol, amount)]
        
    def validate_order_size(self, amount: float, balance: float, symbol: str) -> tuple:
        """
        Valida tamanho da ordem.
        Retorna (is_valid, adjusted_amount, reason)
        """
        # Verifica minimo
        if amount < ABSOLUTE_LIMITS['MIN_ORDER_SIZE']:
            return False, 0, f"Ordem muito pequena: ${amount:.2f} < ${ABSOLUTE_LIMITS['MIN_ORDER_SIZE']}"
        
        # Verifica maximo absoluto
        if amount > ABSOLUTE_LIMITS['MAX_ORDER_SIZE']:
            amount = ABSOLUTE_LIMITS['MAX_ORDER_SIZE']
            logger.warning(f"[LIMITE] Ordem reduzida para ${amount:.2f} (max absoluto)")
        
        # Verifica % do saldo
        max_by_balance = balance * (ABSOLUTE_LIMITS['MAX_ORDER_PCT_BALANCE'] / 100)
        if amount > max_by_balance:
            amount = max_by_balance
            logger.warning(f"[LIMITE] Ordem reduzida para ${amount:.2f} (max {ABSOLUTE_LIMITS['MAX_ORDER_PCT_BALANCE']}% do saldo)")
        
        # Verifica se ainda e valido
        if amount < ABSOLUTE_LIMITS['MIN_ORDER_SIZE']:
            return False, 0, f"Saldo insuficiente para ordem minima"
            
        return True, amount, "OK"
    
    def validate_trade_frequency(self) -> tuple:
        """
        Valida frequencia de trades.
        Retorna (is_valid, reason)
        """
        now = datetime.now()
        
        # Remove trades antigos (>1 hora)
        self.recent_trades = [
            t for t in self.recent_trades 
            if (now - t[0]).total_seconds() < 3600
        ]
        
        # Verifica trades no ultimo minuto
        trades_last_minute = len([
            t for t in self.recent_trades 
            if (now - t[0]).total_seconds() < 60
        ])
        
        if trades_last_minute >= ABSOLUTE_LIMITS['MAX_TRADES_PER_MINUTE']:
            return False, f"Limite de {ABSOLUTE_LIMITS['MAX_TRADES_PER_MINUTE']} trades/minuto atingido"
        
        # Verifica trades na ultima hora
        if len(self.recent_trades) >= ABSOLUTE_LIMITS['MAX_TRADES_PER_HOUR']:
            return False, f"Limite de {ABSOLUTE_LIMITS['MAX_TRADES_PER_HOUR']} trades/hora atingido"
        
        return True, "OK"
    
    def record_trade(self, symbol: str, amount: float):
        """Registra trade realizado"""
        self.recent_trades.append((datetime.now(), symbol, amount))
    
    @staticmethod
    def validate_order_response(order_response: dict) -> bool:
        """Valida resposta da exchange apos enviar ordem"""
        if not order_response:
            logger.error("[ORDEM] Resposta vazia!")
            return False
            
        if 'status' not in order_response:
            logger.error("[ORDEM] Resposta sem campo 'status'")
            return False
            
        if order_response['status'] not in ['open', 'closed', 'filled']:
            logger.error(f"[ORDEM] Status invalido: {order_response.get('status')}")
            return False
            
        logger.info(f"[ORDEM OK] ID: {order_response.get('id')} - Status: {order_response.get('status')}")
        return True
    
    @staticmethod
    def validate_balance(required_amount: float, available_balance: float) -> bool:
        """Valida se ha saldo suficiente"""
        if available_balance < required_amount:
            if available_balance >= ABSOLUTE_LIMITS['MIN_ORDER_SIZE']:
                logger.warning(
                    f"[SALDO] Ajustando: Necessario ${required_amount:.2f}, "
                    f"Disponivel ${available_balance:.2f}"
                )
                return True
            else:
                logger.error(
                    f"[SALDO INSUFICIENTE] "
                    f"Necessario ${required_amount:.2f}, Disponivel ${available_balance:.2f}"
                )
                return False
        return True


class AIValidator:
    """Valida decisoes da IA - Anti-Alucinacao"""
    
    def __init__(self):
        self.ai_decisions_history: list = []
        self.rejected_decisions: list = []
        
    def validate_ai_recommendation(self, recommendation: Dict[str, Any]) -> tuple:
        """
        Valida recomendacao da IA.
        Retorna (is_valid, reason)
        """
        # Verifica confianca minima
        confidence = recommendation.get('confidence', 0)
        if confidence < ABSOLUTE_LIMITS['AI_MIN_CONFIDENCE']:
            reason = f"Confianca da IA muito baixa: {confidence:.2f} < {ABSOLUTE_LIMITS['AI_MIN_CONFIDENCE']}"
            self.rejected_decisions.append({'recommendation': recommendation, 'reason': reason, 'time': datetime.now().isoformat()})
            return False, reason
        
        # Verifica se ajuste esta dentro do limite
        adjustment_pct = recommendation.get('adjustment_pct', 0)
        if abs(adjustment_pct) > ABSOLUTE_LIMITS['AI_MAX_ADJUSTMENT_PCT']:
            reason = f"Ajuste da IA muito grande: {adjustment_pct:.2f}% > {ABSOLUTE_LIMITS['AI_MAX_ADJUSTMENT_PCT']}%"
            self.rejected_decisions.append({'recommendation': recommendation, 'reason': reason, 'time': datetime.now().isoformat()})
            return False, reason
        
        return True, "OK"
    
    def validate_ai_trade_signal(self, signal: Dict[str, Any], market_data: Dict[str, Any]) -> tuple:
        """
        Valida sinal de trade da IA contra dados reais do mercado.
        Retorna (is_valid, reason)
        """
        # Verifica se IA esta "vendo" o mesmo preco que o mercado
        ai_price = signal.get('price', 0)
        market_price = market_data.get('price', 0)
        
        if market_price > 0:
            price_diff_pct = abs((ai_price - market_price) / market_price * 100)
            if price_diff_pct > 1.0:  # Mais de 1% de diferenca
                return False, f"Preco da IA ({ai_price}) difere do mercado ({market_price}) em {price_diff_pct:.2f}%"
        
        # Verifica se RSI da IA bate com calculado
        ai_rsi = signal.get('rsi', 50)
        if ai_rsi < 0 or ai_rsi > 100:
            return False, f"RSI invalido da IA: {ai_rsi}"
        
        return True, "OK"


class PositionValidator:
    """Valida posicoes e exposicao"""
    
    def __init__(self, max_positions: int = 10):
        self.max_positions = min(max_positions, ABSOLUTE_LIMITS['MAX_POSITIONS_TOTAL'])
        self.current_positions: Dict[str, Dict] = {}
        
    def can_open_position(self, symbol: str, amount: float, total_balance: float) -> tuple:
        """
        Verifica se pode abrir nova posicao.
        Retorna (can_open, reason)
        """
        # Verifica numero de posicoes
        if len(self.current_positions) >= self.max_positions:
            return False, f"Limite de {self.max_positions} posicoes atingido"
        
        # Verifica se ja tem posicao nesse simbolo
        if symbol in self.current_positions:
            return False, f"Ja existe posicao em {symbol}"
        
        # Verifica exposicao total
        current_exposure = sum(p.get('amount', 0) for p in self.current_positions.values())
        max_exposure = total_balance * (ABSOLUTE_LIMITS['MAX_EXPOSURE_PCT'] / 100)
        
        if current_exposure + amount > max_exposure:
            return False, f"Exposicao maxima atingida: ${current_exposure + amount:.2f} > ${max_exposure:.2f}"
        
        return True, "OK"
    
    def add_position(self, symbol: str, amount: float, price: float):
        """Adiciona posicao ao tracking"""
        self.current_positions[symbol] = {
            'amount': amount,
            'entry_price': price,
            'entry_time': datetime.now().isoformat()
        }
    
    def remove_position(self, symbol: str):
        """Remove posicao do tracking"""
        if symbol in self.current_positions:
            del self.current_positions[symbol]


class SafetyManager:
    """Gerenciador central de seguranca - BLINDADO"""
    
    def __init__(self, config: dict):
        # Usa limites absolutos como fallback
        max_daily_loss = min(
            config.get('max_daily_loss', 50),
            ABSOLUTE_LIMITS['MAX_LOSS_DAILY_PCT']
        )
        max_drawdown = min(
            config.get('max_drawdown', 10),
            ABSOLUTE_LIMITS['MAX_DRAWDOWN_PCT']
        )
        
        self.kill_switch = KillSwitch(max_daily_loss, max_drawdown)
        self.price_validator = PriceValidator(
            max_deviation_pct=ABSOLUTE_LIMITS['MAX_PRICE_DEVIATION_PCT']
        )
        self.order_validator = OrderValidator()
        self.ai_validator = AIValidator()
        self.position_validator = PositionValidator(
            max_positions=config.get('max_positions', 10)
        )
        
        # Estatisticas de seguranca
        self.blocked_trades = 0
        self.blocked_reasons: Dict[str, int] = {}
        
        logger.info("[SAFETY] Sistema anti-alucinacao inicializado")
        logger.info(f"[SAFETY] Limites: MaxLoss={max_daily_loss}%, MaxDrawdown={max_drawdown}%")
        
    def is_safe_to_trade(self, current_balance: float, daily_pnl: float) -> bool:
        """Verifica se e seguro continuar operando"""
        if self.kill_switch.is_active:
            return False
            
        if self.kill_switch.check_daily_loss(daily_pnl):
            return False
            
        if self.kill_switch.check_drawdown(current_balance):
            return False
            
        return True
    
    def validate_trade(self, symbol: str, side: str, amount: float, 
                       price: float, balance: float, ai_signal: dict = None) -> tuple:
        """
        Validacao COMPLETA antes de qualquer trade.
        Retorna (is_valid, adjusted_amount, reason)
        """
        # 1. Verifica Kill Switch
        if self.kill_switch.is_active:
            self._record_block("kill_switch")
            return False, 0, f"Kill Switch ativo: {self.kill_switch.activation_reason}"
        
        # 2. Valida preco
        if not self.price_validator.validate_price(price, symbol):
            self._record_block("price_invalid")
            return False, 0, "Preco invalido ou suspeito"
        
        # 3. Valida tamanho da ordem
        valid, adjusted_amount, reason = self.order_validator.validate_order_size(amount, balance, symbol)
        if not valid:
            self._record_block("order_size")
            return False, 0, reason
        
        # 4. Valida frequencia
        freq_valid, freq_reason = self.order_validator.validate_trade_frequency()
        if not freq_valid:
            self._record_block("frequency")
            return False, 0, freq_reason
        
        # 5. Valida posicao (se for compra)
        if side.lower() == 'buy':
            can_open, pos_reason = self.position_validator.can_open_position(symbol, adjusted_amount, balance)
            if not can_open:
                self._record_block("position_limit")
                return False, 0, pos_reason
        
        # 6. Valida sinal da IA (se fornecido)
        if ai_signal:
            ai_valid, ai_reason = self.ai_validator.validate_ai_recommendation(ai_signal)
            if not ai_valid:
                self._record_block("ai_rejected")
                return False, 0, ai_reason
        
        return True, adjusted_amount, "OK"
    
    def _record_block(self, reason: str):
        """Registra trade bloqueado"""
        self.blocked_trades += 1
        self.blocked_reasons[reason] = self.blocked_reasons.get(reason, 0) + 1
    
    def record_executed_trade(self, symbol: str, side: str, amount: float, price: float):
        """Registra trade executado com sucesso"""
        self.order_validator.record_trade(symbol, amount)
        
        if side.lower() == 'buy':
            self.position_validator.add_position(symbol, amount, price)
        else:
            self.position_validator.remove_position(symbol)
    
    def get_safety_stats(self) -> dict:
        """Retorna estatisticas de seguranca"""
        return {
            'kill_switch_active': self.kill_switch.is_active,
            'kill_switch_reason': self.kill_switch.activation_reason,
            'blocked_trades': self.blocked_trades,
            'blocked_reasons': self.blocked_reasons,
            'current_positions': len(self.position_validator.current_positions),
            'recent_trades': len(self.order_validator.recent_trades)
        }
    
    def emergency_stop(self, exchange_client) -> None:
        """Parada de emergencia - cancela todas as ordens"""
        logger.critical("[EMERGENCIA] Cancelando todas as ordens abertas...")
        try:
            open_orders = exchange_client.fetch_open_orders()
            for order in open_orders:
                exchange_client.cancel_order(order['id'], order['symbol'])
                logger.info(f"[CANCELADO] Ordem {order['id']}")
            logger.critical("[EMERGENCIA] Todas as ordens foram canceladas")
        except Exception as e:
            logger.critical(f"[ERRO EMERGENCIA] {e}")

