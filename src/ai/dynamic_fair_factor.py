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
        # Tentar carregar configuração do arquivo YAML (config/bots_config.yaml)
        try:
            import yaml
            from pathlib import Path
            cfg_path = Path('config/bots_config.yaml')
            if cfg_path.exists():
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f) or {}
                    bots = cfg.get('bots', {})
                    # Carrega TP e RSI dinâmicos, caso existam
                    rsi_cfg = {}
                    tp_cfg = {}
                    for k, v in bots.items():
                        # mapeia chaves do YAML para as keys usadas pelo DynamicFairFactor
                        key = k
                        rsi_dyn = v.get('rsi_dinamico') or v.get('rsi_dynamics') or v.get('rsi_dynamic')
                        tp_dyn = v.get('take_profit_dinamico') or v.get('take_profit_dynamic') or v.get('take_profit_dynamics')
                        if rsi_dyn:
                            # transforma strings para números se necessário
                            mapped = {}
                            for time_k, val in rsi_dyn.items():
                                # time_k pode ser '0' ou string '60min' -> tenta extrair inteiro
                                try:
                                    t = int(str(time_k).replace('min', '').strip())
                                except Exception:
                                    try:
                                        t = int(float(str(time_k)))
                                    except Exception:
                                        continue
                                if isinstance(val, dict):
                                    mapped[t] = { 'compra': int(str(val.get('compra', '')).replace('<=','').strip()), 'venda': int(str(val.get('venda', '')).replace('>=','').strip()) }
                                else:
                                    # valor escrito como string - tentar parse
                                    # esperar no formato '{compra: <=35, venda: >=70}' no YAML; se for outra forma, ignore
                                    continue
                            rsi_cfg[key] = mapped
                        if tp_dyn:
                            mapped_tp = {}
                            for time_k, val in tp_dyn.items():
                                try:
                                    t = int(str(time_k).replace('min','').strip())
                                except Exception:
                                    try:
                                        t = int(float(str(time_k)))
                                    except Exception:
                                        continue
                                try:
                                    mapped_tp[t] = float(str(val).replace('%','').strip())
                                except Exception:
                                    continue
                            tp_cfg[key] = mapped_tp
                    self.rsi_config = rsi_cfg if rsi_cfg else None
                    self.tp_config = tp_cfg if tp_cfg else None
            else:
                self.rsi_config = None
                self.tp_config = None
        except Exception:
            # Se algo falhar, carrega mapeamento estático padrão (fallback)
            self.rsi_config = None
            self.tp_config = None

        # Se config não veio do YAML, definimos fallback padrão
        if not self.rsi_config:
            self.rsi_config = {
                "Bot_Estavel_Holder": {
                    0: {"compra": 35, "venda": 70},
                    60: {"compra": 40, "venda": 68},
                    120: {"compra": 45, "venda": 65},
                },
                "Bot_Medio_Swing": {
                    0: {"compra": 40, "venda": 65},
                    30: {"compra": 43, "venda": 63},
                    90: {"compra": 45, "venda": 60},
                },
                "Bot_Volatil_Momentum": {
                    0: {"compra": 45, "venda": 75},
                    20: {"compra": 48, "venda": 72},
                    60: {"compra": 50, "venda": 70},
                },
                "Bot_Meme_Scalper": {
                    0: {"compra": 50, "venda": 65},
                    10: {"compra": 53, "venda": 63},
                    20: {"compra": 55, "venda": 60},
                },
            }
        # NOTE: tp_config is set below after validation; remove earlier duplicate definitions

        self.tp_config = {
            "Bot_Estavel_Holder": {0: 2.5, 60: 1.5, 120: 1.0},
            "Bot_Medio_Swing": {0: 3.0, 30: 2.0, 90: 1.5},
            "Bot_Volatil_Momentum": {0: 2.0, 20: 1.5, 60: 1.0},
            "Bot_Meme_Scalper": {0: 1.2, 10: 0.8, 20: 0.5},
        }
        
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

    # ------------ Mapeamento por nome do bot (skeleton do usuário) ------------
    def _normalize_bot_name(self, bot_name: str) -> str:
        if bot_name in self.tp_config or bot_name in self.rsi_config:
            return bot_name
        # tenta converter camel/snake/nome para chave interna padrão
        key = bot_name.replace('-', '_').replace(' ', '_')
        if key in self.tp_config or key in self.rsi_config:
            return key
        # versão em CamelCase: bot_estavel -> Bot_Estavel_Holder tentativa
        # Não é possível converter automaticamente para todas as variações,
        # então retornamos o nome original.
        return bot_name

    def get_dynamic_take_profit_by_name(self, bot_name: str, minutes_open: float):
        """Retorna TP ajustado conforme tempo da posição, baseado no mapeamento por bot."""
        name = self._normalize_bot_name(bot_name)
        config = self.tp_config.get(name) or self.tp_config.get(bot_name)
        if not config:
            return None
        for t in sorted(config.keys(), reverse=True):
            if minutes_open >= t:
                return config[t]
        return config.get(0)

    def get_dynamic_rsi_by_name(self, bot_name: str, minutes_open: float):
        """Retorna dicionário com RSI de compra/venda conforme tempo da posição, baseado no mapeamento por bot."""
        name = self._normalize_bot_name(bot_name)
        config = self.rsi_config.get(name) or self.rsi_config.get(bot_name)
        if not config:
            return None
        for t in sorted(config.keys(), reverse=True):
            if minutes_open >= t:
                return config[t]
        return config.get(0)
    
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
