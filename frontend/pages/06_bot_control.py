"""
🎮 Bot Control Page - Ativar/Pausar Bots, Redistribuir Cryptos e UnicoBot
"""

import streamlit as st
import sys
import json
from pathlib import Path
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.session_manager import get_config, get_history, get_unico_config, get_positions, force_reload
from frontend.utils.data_loaders import save_bots_config, save_unico_bot_config
from frontend.utils.calculators import get_pnl_by_bot, get_daily_pnl


def redistribute_cryptos_from_paused_bots():
    """Redistribui cryptos de bots pausados para bots ativos"""
    positions_dict = get_positions()
    config = get_config()
    
    if not positions_dict or not config:
        return {"success": False, "message": "Sem posições ou config"}
    
    # Converter dict para lista com símbolos
    if isinstance(positions_dict, dict):
        positions = [
            {**pos, 'symbol': symbol} 
            for symbol, pos in positions_dict.items() 
            if isinstance(pos, dict)
        ]
    else:
        positions = positions_dict if positions_dict else []
    
    if not positions:
        return {"success": False, "message": "Nenhuma posição encontrada"}
    
    bots = config.get('bots', config)
    
    # Identificar bots pausados com posições
    paused_positions = {}
    active_bots = []
    
    for bot_type in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']:
        if bot_type in bots:
            is_active = bots[bot_type].get('enabled', False)
            
            if is_active:
                active_bots.append(bot_type)
            else:
                # Bot pausado - pegar suas posições
                bot_positions = [p for p in positions if p.get('bot_type') == bot_type]
                if bot_positions:
                    paused_positions[bot_type] = bot_positions
    
    if not paused_positions:
        return {"success": False, "message": "Nenhum bot pausado com posições"}
    
    if not active_bots:
        return {"success": False, "message": "Nenhum bot ativo para receber"}
    
    # Redistribuir
    redistributions = []
    active_bot_idx = 0
    
    for paused_bot, positions_list in paused_positions.items():
        for pos in positions_list:
            # Atribui para próximo bot ativo (round-robin)
            new_owner = active_bots[active_bot_idx % len(active_bots)]
            symbol = pos.get('symbol')
            
            # Atualizar no dicionário original
            if symbol in positions_dict:
                positions_dict[symbol]['bot_type'] = new_owner
                positions_dict[symbol]['redistributed_at'] = datetime.now().isoformat()
                positions_dict[symbol]['original_bot'] = paused_bot
            
            redistributions.append({
                'symbol': symbol,
                'from': paused_bot,
                'to': new_owner,
                'amount': pos.get('amount', 0),
                'side': pos.get('side', 'LONG')
            })
            
            active_bot_idx += 1
    
    # Salvar posições atualizadas (mantém formato dict)
    positions_file = Path("data/multibot_positions.json")
    if positions_file.exists():
        with open(positions_file, 'w', encoding='utf-8') as f:
            json.dump(positions_dict, f, indent=2)
    
    return {
        "success": True,
        "message": f"Redistribuídas {len(redistributions)} posições",
        "redistributions": redistributions
    }


def render():
    """Renderiza página de controle de bots"""
    st.markdown('<div class="main-header">🎮 CONTROLE DE BOTS - App R7</div>', unsafe_allow_html=True)
    
    config = get_config()
    unico_config = get_unico_config()
    
    if not config:
        st.error("❌ Arquivo de configuração não encontrado!")
        return
    
    # ===== SEÇÃO: UNICOBOT =====
    st.header("⚡ UnicoBot - Controle Unificado")
    
    unico_enabled = unico_config.get('enabled', False) if unico_config else False
    operation_mode = unico_config.get('operation_mode', 'SOLO') if unico_config else 'SOLO'
    
    # Status atual
    if unico_enabled:
        mode_info = unico_config.get('operation_modes', {}).get(operation_mode, {})
        nickname = mode_info.get('nickname', operation_mode)
        reference = mode_info.get('reference', '')
        
        if operation_mode == 'SOLO':
            st.success(f"🟢 **Bot Unico ATIVO - {nickname}**")
            st.info(f"📌 {reference}")
            st.info("📌 Bot Único assume TODAS as cryptos e TODO o capital. Os 4 bots ficam pausados.")
        elif operation_mode == 'HYBRID':
            st.success(f"🟢 **Bot Unico ATIVO - {nickname}**")
            st.info(f"📌 {reference}")
            st.info("📌 Bot Único trabalha JUNTO com os 4 bots. Cada um tem sua própria carteira (+1 bot no sistema).")
        elif operation_mode == 'FOMINHA':
            st.success(f"🟢 **Bot Unico ATIVO - {nickname}**")
            st.warning(f"⚡ {reference}")
            st.warning("⚡ Modo AGRESSIVO! Bot Único + 4 bots ativos. Bot Único fica com 70% dos lucros de TODOS!")
            st.info("🤖 IA monitora Fear & Greed + Notícias a cada 30s. Máximo lucro rápido!")
        elif operation_mode == 'EQUIPE':
            st.success(f"🟢 **Bot Unico ATIVO - {nickname}**")
            st.info(f"📌 {reference}")
            st.info("📌 Todos os 5 bots trabalham juntos. Lucro dividido igualmente (20% cada).")
            st.info("🤖 IA coordena estratégias e redistribui capital automaticamente.")
    else:
        st.info("🔴 **Bot Unico INATIVO** - Os 4 bots especializados estão no controle")
    
    st.markdown("---")
    
    # Configuração do modo
    if unico_enabled:
        st.subheader("⚙️ Configurar Modo de Operação")
        
        col_mode1, col_mode2, col_mode3, col_mode4 = st.columns(4)
        
        with col_mode1:
            st.markdown("""
            **🎯 MODO SOLO**
            - Bot assume TUDO
            - Pausa 4 bots
            - Controle total
            """)
            
            if operation_mode != 'SOLO':
                if st.button("🎯 SOLO", type="primary", use_container_width=True, key="btn_solo"):
                    unico_config['operation_mode'] = 'SOLO'
                    save_unico_bot_config(unico_config)
                    
                    # Pausa os 4 bots
                    bots = config.get('bots', config)
                    for bot_type in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']:
                        if bot_type in bots and isinstance(bots[bot_type], dict):
                            bots[bot_type]['enabled'] = False
                    
                    if 'bots' in config:
                        config['bots'] = bots
                    save_bots_config(config)
                    
                    force_reload('config')
                    force_reload('unico')
                    st.success("✅ Modo SOLO ativado!")
                    st.rerun()
            else:
                st.success("✅ ATIVO")
        
        with col_mode2:
            st.markdown("""
            **🔄 MODO HÍBRIDO**
            - 5 bots juntos
            - Carteira própria
            - Diversificação
            """)
            
            if operation_mode != 'HYBRID':
                if st.button("🔄 HÍBRIDO", type="secondary", use_container_width=True, key="btn_hybrid"):
                    unico_config['operation_mode'] = 'HYBRID'
                    save_unico_bot_config(unico_config)
                    force_reload('unico')
                    st.success("✅ Modo HÍBRIDO ativado!")
                    st.rerun()
            else:
                st.success("✅ ATIVO")
        
        with col_mode3:
            st.markdown("""
            **🤑 MODO FOMINHA**
            - AGRESSIVO
            - Bot leva 70%
            - IA 24/7
            """)
            
            if operation_mode != 'FOMINHA':
                if st.button("🤑 FOMINHA", type="secondary", use_container_width=True, key="btn_fominha"):
                    unico_config['operation_mode'] = 'FOMINHA'
                    save_unico_bot_config(unico_config)
                    force_reload('unico')
                    st.success("✅ Modo FOMINHA ativado!")
                    st.balloons()
                    st.rerun()
            else:
                st.success("✅ ATIVO")
        
        with col_mode4:
            st.markdown("""
            **🤝 MODO EQUIPE**
            - Colaborativo
            - Lucro dividido
            - IA coordena
            """)
            
            if operation_mode != 'EQUIPE':
                if st.button("🤝 EQUIPE", type="secondary", use_container_width=True, key="btn_equipe"):
                    unico_config['operation_mode'] = 'EQUIPE'
                    save_unico_bot_config(unico_config)
                    st.success("✅ Modo EQUIPE ativado!")
                    st.rerun()
            else:
                st.success("✅ ATIVO")
    
    st.markdown("---")
    
    # Controle ON/OFF
    col1, col2 = st.columns([1, 1])
    
    with col2:
        if unico_enabled:
            if st.button("🔴 DESATIVAR UnicoBot", type="secondary", use_container_width=True):
                if unico_config:
                    unico_config['enabled'] = False
                    save_unico_bot_config(unico_config)
                    force_reload('unico')
                    st.success("✅ UnicoBot desativado!")
                    st.rerun()
        else:
            # Ao ativar, perguntar o modo
            st.subheader("Escolha o modo de operação:")
            
            mode_choice = st.radio(
                "Modo",
                ["SOLO - Bot assume tudo", 
                 "HÍBRIDO - Trabalha com 4 bots",
                 "FOMINHA - Bot leva 70% dos lucros 🤑",
                 "EQUIPE - Lucro dividido igualmente 🤝"],
                index=0,
                key="mode_choice"
            )
            
            if st.button("⚡ ATIVAR UnicoBot", type="primary", use_container_width=True):
                if unico_config:
                    unico_config['enabled'] = True
                    
                    # Define o modo baseado na escolha
                    if "SOLO" in mode_choice:
                        unico_config['operation_mode'] = 'SOLO'
                        
                        # Desativa todos os bots especializados
                        bots = config.get('bots', config)
                        for bot_type in ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme']:
                            if bot_type in bots and isinstance(bots[bot_type], dict):
                                bots[bot_type]['enabled'] = False
                        
                        if 'bots' in config:
                            config['bots'] = bots
                        save_bots_config(config)
                        
                        st.success("✅ UnicoBot ATIVADO em MODO SOLO! Os 4 bots foram pausados.")
                    
                    elif "HÍBRIDO" in mode_choice:
                        unico_config['operation_mode'] = 'HYBRID'
                        st.success("✅ UnicoBot ATIVADO em MODO HÍBRIDO!")
                    
                    elif "FOMINHA" in mode_choice:
                        unico_config['operation_mode'] = 'FOMINHA'
                        st.success("✅ UnicoBot ATIVADO em MODO FOMINHA! 🤑")
                        st.warning("⚡ Modo agressivo: IA monitora mercado a cada 30s!")
                    
                    elif "EQUIPE" in mode_choice:
                        unico_config['operation_mode'] = 'EQUIPE'
                        st.success("✅ UnicoBot ATIVADO em MODO EQUIPE! 🤝")
                        st.info("💡 IA coordenará todos os 5 bots automaticamente.")
                    
                    save_unico_bot_config(unico_config)
                    force_reload('config')
                    force_reload('unico')
                    st.balloons()
                    st.rerun()
    
    st.markdown("---")
    
    # ===== SEÇÃO: BOTS ESPECIALIZADOS =====
    st.header("🤖 Bots Especializados")
    
    bot_info = {
        'bot_estavel': {'name': '🔵 Bot Estável', 'desc': 'BTC, ETH, BNB - Baixa volatilidade', 'color': '#1e3a5f'},
        'bot_medio': {'name': '🟢 Bot Médio', 'desc': 'SOL, ADA, DOT - Volatilidade moderada', 'color': '#1e5f3a'},
        'bot_volatil': {'name': '🟡 Bot Volátil', 'desc': 'DOGE, XRP - Alta volatilidade', 'color': '#5f5f1e'},
        'bot_meme': {'name': '🔴 Bot Meme', 'desc': 'SHIB, PEPE - Máxima volatilidade', 'color': '#5f1e1e'},
        'bot_unico': {'name': '⚡ Bot Unico', 'desc': 'Controle unificado', 'color': '#4a1e5f'}
    }
    
    history = get_history()
    pnl_by_bot = get_pnl_by_bot(history)
    daily_pnl = get_daily_pnl(history)
    
    col1, col2 = st.columns(2)
    
    bots = config.get('bots', config)
    bot_types = ['bot_estavel', 'bot_medio', 'bot_volatil', 'bot_meme', 'bot_unico']
    
    for i, bot_type in enumerate(bot_types):
        if bot_type not in bots:
            continue
            
        bot_config = bots[bot_type] if isinstance(bots[bot_type], dict) else {}
        info = bot_info.get(bot_type, {'name': bot_type, 'desc': '', 'color': '#333'})
        is_enabled = bot_config.get('enabled', False)
        stats = pnl_by_bot.get(bot_type, {})
        
        with col1 if i % 2 == 0 else col2:
            status_icon = "🟢" if is_enabled else "🔴"
            status_text = "ATIVO" if is_enabled else "PAUSADO"
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {info['color']}, {info['color']}dd); 
                        padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
                <h3>{info['name']} {status_icon}</h3>
                <p style="color: #aaa; margin: 0.5rem 0;">{info['desc']}</p>
                <p><strong>Status:</strong> {status_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
            mcol1, mcol2, mcol3 = st.columns(3)
            with mcol1:
                win_rate = 0
                if stats.get('trades', 0) > 0:
                    win_rate = (stats.get('wins', 0) / stats['trades']) * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with mcol2:
                st.metric("Trades", stats.get('trades', 0))
            with mcol3:
                pnl_today = daily_pnl.get(bot_type, 0)
                st.metric("PnL Hoje", f"${pnl_today:+.2f}")
            
            if is_enabled:
                if st.button(f"⏸️ Pausar {info['name']}", key=f"pause_{bot_type}", use_container_width=True):
                    bots[bot_type]['enabled'] = False
                    if 'bots' in config:
                        config['bots'] = bots
                    save_bots_config(config)
                    force_reload('config')
                    st.success(f"✅ {info['name']} pausado!")
                    st.rerun()
            else:
                if st.button(f"▶️ Ativar {info['name']}", key=f"activate_{bot_type}", type="primary", use_container_width=True):
                    bots[bot_type]['enabled'] = True
                    if 'bots' in config:
                        config['bots'] = bots
                    save_bots_config(config)
                    force_reload('config')
                    st.success(f"✅ {info['name']} ativado!")
                    st.rerun()
            
            st.markdown("---")
    
    # ===== AÇÕES RÁPIDAS =====
    st.header("🚀 Ações Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Ativar TODOS", use_container_width=True):
            for bot_type in bot_types:
                if bot_type in bots and isinstance(bots[bot_type], dict):
                    bots[bot_type]['enabled'] = True
            if 'bots' in config:
                config['bots'] = bots
            save_bots_config(config)
            force_reload('config')
            st.success("Todos os bots ativados!")
            st.rerun()
    
    with col2:
        if st.button("⏸️ Pausar TODOS", use_container_width=True):
            for bot_type in bot_types:
                if bot_type in bots and isinstance(bots[bot_type], dict):
                    bots[bot_type]['enabled'] = False
            if 'bots' in config:
                config['bots'] = bots
            save_bots_config(config)
            force_reload('config')
            st.success("Todos os bots pausados!")
            st.rerun()
    
    with col3:
        if st.button("🔄 Atualizar Página", use_container_width=True):
            force_reload('config')
            force_reload('history')
            st.rerun()
    
    # ===== GESTÃO DE POSIÇÕES =====
    st.markdown("---")
    st.header("💰 Gestão de Posições")
    
    positions_dict = get_positions()
    
    # Converter dict para lista se necessário
    if isinstance(positions_dict, dict):
        positions = [
            {**pos, 'symbol': symbol} 
            for symbol, pos in positions_dict.items() 
            if isinstance(pos, dict)
        ]
    else:
        positions = positions_dict if positions_dict else []
    
    # Contar posições por bot
    paused_bots_with_positions = {}
    active_bots = []
    
    for bot_type in bot_types:
        is_enabled = bots.get(bot_type, {}).get('enabled', True) if isinstance(bots.get(bot_type), dict) else True
        bot_positions = [p for p in positions if p.get('bot_type') == bot_type]
        
        if not is_enabled and len(bot_positions) > 0:
            paused_bots_with_positions[bot_type] = len(bot_positions)
        elif is_enabled:
            active_bots.append(bot_type)
    
    # Mostrar informações
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.info(f"🔴 **Bots Pausados com Posições:** {len(paused_bots_with_positions)}")
        if paused_bots_with_positions:
            for bot, count in paused_bots_with_positions.items():
                st.write(f"• {bot_info[bot]['name']}: {count} posições")
    
    with info_col2:
        st.success(f"🟢 **Bots Ativos:** {len(active_bots)}")
        if active_bots:
            for bot in active_bots:
                st.write(f"• {bot_info[bot]['name']}")
    
    # Botão de redistribuição
    if len(paused_bots_with_positions) > 0 and len(active_bots) > 0:
        if st.button("🔄 Redistribuir Cryptos de Bots Pausados", type="primary", use_container_width=True):
            with st.spinner("Redistribuindo posições..."):
                result = redistribute_cryptos_from_paused_bots()
                
                if result['success']:
                    st.success(result['message'])
                    
                    if result.get('redistributions'):
                        with st.expander("📊 Ver Detalhes da Redistribuição"):
                            for redistrib in result['redistributions']:
                                st.write(f"**{redistrib['symbol']}** - Posição {redistrib['side']}")
                                st.write(f"  └ De: `{redistrib['from']}` → Para: `{redistrib['to']}`")
                                st.write(f"  └ Quantidade: {redistrib['amount']}")
                                st.markdown("---")
                    
                    force_reload('config')
                    st.balloons()
                    st.rerun()
                else:
                    st.warning(result['message'])
    elif len(paused_bots_with_positions) == 0:
        st.info("✅ Não há bots pausados com posições abertas")
    elif len(active_bots) == 0:
        st.warning("⚠️ Nenhum bot ativo para receber as posições! Ative pelo menos um bot primeiro.")


if __name__ == "__main__":
    render()
