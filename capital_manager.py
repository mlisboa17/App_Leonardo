#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💰 CAPITAL MANAGEMENT SYSTEM - App Leonardo v3.0
================================================

Sistema inteligente de gerenciamento de capital com foco em
profitabilidade e gestão de risco.

REGRAS DE CAPITAL:
1. COMPRA: Executar apenas com R:R ≥ 2 (Risk/Reward)
2. VENDA: Buscar maximizar lucro, liberar capital
3. STOP LOSS: Manter em -0.5% a -1.5% (configurável por bot)
4. TAKE PROFIT: Manter em 0.3% a 1.5% (configurável por bot)
5. SALDO: Priorizar compras se capital disponível
6. LIMITE DE RISCO: Máximo 2% da carteira por trade

EXEMPLO DE R:R:
- Compra: $100
- Stop Loss: -$2 (risco = $2)
- Take Profit: +$4 (reward = $4)
- R:R = 4/2 = 2:1 ✅ EXECUTAR
- R:R = 2/2 = 1:1 ❌ REJEITAR

USO:
    python capital_manager.py              # Verificar saldo
    python capital_manager.py analyze      # Analisar capital
    python capital_manager.py rebalance    # Rebalancear
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('CapitalManager')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class TradeSignal:
    """Sinal de trade com validação de R:R"""
    symbol: str
    bot: str
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    position_size: float
    
    @property
    def risk_amount(self) -> float:
        """Valor em risco (entry - SL)"""
        return abs(self.entry_price - self.stop_loss_price) * self.position_size
    
    @property
    def reward_amount(self) -> float:
        """Valor potencial de ganho (TP - entry)"""
        return abs(self.take_profit_price - self.entry_price) * self.position_size
    
    @property
    def risk_reward_ratio(self) -> float:
        """Relação Risco/Recompensa"""
        if self.risk_amount == 0:
            return 0.0
        return self.reward_amount / self.risk_amount
    
    @property
    def is_valid(self) -> bool:
        """Retorna True se o sinal atende aos critérios mínimos"""
        return self.risk_reward_ratio >= 2.0  # Mínimo 2:1


class CapitalManager:
    """Gerenciador central de capital"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.config_dir = Path("config")
        
        # Arquivos
        self.balances_file = self.data_dir / "dashboard_balances.json"
        self.positions_file = self.data_dir / "multibot_positions.json"
        self.trades_file = self.data_dir / "all_trades_history.json"
        self.signals_file = self.data_dir / "ai" / "trade_signals.json"
        
        # Criar diretórios
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "ai").mkdir(exist_ok=True)
        
        # Parâmetros
        self.initial_capital = 1000.0  # $1000 USDT
        self.max_risk_per_trade = 0.02  # Máx 2% por trade
        self.min_reward_ratio = 2.0  # Mínimo R:R 2:1
        
        # Limites por bot
        self.bot_limits = {
            'bot_estavel': {'max_per_trade': 39.15, 'max_positions': 4, 'risk_pct': 0.5},
            'bot_medio': {'max_per_trade': 39.15, 'max_positions': 4, 'risk_pct': 1.0},
            'bot_volatil': {'max_per_trade': 39.15, 'max_positions': 3, 'risk_pct': 1.2},
            'bot_meme': {'max_per_trade': 30.0, 'max_positions': 2, 'risk_pct': 1.5},
            'unico_bot': {'max_per_trade': 50.0, 'max_positions': 9, 'risk_pct': 0.6},
        }
        
        # Cache
        self.current_balance = self.initial_capital
        self.invested_balance = 0.0
        self.available_balance = self.initial_capital
        self.open_positions = []
        self.trade_history = []
    
    def load_state(self):
        """Carrega estado atual do capital"""
        try:
            # Carregar balanço
            if self.balances_file.exists():
                with open(self.balances_file, 'r') as f:
                    balances = json.load(f)
                    self.current_balance = balances.get('current_balance', self.initial_capital)
                    self.invested_balance = balances.get('invested_balance', 0.0)
                    self.available_balance = balances.get('available_balance', self.initial_capital)
            
            # Carregar posições abertas
            if self.positions_file.exists():
                with open(self.positions_file, 'r') as f:
                    self.open_positions = json.load(f)
            
            # Carregar histórico de trades
            if self.trades_file.exists():
                with open(self.trades_file, 'r') as f:
                    self.trade_history = json.load(f)
        
        except Exception as e:
            logger.error(f"Erro ao carregar estado: {e}")
    
    def validate_trade_signal(self, signal: TradeSignal) -> Tuple[bool, str]:
        """
        Valida um sinal de trade contra as regras de capital
        
        Retorna:
            (é_válido, motivo)
        """
        # Verificação 1: R:R mínimo de 2:1
        if signal.risk_reward_ratio < self.min_reward_ratio:
            return False, f"R:R insuficiente: {signal.risk_reward_ratio:.2f}:1 (mínimo: 2:1)"
        
        # Verificação 2: Risco por trade não pode exceder 2% do capital
        risk_pct = (signal.risk_amount / self.current_balance) * 100
        if risk_pct > self.max_risk_per_trade * 100:
            return False, f"Risco {risk_pct:.2f}% > {self.max_risk_per_trade*100}% máximo"
        
        # Verificação 3: Saldo disponível suficiente
        if signal.position_size > self.available_balance:
            return False, f"Saldo insuficiente: ${signal.position_size:.2f} > ${self.available_balance:.2f}"
        
        # Verificação 4: Limites do bot
        if signal.bot in self.bot_limits:
            limits = self.bot_limits[signal.bot]
            
            # Verificar tamanho máximo por trade
            if signal.position_size > limits['max_per_trade']:
                return False, f"Tamanho > limite do bot: ${signal.position_size:.2f} > ${limits['max_per_trade']}"
            
            # Verificar máximo de posições
            bot_positions = sum(1 for p in self.open_positions 
                              if p.get('bot') == signal.bot)
            if bot_positions >= limits['max_positions']:
                return False, f"Máximo de posições atingido: {bot_positions}/{limits['max_positions']}"
        
        # Todas as verificações passaram
        return True, "✅ Sinal válido para execução"
    
    def calculate_optimal_position_size(self, 
                                       symbol: str,
                                       entry_price: float,
                                       stop_loss_price: float,
                                       take_profit_price: float,
                                       bot: str = 'bot_estavel') -> float:
        """
        Calcula o tamanho de posição ótimo baseado em:
        - Risco máximo permitido (2% do capital)
        - Limite do bot
        - Relação R:R desejada (2:1)
        
        Retorna: Tamanho da posição em USDT
        """
        # Risco máximo em USDT
        max_risk = self.current_balance * self.max_risk_per_trade
        
        # Risco por unidade (diferença entry-SL)
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit == 0:
            return 0.0
        
        # Tamanho baseado em risco
        position_size = max_risk / risk_per_unit
        
        # Aplicar limites do bot
        if bot in self.bot_limits:
            limits = self.bot_limits[bot]
            position_size = min(position_size, limits['max_per_trade'])
        
        # Nunca exceeder saldo disponível
        position_size = min(position_size, self.available_balance)
        
        # Arredondar para 2 casas decimais
        return round(position_size, 2)
    
    def should_buy(self, 
                  symbol: str,
                  entry_price: float,
                  stop_loss_price: float,
                  take_profit_price: float,
                  bot: str = 'bot_estavel') -> Tuple[bool, Dict]:
        """
        Determina se deve executar compra com base em regras de capital
        
        Retorna:
            (deve_comprar, detalhes)
        """
        result = {
            'should_buy': False,
            'reason': '',
            'position_size': 0.0,
            'risk_reward_ratio': 0.0,
            'available_capital': self.available_balance,
            'current_capital': self.current_balance,
            'risk_amount': 0.0,
            'reward_amount': 0.0
        }
        
        try:
            # Criar sinal
            position_size = self.calculate_optimal_position_size(
                symbol, entry_price, stop_loss_price, take_profit_price, bot
            )
            
            signal = TradeSignal(
                symbol=symbol,
                bot=bot,
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                position_size=position_size
            )
            
            # Validar
            is_valid, message = self.validate_trade_signal(signal)
            
            result['should_buy'] = is_valid
            result['reason'] = message
            result['position_size'] = signal.position_size
            result['risk_reward_ratio'] = signal.risk_reward_ratio
            result['risk_amount'] = signal.risk_amount
            result['reward_amount'] = signal.reward_amount
            
            return is_valid, result
        
        except Exception as e:
            result['reason'] = f"Erro na validação: {e}"
            return False, result
    
    def should_sell(self, 
                   symbol: str,
                   current_price: float,
                   entry_price: float,
                   position_size: float) -> Tuple[bool, Dict]:
        """
        Determina se deve vender baseado em:
        1. Lucro > 0.3% (mínimo viável)
        2. Captura de lucro > 1.0% (venda normal)
        3. Stop loss atingido
        
        Retorna:
            (deve_vender, motivo)
        """
        result = {
            'should_sell': False,
            'reason': '',
            'current_price': current_price,
            'entry_price': entry_price,
            'pnl_pct': 0.0,
            'pnl_usd': 0.0
        }
        
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        pnl_usd = (current_price - entry_price) * position_size
        
        result['pnl_pct'] = pnl_pct
        result['pnl_usd'] = pnl_usd
        
        # Vender com lucro > 0.3% (mínimo viável)
        if pnl_pct > 0.3:
            result['should_sell'] = True
            if pnl_pct > 1.0:
                result['reason'] = f"Captura de lucro: +{pnl_pct:.2f}% (+${pnl_usd:.2f})"
            else:
                result['reason'] = f"Lucro mínimo: +{pnl_pct:.2f}% (+${pnl_usd:.2f})"
        
        # Vender com loss mínimo (-0.5%)
        elif pnl_pct < -0.5:
            result['should_sell'] = True
            result['reason'] = f"Stop loss: {pnl_pct:.2f}% (-${abs(pnl_usd):.2f})"
        
        return result['should_sell'], result
    
    def execute_trade(self, 
                     symbol: str,
                     position_size: float,
                     entry_price: float,
                     side: str,  # 'buy' ou 'sell'
                     bot: str = 'bot_estavel'):
        """Executa um trade e atualiza o estado do capital"""
        try:
            trade_value = position_size * entry_price
            
            if side == 'buy':
                self.available_balance -= trade_value
                self.invested_balance += trade_value
                logger.info(f"✅ COMPRA executada: {symbol} ${position_size:.2f} @ ${entry_price:.2f}")
            
            elif side == 'sell':
                self.available_balance += trade_value
                self.invested_balance -= trade_value
                logger.info(f"✅ VENDA executada: {symbol} ${position_size:.2f} @ ${entry_price:.2f}")
            
            # Atualizar arquivo de balanço
            self._save_balances()
        
        except Exception as e:
            logger.error(f"Erro ao executar trade: {e}")
    
    def _save_balances(self):
        """Salva estado do capital em arquivo"""
        balances = {
            'current_balance': self.current_balance,
            'invested_balance': self.invested_balance,
            'available_balance': self.available_balance,
            'last_update': datetime.now().isoformat()
        }
        
        with open(self.balances_file, 'w') as f:
            json.dump(balances, f, indent=2)
    
    def print_summary(self):
        """Imprime resumo do capital"""
        print("\n" + "=" * 70)
        print("💰 RESUMO DO CAPITAL DISPONÍVEL")
        print("=" * 70)
        
        # Carregar estado
        self.load_state()
        
        total_pnl = self.current_balance - self.initial_capital
        roi = (total_pnl / self.initial_capital) * 100
        
        print(f"Capital Inicial:        ${self.initial_capital:.2f}")
        print(f"Capital Atual:          ${self.current_balance:.2f}")
        print(f"PnL Total:              ${total_pnl:+.2f} ({roi:+.2f}%)")
        print()
        
        print(f"Investido:              ${self.invested_balance:.2f}")
        print(f"Disponível:             ${self.available_balance:.2f}")
        print(f"Posições Abertas:       {len(self.open_positions)}")
        print()
        
        print("📊 LIMITES DE RISCO:")
        print(f"  • Máx risco por trade: {self.max_risk_per_trade*100:.1f}% (~${self.current_balance * self.max_risk_per_trade:.2f})")
        print(f"  • Mínimo R:R:          {self.min_reward_ratio:.1f}:1")
        print()
        
        print("🤖 LIMITES POR BOT:")
        for bot, limits in self.bot_limits.items():
            print(f"  • {bot}:")
            print(f"      - Máx por trade:  ${limits['max_per_trade']:.2f}")
            print(f"      - Max posições:   {limits['max_positions']}")
            print(f"      - Risco %:        {limits['risk_pct']:.1f}%")
        
        print("\n" + "=" * 70)
    
    def print_validation_example(self):
        """Mostra exemplo de validação de sinal"""
        print("\n" + "=" * 70)
        print("📋 EXEMPLO DE VALIDAÇÃO DE SINAL")
        print("=" * 70)
        
        # Cenário 1: Trade válido
        print("\n✅ CENÁRIO 1: Trade Válido (R:R 2:1)")
        symbol = "BTCUSDT"
        entry = 45000.0
        sl = 44775.0  # -$225 por unidade
        tp = 45450.0  # +$450 por unidade
        size = 1.0
        
        signal = TradeSignal(
            symbol=symbol,
            bot='bot_estavel',
            entry_price=entry,
            stop_loss_price=sl,
            take_profit_price=tp,
            position_size=size
        )
        
        print(f"  Symbol:        {symbol}")
        print(f"  Entry:         ${entry:.2f}")
        print(f"  Stop Loss:     ${sl:.2f} (Risco: ${signal.risk_amount:.2f})")
        print(f"  Take Profit:   ${tp:.2f} (Reward: ${signal.reward_amount:.2f})")
        print(f"  R:R Ratio:     {signal.risk_reward_ratio:.2f}:1")
        print(f"  Status:        {'✅ VÁLIDO' if signal.is_valid else '❌ INVÁLIDO'}")
        
        # Cenário 2: Trade inválido (R:R baixo)
        print("\n❌ CENÁRIO 2: Trade Inválido (R:R 0.5:1)")
        entry = 45000.0
        sl = 44925.0  # -$75 por unidade
        tp = 45037.5  # +$37.5 por unidade
        
        signal2 = TradeSignal(
            symbol=symbol,
            bot='bot_estavel',
            entry_price=entry,
            stop_loss_price=sl,
            take_profit_price=tp,
            position_size=size
        )
        
        print(f"  Symbol:        {symbol}")
        print(f"  Entry:         ${entry:.2f}")
        print(f"  Stop Loss:     ${sl:.2f} (Risco: ${signal2.risk_amount:.2f})")
        print(f"  Take Profit:   ${tp:.2f} (Reward: ${signal2.reward_amount:.2f})")
        print(f"  R:R Ratio:     {signal2.risk_reward_ratio:.2f}:1")
        print(f"  Status:        {'✅ VÁLIDO' if signal2.is_valid else '❌ INVÁLIDO'} - R:R muito baixo")
        
        print("\n" + "=" * 70)


def main():
    """Função principal"""
    import sys
    
    manager = CapitalManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'analyze':
            manager.print_summary()
            manager.print_validation_example()
        elif command == 'example':
            manager.print_validation_example()
        else:
            print(f"Comando desconhecido: {command}")
    else:
        manager.print_summary()


if __name__ == '__main__':
    main()
