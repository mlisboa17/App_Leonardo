"""
Dashboard Visual do Bot de Trading Leonardo
Interface em tempo real com Rich
"""
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box
from datetime import datetime
from typing import Dict, Optional
import time


class TradingDashboard:
    """Dashboard visual para o bot de trading"""
    
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        
        # Dados do bot
        self.bot_data = {
            'status': 'Inicializando...',
            'balance': 0.0,
            'daily_pnl': 0.0,
            'total_pnl': 0.0,
            'current_price': 0.0,
            'position': None,
            'trades_count': 0,
            'wins': 0,
            'losses': 0,
            'last_signal': 'Aguardando...',
            'rsi': None,
            'macd': None,
            'macd_signal': None,
            'sma_20': None,
            'sma_50': None,
            'sma_200': None,
            'last_update': datetime.now(),
            'symbol': 'BTC/USDT',
            'timeframe': '1h',
            'dry_run': False,
            'testnet': True,
            'kill_switch_active': False,
            'max_daily_loss': 500,
            'max_drawdown': 20,
            'interval': 60,
        }
        
        self._setup_layout()
    
    def _setup_layout(self):
        """Configura o layout do dashboard"""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        self.layout["left"].split(
            Layout(name="info", ratio=2),
            Layout(name="indicators", ratio=3),
        )
        
        self.layout["right"].split(
            Layout(name="performance", ratio=2),
            Layout(name="activity", ratio=3),
        )
    
    def _make_header(self) -> Panel:
        """Cria o cabeçalho"""
        status_color = "green" if self.bot_data['status'] == 'Operando' else "yellow"
        
        mode_badges = []
        if self.bot_data['testnet']:
            mode_badges.append("[cyan]🧪 TESTNET[/cyan]")
        else:
            mode_badges.append("[red]⚠️  REAL[/red]")
        
        if self.bot_data['dry_run']:
            mode_badges.append("[blue]🔸 DRY RUN[/blue]")
        
        if self.bot_data['kill_switch_active']:
            mode_badges.append("[red blink]🛑 KILL SWITCH[/red blink]")
        
        header_text = Text()
        header_text.append("🤖 BOT DE TRADING LEONARDO ", style="bold white")
        header_text.append(" | ", style="dim")
        header_text.append(f"Status: ", style="dim")
        header_text.append(f"{self.bot_data['status']}", style=f"bold {status_color}")
        header_text.append(" | ", style="dim")
        header_text.append(" ".join(mode_badges))
        
        return Panel(
            header_text,
            style="bold white on blue",
            box=box.DOUBLE
        )
    
    def _make_info_panel(self) -> Panel:
        """Cria painel de informações gerais"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="cyan", width=18)
        table.add_column(style="white bold")
        
        table.add_row("📈 Par", self.bot_data['symbol'])
        table.add_row("⏱️  Timeframe", self.bot_data['timeframe'])
        table.add_row("🔄 Intervalo", f"{self.bot_data['interval']}s")
        table.add_row("💰 Saldo", f"${self.bot_data['balance']:,.2f}")
        
        price_color = "green" if self.bot_data['current_price'] > 0 else "white"
        table.add_row(
            "💵 Preço Atual",
            f"[{price_color}]${self.bot_data['current_price']:,.2f}[/{price_color}]"
        )
        
        position_text = self.bot_data['position'] or "Nenhuma"
        position_color = "yellow" if self.bot_data['position'] else "dim"
        table.add_row(
            "📊 Posição",
            f"[{position_color}]{position_text}[/{position_color}]"
        )
        
        return Panel(
            table,
            title="[bold cyan]ℹ️  Informações[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED
        )
    
    def _make_indicators_panel(self) -> Panel:
        """Cria painel de indicadores técnicos"""
        table = Table(show_header=True, box=box.SIMPLE_HEAD, padding=(0, 1))
        table.add_column("Indicador", style="cyan bold", width=12)
        table.add_column("Valor", style="white", width=15)
        table.add_column("Sinal", style="bold", width=12)
        
        # RSI
        if self.bot_data['rsi'] is not None:
            rsi_val = self.bot_data['rsi']
            if rsi_val < 30:
                rsi_signal = "[green]📈 COMPRA[/green]"
            elif rsi_val > 70:
                rsi_signal = "[red]📉 VENDA[/red]"
            else:
                rsi_signal = "[dim]➖ NEUTRO[/dim]"
            table.add_row("RSI", f"{rsi_val:.2f}", rsi_signal)
        else:
            table.add_row("RSI", "[dim]Calculando...[/dim]", "[dim]---[/dim]")
        
        # MACD
        if self.bot_data['macd'] is not None and self.bot_data['macd_signal'] is not None:
            macd_val = self.bot_data['macd']
            macd_sig = self.bot_data['macd_signal']
            
            if macd_val > macd_sig:
                macd_signal = "[green]📈 ALTA[/green]"
            else:
                macd_signal = "[red]📉 BAIXA[/red]"
            
            table.add_row(
                "MACD",
                f"{macd_val:.2f} / {macd_sig:.2f}",
                macd_signal
            )
        else:
            table.add_row("MACD", "[dim]Calculando...[/dim]", "[dim]---[/dim]")
        
        # SMAs
        for period in [20, 50, 200]:
            sma_key = f'sma_{period}'
            if self.bot_data.get(sma_key) is not None:
                sma_val = self.bot_data[sma_key]
                table.add_row(f"SMA {period}", f"${sma_val:,.2f}", "")
            else:
                table.add_row(f"SMA {period}", "[dim]Calculando...[/dim]", "")
        
        return Panel(
            table,
            title="[bold yellow]📊 Indicadores Técnicos[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED
        )
    
    def _make_performance_panel(self) -> Panel:
        """Cria painel de performance"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="magenta", width=18)
        table.add_column(style="white bold")
        
        # PnL Diário
        pnl_color = "green" if self.bot_data['daily_pnl'] >= 0 else "red"
        pnl_symbol = "📈" if self.bot_data['daily_pnl'] >= 0 else "📉"
        table.add_row(
            "💵 PnL Diário",
            f"[{pnl_color}]{pnl_symbol} ${self.bot_data['daily_pnl']:,.2f}[/{pnl_color}]"
        )
        
        # PnL Total
        total_pnl_color = "green" if self.bot_data['total_pnl'] >= 0 else "red"
        table.add_row(
            "💰 PnL Total",
            f"[{total_pnl_color}]${self.bot_data['total_pnl']:,.2f}[/{total_pnl_color}]"
        )
        
        # Trades
        table.add_row("🔢 Total Trades", str(self.bot_data['trades_count']))
        
        # Win Rate
        total = self.bot_data['wins'] + self.bot_data['losses']
        if total > 0:
            win_rate = (self.bot_data['wins'] / total) * 100
            win_color = "green" if win_rate >= 50 else "red"
            table.add_row(
                "📊 Win Rate",
                f"[{win_color}]{win_rate:.1f}%[/{win_color}] ({self.bot_data['wins']}W / {self.bot_data['losses']}L)"
            )
        else:
            table.add_row("📊 Win Rate", "[dim]---[/dim]")
        
        # Limites de Segurança
        table.add_row("", "")  # Espaço
        table.add_row(
            "🛡️  Perda Máx/Dia",
            f"[yellow]${self.bot_data['max_daily_loss']}[/yellow]"
        )
        table.add_row(
            "🛡️  Drawdown Máx",
            f"[yellow]{self.bot_data['max_drawdown']}%[/yellow]"
        )
        
        return Panel(
            table,
            title="[bold magenta]📈 Performance[/bold magenta]",
            border_style="magenta",
            box=box.ROUNDED
        )
    
    def _make_activity_panel(self) -> Panel:
        """Cria painel de atividades recentes"""
        # Últimos eventos
        activity_text = Text()
        
        activity_text.append("🎯 Último Sinal:\n", style="bold")
        activity_text.append(f"   {self.bot_data['last_signal']}\n\n", style="white")
        
        activity_text.append("⏰ Última Atualização:\n", style="bold")
        activity_text.append(
            f"   {self.bot_data['last_update'].strftime('%H:%M:%S')}\n\n",
            style="dim"
        )
        
        activity_text.append("📝 Log de Ações:\n", style="bold cyan")
        activity_text.append("   • Analisando mercado...\n", style="dim")
        activity_text.append("   • Calculando indicadores...\n", style="dim")
        activity_text.append("   • Aguardando próximo ciclo...\n", style="dim")
        
        return Panel(
            activity_text,
            title="[bold green]📋 Atividade Recente[/bold green]",
            border_style="green",
            box=box.ROUNDED
        )
    
    def _make_footer(self) -> Panel:
        """Cria o rodapé"""
        footer_text = Text()
        footer_text.append("⌨️  Controles: ", style="bold")
        footer_text.append("[Ctrl+C] Parar Bot", style="yellow")
        footer_text.append(" | ", style="dim")
        footer_text.append(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", style="cyan")
        footer_text.append(" | ", style="dim")
        footer_text.append("💻 Bot Leonardo v1.0", style="dim")
        
        return Panel(
            footer_text,
            style="white on black",
            box=box.ROUNDED
        )
    
    def update_data(self, **kwargs):
        """Atualiza dados do dashboard"""
        self.bot_data.update(kwargs)
        self.bot_data['last_update'] = datetime.now()
    
    def render(self) -> Layout:
        """Renderiza o dashboard completo"""
        self.layout["header"].update(self._make_header())
        self.layout["info"].update(self._make_info_panel())
        self.layout["indicators"].update(self._make_indicators_panel())
        self.layout["performance"].update(self._make_performance_panel())
        self.layout["activity"].update(self._make_activity_panel())
        self.layout["footer"].update(self._make_footer())
        
        return self.layout
    
    def clear(self):
        """Limpa o console"""
        self.console.clear()


# Teste do dashboard
if __name__ == "__main__":
    dashboard = TradingDashboard()
    
    # Dados de exemplo
    dashboard.update_data(
        status='Operando',
        balance=10500.50,
        daily_pnl=50.25,
        total_pnl=500.50,
        current_price=91370.01,
        position='LONG',
        trades_count=15,
        wins=9,
        losses=6,
        last_signal='COMPRA executada - RSI em sobrevenda (28.5)',
        rsi=28.5,
        macd=150.23,
        macd_signal=145.10,
        sma_20=90000.00,
        sma_50=89500.00,
        sma_200=88000.00,
        symbol='BTC/USDT',
        timeframe='1h',
        testnet=True,
        dry_run=False
    )
    
    # Renderiza com Live (atualização em tempo real)
    with Live(dashboard.render(), refresh_per_second=1, screen=True) as live:
        try:
            for i in range(60):  # Demonstração por 60 segundos
                # Simula mudanças
                dashboard.update_data(
                    current_price=91370.01 + (i * 10),
                    rsi=28.5 + (i * 0.5),
                    daily_pnl=50.25 + (i * 2)
                )
                live.update(dashboard.render())
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    print("\n✅ Dashboard encerrado")
