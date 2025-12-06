"""
SISTEMA DE FATOR DINÂMICO - LÓGICA DA FEIRA
=============================================

ANALOGIA:
- Na feira, de manhã o preço está alto
- Com o passar das horas, o feirante vai baixando o preço
- No final do dia, vende por qualquer preço para não perder

APLICAÇÃO NO TRADING:

VENDA (começa exigente, vai relaxando):
────────────────────────────────────────
Tempo 0:    TP = 2.0% (exigente - quer preço alto)
Tempo 30m:  TP = 1.5% (um pouco mais flexível)
Tempo 60m:  TP = 1.0% (aceita menos)
Tempo 90m:  TP = 0.5% (não quer perder)
Tempo 120m: TP = 0.2% (vende quase no zero pra liberar capital)

COMPRA (começa exigente, vai relaxando):
────────────────────────────────────────
RSI 0m:    < 25 (só compra muito oversold)
RSI 30m:   < 28 (relaxa um pouco)
RSI 60m:   < 32 (aceita mais)
RSI 90m:   < 35 (mais flexível)

CONDIÇÃO EXTRA PARA VENDA:
────────────────────────────────────────
Só vende quando tendência sair de ALTA para LATERAL/QUEDA
- Se está em ALTA: SEGURA (mesmo que atinja TP dinâmico)
- Se virou LATERAL: Pode vender no TP dinâmico
- Se virou QUEDA: Vende imediatamente

FÓRMULA DO FATOR:
────────────────────────────────────────
fator_tempo = min(1.0, tempo_aberto / tempo_maximo)

TP_dinamico = TP_inicial * (1 - fator_tempo * 0.7)
   Exemplo: TP=2%, tempo=60min, max=120min
   fator = 60/120 = 0.5
   TP_dinamico = 2% * (1 - 0.5*0.7) = 2% * 0.65 = 1.3%

RSI_dinamico = RSI_base + (fator_tempo * 10)
   Exemplo: RSI=25, tempo=60min, max=120min
   fator = 0.5
   RSI_dinamico = 25 + (0.5 * 10) = 30
"""

class DynamicFairFactor:
    """
    Sistema de Fator Dinâmico - Lógica da Feira
    
    Com o tempo:
    - VENDA: fica menos exigente (aceita TP menor)
    - COMPRA: fica menos exigente (aceita RSI maior)
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Tempos máximos por tipo de bot (minutos)
        self.max_hold_times = {
            'bot_estavel': 180,
            'bot_medio': 120,
            'bot_volatil': 90,
            'bot_meme': 60
        }
        
        # Fator de redução máxima (0.7 = reduz até 70% do TP original)
        self.max_reduction = 0.7
        
        # RSI base e incremento máximo
        self.rsi_base = {
            'bot_estavel': 25,
            'bot_medio': 23,
            'bot_volatil': 22,
            'bot_meme': 20
        }
        self.rsi_max_increment = 12  # Adiciona até 12 ao RSI com o tempo
        
    def get_time_factor(self, minutes_open: float, bot_type: str) -> float:
        """
        Calcula o fator de tempo (0.0 a 1.0)
        0.0 = acabou de abrir (muito exigente)
        1.0 = muito tempo aberto (pouco exigente)
        """
        max_time = self.max_hold_times.get(bot_type, 120)
        factor = min(1.0, minutes_open / max_time)
        return factor
    
    def get_dynamic_take_profit(self, base_tp: float, minutes_open: float, 
                                 bot_type: str, trend: str = 'LATERAL') -> tuple:
        """
        Calcula Take Profit dinâmico baseado no tempo
        
        Returns: (tp_dinamico, pode_vender, motivo)
        """
        factor = self.get_time_factor(minutes_open, bot_type)
        
        # Reduz TP com o tempo (mínimo 20% do original)
        reduction = factor * self.max_reduction
        tp_dinamico = base_tp * (1 - reduction)
        tp_dinamico = max(tp_dinamico, base_tp * 0.2)  # Mínimo 20% do TP original
        
        # Verifica tendência para permitir venda
        pode_vender = False
        motivo = ""
        
        if trend == 'ALTA':
            # Em alta: só vende se tempo muito longo OU lucro muito alto
            if factor > 0.8:
                pode_vender = True
                motivo = f"⏰ Tempo longo ({minutes_open:.0f}m) - liberando capital"
            else:
                pode_vender = False
                motivo = f"📈 Tendência ALTA - segurando (TP dinâmico: {tp_dinamico:.2f}%)"
        
        elif trend == 'LATERAL':
            # Lateral: pode vender no TP dinâmico
            pode_vender = True
            motivo = f"➖ Tendência LATERAL - TP dinâmico: {tp_dinamico:.2f}%"
        
        else:  # QUEDA
            # Em queda: vende imediatamente se tiver lucro
            pode_vender = True
            tp_dinamico = max(0.1, tp_dinamico * 0.5)  # Reduz mais ainda
            motivo = f"📉 Tendência QUEDA - vendendo rápido (TP: {tp_dinamico:.2f}%)"
        
        return tp_dinamico, pode_vender, motivo
    
    def get_dynamic_rsi(self, base_rsi: float, minutes_waiting: float, 
                        bot_type: str) -> float:
        """
        Calcula RSI dinâmico para compra baseado no tempo esperando
        
        Quanto mais tempo sem comprar, mais flexível fica
        """
        # Para compra, usamos tempo desde última compra
        factor = self.get_time_factor(minutes_waiting, bot_type)
        
        # Aumenta RSI aceito com o tempo
        increment = factor * self.rsi_max_increment
        rsi_dinamico = base_rsi + increment
        
        return min(rsi_dinamico, 45)  # Máximo RSI 45 (nunca compra em overbought)
    
    def should_sell(self, position: dict, current_price: float, 
                    trend: str, bot_type: str, base_tp: float) -> tuple:
        """
        Decide se deve vender usando lógica da feira
        
        Returns: (deve_vender, motivo, tp_usado)
        """
        from datetime import datetime
        
        entry_price = position.get('entry_price', current_price)
        entry_time = position.get('time', datetime.now().isoformat())
        
        if isinstance(entry_time, str):
            entry_time = datetime.fromisoformat(entry_time)
        
        minutes_open = (datetime.now() - entry_time).total_seconds() / 60
        
        # Calcula lucro atual
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Pega TP dinâmico
        tp_dinamico, pode_vender, motivo = self.get_dynamic_take_profit(
            base_tp, minutes_open, bot_type, trend
        )
        
        # Verifica se deve vender
        if pnl_pct >= tp_dinamico and pode_vender:
            return True, f"💰 {motivo} | Lucro: {pnl_pct:.2f}% >= TP: {tp_dinamico:.2f}%", tp_dinamico
        
        if not pode_vender:
            return False, motivo, tp_dinamico
        
        return False, f"Aguardando TP {tp_dinamico:.2f}% (atual: {pnl_pct:.2f}%)", tp_dinamico


# Teste
if __name__ == "__main__":
    feira = DynamicFairFactor()
    
    print("="*60)
    print("🏪 SIMULAÇÃO LÓGICA DA FEIRA")
    print("="*60)
    
    base_tp = 2.0  # 2% Take Profit base
    
    print("\n📊 EVOLUÇÃO DO TAKE PROFIT COM O TEMPO:")
    print("-"*60)
    for minutes in [0, 15, 30, 45, 60, 90, 120, 150, 180]:
        for trend in ['ALTA', 'LATERAL', 'QUEDA']:
            tp, pode, motivo = feira.get_dynamic_take_profit(base_tp, minutes, 'bot_medio', trend)
            status = "✅" if pode else "🔒"
            print(f"  {minutes:3}min | {trend:7} | TP: {tp:.2f}% | {status} {motivo[:40]}")
        print()
    
    print("\n📊 EVOLUÇÃO DO RSI PARA COMPRA:")
    print("-"*60)
    base_rsi = 25
    for minutes in [0, 15, 30, 45, 60, 90, 120]:
        rsi = feira.get_dynamic_rsi(base_rsi, minutes, 'bot_medio')
        print(f"  {minutes:3}min esperando | RSI aceito: < {rsi:.1f}")
