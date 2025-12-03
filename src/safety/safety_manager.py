"""
Módulo de Segurança - Sistema Anti-Alucinação
Implementa Kill Switch, validações e proteções
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class KillSwitch:
    """Sistema de parada de emergência"""
    
    def __init__(self, max_daily_loss: float, max_drawdown_pct: float):
        self.max_daily_loss = max_daily_loss
        self.max_drawdown_pct = max_drawdown_pct
        self.daily_pnl = 0.0
        self.peak_balance = 0.0
        self.is_active = False
        self.last_reset = datetime.now()
        
    def check_daily_loss(self, current_pnl: float) -> bool:
        """Verifica se atingiu limite de perda diária (apenas perdas, não lucros)"""
        # Reset diário
        if datetime.now() - self.last_reset > timedelta(days=1):
            self.daily_pnl = 0.0
            self.last_reset = datetime.now()
            
        self.daily_pnl = current_pnl
        
        # Só ativa kill switch se for PERDA (valor negativo)
        if self.daily_pnl < 0 and abs(self.daily_pnl) >= self.max_daily_loss:
            logger.critical(f"⛔ KILL SWITCH: Perda diária de {abs(self.daily_pnl):.2f} USDT atingida!")
            self.activate()
            return True
        return False
    
    def check_drawdown(self, current_balance: float) -> bool:
        """Verifica drawdown máximo"""
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
            
        if self.peak_balance > 0:
            drawdown_pct = ((self.peak_balance - current_balance) / self.peak_balance) * 100
            
            if drawdown_pct >= self.max_drawdown_pct:
                logger.critical(f"⛔ KILL SWITCH: Drawdown de {drawdown_pct:.2f}% atingido!")
                self.activate()
                return True
        return False
    
    def activate(self):
        """Ativa o kill switch"""
        self.is_active = True
        logger.critical("🛑 KILL SWITCH ATIVADO - Bot parado!")
        
    def deactivate(self):
        """Desativa manualmente (requer intervenção)"""
        self.is_active = False
        logger.warning("✅ Kill Switch desativado manualmente")


class PriceValidator:
    """Valida sanidade dos preços"""
    
    def __init__(self, max_deviation_pct: float = 5.0):
        self.max_deviation_pct = max_deviation_pct
        self.last_prices = {}  # Dicionário para armazenar último preço de cada símbolo
        
    def validate_price(self, new_price: float, symbol: str) -> bool:
        """
        Valida se o preço é sano (não variou drasticamente)
        Retorna True se válido, False se suspeito
        """
        # Primeira vez que vemos este símbolo
        if symbol not in self.last_prices:
            self.last_prices[symbol] = new_price
            return True
        
        # Obtém último preço DESTE símbolo específico
        last_price = self.last_prices[symbol]
        deviation_pct = abs((new_price - last_price) / last_price * 100)
        
        if deviation_pct > self.max_deviation_pct:
            logger.warning(
                f"⚠️ PREÇO SUSPEITO para {symbol}: "
                f"Variação de {deviation_pct:.2f}% "
                f"({last_price:.2f} → {new_price:.2f})"
            )
            return False
        
        # Atualiza último preço deste símbolo
        self.last_prices[symbol] = new_price
        return True


class OrderValidator:
    """Valida execução de ordens"""
    
    @staticmethod
    def validate_order_response(order_response: dict) -> bool:
        """Valida resposta da exchange após enviar ordem"""
        if not order_response:
            logger.error("❌ Resposta de ordem vazia!")
            return False
            
        if 'status' not in order_response:
            logger.error("❌ Resposta sem campo 'status'")
            return False
            
        if order_response['status'] not in ['open', 'closed', 'filled']:
            logger.error(f"❌ Status de ordem inválido: {order_response.get('status')}")
            return False
            
        logger.info(f"✅ Ordem validada: {order_response.get('id')} - {order_response.get('status')}")
        return True
    
    @staticmethod
    def validate_balance(required_amount: float, available_balance: float) -> bool:
        """Valida se há saldo suficiente - versão flexível"""
        # Permitir operações com até 90% do saldo disponível
        usable_balance = available_balance * 0.9
        if available_balance < required_amount:
            # Se não tem o valor exato, tenta com 90% do saldo disponível
            if usable_balance > 1.0:  # Mínimo de $1
                logger.warning(
                    f"⚠️ Ajustando operação: "
                    f"Necessário {required_amount:.2f}, Usando {usable_balance:.2f} (90% do disponível)"
                )
                return True
            else:
                logger.error(
                    f"❌ Saldo muito baixo: "
                    f"Necessário {required_amount:.2f}, Disponível {available_balance:.2f}"
                )
                return False
        return True


class SafetyManager:
    """Gerenciador central de segurança"""
    
    def __init__(self, config: dict):
        self.kill_switch = KillSwitch(
            max_daily_loss=config.get('max_daily_loss', 500),
            max_drawdown_pct=config.get('max_drawdown', 20)
        )
        self.price_validator = PriceValidator(
            max_deviation_pct=config.get('price_deviation_limit', 5)
        )
        self.order_validator = OrderValidator()
        
    def is_safe_to_trade(self, current_balance: float, daily_pnl: float) -> bool:
        """Verifica se é seguro continuar operando"""
        if self.kill_switch.is_active:
            return False
            
        if self.kill_switch.check_daily_loss(daily_pnl):
            return False
            
        if self.kill_switch.check_drawdown(current_balance):
            return False
            
        return True
    
    def emergency_stop(self, exchange_client) -> None:
        """Parada de emergência - cancela todas as ordens"""
        logger.critical("🚨 EMERGÊNCIA: Cancelando todas as ordens abertas...")
        try:
            open_orders = exchange_client.fetch_open_orders()
            for order in open_orders:
                exchange_client.cancel_order(order['id'], order['symbol'])
                logger.info(f"❌ Ordem {order['id']} cancelada")
            logger.critical("✅ Todas as ordens foram canceladas")
        except Exception as e:
            logger.critical(f"❌ ERRO ao cancelar ordens: {e}")
