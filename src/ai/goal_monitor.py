"""
📊 MONITOR DE METAS - R7_V1 (META 10% AO MÊS)
=============================================
Monitora progresso em relação às metas mensais AGRESSIVAS.

🎯 META PRINCIPAL: 10% ao mês = $100/mês com $1000

NÍVEIS DE META (FASE 1 - Spot Agressivo):
- 🏆 SUPER: $120/mês (12%) - Excepcional
- ✅ META: $100/mês (10%) - Objetivo principal
- 📊 BOM: $80/mês (8%) - Aceitável
- ⚠️ MÍNIMO: $50/mês (5%) - Mínimo aceitável

NÍVEIS DE META (FASE 2 - Híbrido com Futuros):
- 🏆 SUPER: $150/mês (15%)
- ✅ META: $120/mês (12%)
- 📊 BOM: $100/mês (10%)
- ⚠️ MÍNIMO: $80/mês (8%)

⚠️ RISCO: Metas agressivas = Risco maior de perdas
🛡️ PROTEÇÃO: Daily stop 5%, Emergency stop 15%

Autor: Sistema R7_V1
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple


class GoalMonitor:
    """Monitor de metas mensais e diárias - META 10%"""
    
    # Metas FASE 1 (Spot Agressivo) - META 10%
    PHASE1_GOALS = {
        'super': {'value': 120, 'percentage': 12.0, 'emoji': '🏆', 'name': 'SUPER'},
        'meta': {'value': 100, 'percentage': 10.0, 'emoji': '✅', 'name': 'META'},
        'bom': {'value': 80, 'percentage': 8.0, 'emoji': '📊', 'name': 'BOM'},
        'minimo': {'value': 50, 'percentage': 5.0, 'emoji': '⚠️', 'name': 'MÍNIMO'},
    }
    
    # Metas FASE 2 (Híbrido com Futuros 2x) - META 12%
    PHASE2_GOALS = {
        'super': {'value': 150, 'percentage': 15.0, 'emoji': '🏆', 'name': 'SUPER'},
        'meta': {'value': 120, 'percentage': 12.0, 'emoji': '✅', 'name': 'META'},
        'bom': {'value': 100, 'percentage': 10.0, 'emoji': '📊', 'name': 'BOM'},
        'minimo': {'value': 80, 'percentage': 8.0, 'emoji': '⚠️', 'name': 'MÍNIMO'},
    }
    
    # Metas diárias (30 dias/mês)
    PHASE1_DAILY = {'super': 4.0, 'meta': 3.33, 'bom': 2.67, 'minimo': 1.67}  # $100/mês = $3.33/dia
    PHASE2_DAILY = {'super': 5.0, 'meta': 4.0, 'bom': 3.33, 'minimo': 2.67}   # $120/mês = $4/dia
    
    def __init__(self, capital: float = 1000, phase: int = 1):
        self.capital = capital
        self.phase = phase  # 1 = Spot Agressivo, 2 = Híbrido
        self.data_file = Path("data/goal_tracking.json")
        self.history = self._load_history()
        
        # Seleciona metas baseado na fase
        self.MONTHLY_GOALS = self.PHASE1_GOALS if phase == 1 else self.PHASE2_GOALS
        self.DAILY_GOALS = self.PHASE1_DAILY if phase == 1 else self.PHASE2_DAILY
    
    def set_phase(self, phase: int):
        """Muda a fase (1=Spot Agressivo, 2=Híbrido)"""
        self.phase = phase
        self.MONTHLY_GOALS = self.PHASE1_GOALS if phase == 1 else self.PHASE2_GOALS
        self.DAILY_GOALS = self.PHASE1_DAILY if phase == 1 else self.PHASE2_DAILY
    
    def _load_history(self) -> Dict:
        """Carrega histórico de metas"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'monthly': {},
            'daily': {},
            'total_pnl': 0,
            'start_date': datetime.now().isoformat(),
            'phase': 1
        }
    
    def _save_history(self):
        """Salva histórico"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.history['phase'] = self.phase
        with open(self.data_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_trade_result(self, pnl: float):
        """Registra resultado de um trade"""
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')
        
        # Atualiza diário
        if today not in self.history['daily']:
            self.history['daily'][today] = 0
        self.history['daily'][today] += pnl
        
        # Atualiza mensal
        if month not in self.history['monthly']:
            self.history['monthly'][month] = 0
        self.history['monthly'][month] += pnl
        
        # Atualiza total
        self.history['total_pnl'] += pnl
        
        self._save_history()
    
    def get_daily_progress(self) -> Dict:
        """Retorna progresso diário"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_pnl = self.history['daily'].get(today, 0)
        
        result = {
            'date': today,
            'pnl': daily_pnl,
            'phase': self.phase,
            'goals': {}
        }
        
        for goal_key, goal_value in self.DAILY_GOALS.items():
            goal_info = self.MONTHLY_GOALS[goal_key]
            progress = (daily_pnl / goal_value * 100) if goal_value > 0 else 0
            achieved = daily_pnl >= goal_value
            
            result['goals'][goal_key] = {
                'name': goal_info['name'],
                'emoji': goal_info['emoji'],
                'target': goal_value,
                'progress': min(100, progress),
                'achieved': achieved,
                'remaining': max(0, goal_value - daily_pnl)
            }
        
        return result
    
    def get_monthly_progress(self) -> Dict:
        """Retorna progresso mensal"""
        month = datetime.now().strftime('%Y-%m')
        monthly_pnl = self.history['monthly'].get(month, 0)
        
        # Dias passados no mês
        day_of_month = datetime.now().day
        
        result = {
            'month': month,
            'pnl': monthly_pnl,
            'day_of_month': day_of_month,
            'phase': self.phase,
            'phase_name': 'Spot Otimizado' if self.phase == 1 else 'Híbrido 50/50',
            'goals': {}
        }
        
        for goal_key, goal_info in self.MONTHLY_GOALS.items():
            goal_value = goal_info['value']
            progress = (monthly_pnl / goal_value * 100) if goal_value > 0 else 0
            achieved = monthly_pnl >= goal_value
            
            # Projeção para fim do mês
            if day_of_month > 0:
                daily_avg = monthly_pnl / day_of_month
                projected = daily_avg * 30
            else:
                projected = 0
            
            result['goals'][goal_key] = {
                'name': goal_info['name'],
                'emoji': goal_info['emoji'],
                'target': goal_value,
                'progress': min(100, progress),
                'achieved': achieved,
                'remaining': max(0, goal_value - monthly_pnl),
                'projected': round(projected, 2),
                'on_track': projected >= goal_value
            }
        
        return result
    
    def get_current_goal_status(self) -> Tuple[str, str, float]:
        """
        Retorna qual meta está mais próxima de ser atingida.
        Returns: (goal_key, goal_name, progress_pct)
        """
        month_progress = self.get_monthly_progress()
        
        # Encontra meta mais próxima de ser atingida
        best_goal = None
        best_progress = 0
        
        for goal_key, goal_data in month_progress['goals'].items():
            if goal_data['progress'] > best_progress:
                best_progress = goal_data['progress']
                best_goal = goal_key
        
        if best_goal:
            goal_info = self.MONTHLY_GOALS[best_goal]
            return best_goal, goal_info['name'], best_progress
        
        return 'minimo', 'MÍNIMO', 0
    
    def get_status_report(self) -> str:
        """Retorna relatório formatado"""
        daily = self.get_daily_progress()
        monthly = self.get_monthly_progress()
        
        phase_name = "🟢 FASE 1: Spot Otimizado" if self.phase == 1 else "🔷 FASE 2: Híbrido 50/50"
        
        report = f"""
╔═══════════════════════════════════════════════════════════════╗
║          📊 MONITOR DE METAS - ESTRATÉGIA HÍBRIDA             ║
║                    {phase_name:<35}                 ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  📅 HOJE ({daily['date']}):  ${daily['pnl']:+.2f}                    
║  ─────────────────────────────────────────────────────────────║
"""
        
        for goal_key in ['super_meta', 'meta_normal', 'media', 'minimo']:
            g = daily['goals'][goal_key]
            status = "✅" if g['achieved'] else f"{g['progress']:.0f}%"
            report += f"║  {g['emoji']} {g['name']:<12}: ${g['target']:.2f}/dia  [{status}]\n"
        
        report += f"""║                                                               ║
║  📆 ESTE MÊS ({monthly['month']}):  ${monthly['pnl']:+.2f}           
║  ─────────────────────────────────────────────────────────────║
"""
        
        for goal_key in ['super_meta', 'meta_normal', 'media', 'minimo']:
            g = monthly['goals'][goal_key]
            status = "✅" if g['achieved'] else f"{g['progress']:.0f}%"
            proj_status = "📈" if g['on_track'] else "📉"
            report += f"║  {g['emoji']} {g['name']:<12}: ${g['target']}/mês [{status}] {proj_status} Proj: ${g['projected']:.0f}\n"
        
        report += """║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        return report


# Singleton
_goal_monitor = None

def get_goal_monitor(capital: float = 1000, phase: int = 1) -> GoalMonitor:
    """
    Obtém instância do GoalMonitor.
    
    Args:
        capital: Capital inicial ($1000 padrão)
        phase: Fase da estratégia híbrida (1=Spot, 2=Híbrido 50/50)
    """
    global _goal_monitor
    if _goal_monitor is None:
        _goal_monitor = GoalMonitor(capital, phase)
    return _goal_monitor
