"""
Página dedicada ao Bot Unico (Sistema Adaptativo)
Mostra status, ajustes dinâmicos e métricas em tempo real
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import sys
import os

# Adiciona path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adaptive_bot_system import AdaptiveBotSystem

st.set_page_config(
    page_title="⚡ Bot Unico",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
.unico-header {
    background: linear-gradient(135deg, #9b4de4 0%, #6a1b9a 100%);
    padding: 20px;
    border-radius: 10px;
    color: white;
    margin-bottom: 20px;
}

.status-active {
    background-color: #1f771f;
    padding: 10px;
    border-radius: 5px;
    color: white;
}

.status-inactive {
    background-color: #772222;
    padding: 10px;
    border-radius: 5px;
    color: white;
}

.adjustment-box {
    background-color: #1a1a2e;
    padding: 15px;
    border-left: 4px solid #9b4de4;
    border-radius: 5px;
    margin: 10px 0;
}

.metric-card {
    background-color: #16213e;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #9b4de4;
}
</style>
""", unsafe_allow_html=True)


def load_config():
    """Carrega configuração dos bots"""
    try:
        import yaml
        config_file = Path("config/bots_config.yaml")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except:
        pass
    return {}


def load_account_data():
    """Carrega dados da conta"""
    try:
        balances_file = Path("data/dashboard_balances.json")
        if balances_file.exists():
            with open(balances_file, 'r') as f:
                return json.load(f)
    except:
        pass
    
    return {
        'usdt_balance': 0,
        'crypto_balance': 0,
        'total_balance': 0,
        'daily_pnl': 0
    }


def load_market_data():
    """Carrega dados do mercado"""
    try:
        market_file = Path("data/market_cache/last_scan.json")
        if market_file.exists():
            with open(market_file, 'r') as f:
                data = json.load(f)
                return {
                    'volatility': data.get('market', {}).get('volatility', 0)
                }
    except:
        pass
    
    return {'volatility': 0}


def toggle_bot_unico():
    """Ativa/desativa o Bot Unico com sincronização dos outros bots"""
    config = load_config()
    if config:
        is_enabling = not config['bot_unico'].get('enabled', False)
        config['bot_unico']['enabled'] = is_enabling
        
        # Sincroniza com os outros 4 bots
        other_bots = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']
        
        if is_enabling:
            # Quando ativa bot_unico, desativa os outros
            for bot in other_bots:
                if bot in config:
                    config[bot]['enabled'] = False
            action = "ativado"
            affect = "desativados"
        else:
            # Quando desativa bot_unico, reativa os outros
            for bot in other_bots:
                if bot in config:
                    config[bot]['enabled'] = True
            action = "desativado"
            affect = "reativados"
        
        try:
            import yaml
            with open('config/bots_config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            st.success(f"✅ Bot Unico {action}!")
            st.info(f"ℹ️ Os 4 bots especializados foram {affect} automaticamente")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")


def main():
    """Função principal"""
    
    # Header
    st.markdown("""
    <div class="unico-header">
        <h1>⚡ BOT UNICO - SISTEMA ADAPTATIVO HÍBRIDO</h1>
        <p>Controle unificado com ajustes dinâmicos automáticos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carrega dados
    config = load_config()
    account_data = load_account_data()
    market_data = load_market_data()
    
    if not config or 'bot_unico' not in config:
        st.error("❌ Configuração do Bot Unico não encontrada!")
        return
    
    unico_config = config['bot_unico']
    is_enabled = unico_config.get('enabled', False)
    
    # ===== SEÇÃO 1: STATUS =====
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if is_enabled:
            st.markdown("""
            <div class="status-active">
                <h3>🟢 ATIVO</h3>
                <p>Bot Unico está controlando todas as operações</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-inactive">
                <h3>🔴 INATIVO</h3>
                <p>Bots especializados estão no controle</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Botão para ativar/desativar
        if st.button(
            "🔴 Desativar Bot Unico" if is_enabled else "🟢 Ativar Bot Unico",
            use_container_width=True,
            key="toggle_unico"
        ):
            toggle_bot_unico()
    
    with col3:
        st.metric("📍 Status", "ATIVO" if is_enabled else "INATIVO")
    
    st.markdown("---")
    
    # ===== SEÇÃO 2: SISTEMA ADAPTATIVO =====
    st.subheader("🔧 SISTEMA ADAPTATIVO")
    
    system = AdaptiveBotSystem()
    current_config = system.get_current_configuration(market_data, account_data)
    
    # Mostra ajustes
    adjustments = current_config.get('_adaptive_adjustments', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Parâmetros Adaptativos:**")
        st.metric("📈 Take Profit", f"{adjustments.get('take_profit', 0):.2f}%")
        st.metric("🛑 Stop Loss", f"{adjustments.get('stop_loss', 0):.2f}%")
    
    with col2:
        st.markdown("**💰 Dados da Conta:**")
        st.metric("💵 Saldo USDT", f"${account_data.get('usdt_balance', 0):.2f}")
        st.metric("📅 PnL Hoje", f"${account_data.get('daily_pnl', 0):+.2f}")
    
    st.markdown("---")
    
    # ===== SEÇÃO 3: RAZÕES DOS AJUSTES =====
    st.subheader("💡 Razões dos Ajustes")
    
    reasons = adjustments.get('reason', [])
    
    if reasons:
        for i, reason in enumerate(reasons, 1):
            st.markdown(f"""
            <div class="adjustment-box">
                <strong>{reason}</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ Nenhum ajuste especial necessário - Mercado em condições normais")
    
    st.markdown("---")
    
    # ===== SEÇÃO 4: CONFIGURAÇÃO =====
    st.subheader("⚙️ CONFIGURAÇÃO DO BOT UNICO")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Portfolio:**")
        portfolio = unico_config.get('portfolio', [])
        for crypto in portfolio:
            st.write(f"• {crypto['symbol']}: {crypto.get('weight', 0)}%")
    
    with col2:
        st.markdown("**Parâmetros Base:**")
        risk = unico_config.get('risk', {})
        st.write(f"• Max Hold: {risk.get('max_hold_minutes', 0)} min")
        st.write(f"• Min Interval: {risk.get('min_interval_minutes', 0)} min")
        st.write(f"• Max Positions: {unico_config.get('trading', {}).get('max_positions', 0)}")
        st.write(f"• Amount/Trade: ${unico_config.get('trading', {}).get('amount_per_trade', 0)}")
    
    with col3:
        st.markdown("**Regras Adaptativas:**")
        adaptive = unico_config.get('adaptive_rules', {})
        st.write(f"• Low Balance: ${adaptive.get('low_balance_threshold', 0)}")
        st.write(f"• High Vol: {adaptive.get('high_volatility_threshold', 0)}%")
        st.write(f"• Profit Lock: ${adaptive.get('profit_lock_on_daily_pnl', 0)}")
        st.write(f"• Loss Recovery: {adaptive.get('consecutive_losses_threshold', 0)} losses")
    
    st.markdown("---")
    
    # ===== SEÇÃO 5: COMO FUNCIONA =====
    st.subheader("📚 Como Funciona")
    
    with st.expander("🔍 Entender o Sistema Adaptativo"):
        st.markdown("""
        ### Bot Unico - Sistema Híbrido Adaptativo
        
        O Bot Unico é um sistema inteligente que **se adapta dinamicamente** mantendo sempre margens mínimas de lucro.
        
        #### 🎯 Características Principais:
        
        1. **Saldo USDT Baixo** (< $50)
           - Aumenta o percentual de venda para recuperar capital
           - Exemplo: Se USDT = $30, aumenta TP em +0.5%
           - Garante margem mínima de 0.5% mesmo em stress
        
        2. **Volatilidade Alta** (> 5%)
           - Reduz Take Profit para sair mais cedo (menos risco)
           - Exemplo: Reduz TP em -0.3%
           - Protege contra reversões bruscas
        
        3. **Volatilidade Baixa** (< 1%)
           - Aumenta Take Profit para deixar correr mais
           - Exemplo: Aumenta TP em +0.2%
           - Aproveita movimentos lentos
        
        4. **PnL do Dia Alto** (> $100)
           - Trava os ganhos reduzindo TP
           - Realiza lucros antes de reversão
           - Garante ganhos do dia
        
        5. **Perdas Consecutivas** (> 3)
           - Ativa modo recuperação
           - Aumenta % de venda em +0.7%
           - Busca recuperar perdas
        
        #### ⚠️ Garantias de Segurança:
        
        - **TP Mínimo:** Nunca abaixo de 0.5% (margem de segurança)
        - **SL Máximo:** Nunca acima de -0.5% (stop muito apertado)
        - **Diversificação:** 9 posições máx, $39.15 por trade
        - **Monitoramento:** Atualiza a cada 5 minutos
        
        #### 🔄 Fluxo de Decisão:
        
        ```
        Entrada do Trade
            ↓
        Verifica Saldo USDT
            ↓
        Verifica Volatilidade
            ↓
        Verifica PnL do Dia
            ↓
        Verifica Perdas Consecutivas
            ↓
        Aplica Ajustes (garantindo mínimos)
            ↓
        Executa Trade com Parâmetros Adaptivos
        ```
        
        #### 📊 Vantagens:
        
        ✅ Adaptável a qualquer condição de mercado
        ✅ Margem mínima de 0.5% garantida
        ✅ Recuperação automática de perdas
        ✅ Proteção contra saldo baixo
        ✅ Aproveita volatilidade quando favorável
        """)
    
    st.markdown("---")
    
    # ===== SEÇÃO 6: ESTADO ATUAL =====
    st.subheader("📈 Estado Atual do Sistema")
    
    state = system.state
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔢 Perdas Consecutivas", state.get('consecutive_losses', 0))
    
    with col2:
        st.metric("💰 PnL do Dia", f"${state.get('daily_pnl', 0):.2f}")
    
    with col3:
        last_update = state.get('last_update', 'Nunca')
        if last_update != 'Nunca':
            try:
                last_dt = datetime.fromisoformat(last_update)
                time_ago = datetime.now() - last_dt
                if time_ago.seconds < 60:
                    time_str = f"{time_ago.seconds}s atrás"
                elif time_ago.seconds < 3600:
                    time_str = f"{time_ago.seconds // 60}m atrás"
                else:
                    time_str = f"{time_ago.seconds // 3600}h atrás"
                st.metric("🕐 Última Atualização", time_str)
            except:
                st.metric("🕐 Última Atualização", "Erro ao calcular")
        else:
            st.metric("🕐 Última Atualização", "Nunca")
    
    with col4:
        st.metric("📊 Mercado", f"Vol: {market_data.get('volatility', 0):.1f}%")
    
    st.markdown("---")
    
    # ===== AVISO =====
    if is_enabled:
        st.warning("""
        ⚠️ **Bot Unico Ativo**
        
        - Os 4 bots especializados (Estável, Médio, Volátil, Meme) estão **PAUSADOS**
        - Apenas o Bot Unico está operando
        - Desative o Bot Unico para retomar operação dos 4 bots
        """)


if __name__ == "__main__":
    main()
