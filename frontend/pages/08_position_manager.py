"""
📍 Position Manager - Controle de Posições Individuais
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import json

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from frontend.utils.session_manager import get_positions, get_config, force_reload


def close_position(symbol: str, bot_type: str):
    """
    Fecha uma posição específica
    
    Args:
        symbol: Symbol da crypto (ex: BTCUSDT)
        bot_type: Tipo do bot (ex: bot_estavel)
    """
    positions_file = Path("data/multibot_positions.json")
    
    if positions_file.exists():
        with open(positions_file, 'r') as f:
            positions = json.load(f)
        
        # Remove a posição
        if symbol in positions:
            del positions[symbol]
            
            # Salva
            with open(positions_file, 'w') as f:
                json.dump(positions, f, indent=2)
            
            # Log da ação
            log_file = Path("data/position_closures.log")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} | MANUAL_CLOSE | {bot_type} | {symbol}\n")
            
            return True
    
    return False


def close_all_positions_for_bot(bot_type: str):
    """
    Fecha todas as posições de um bot específico
    
    Args:
        bot_type: Tipo do bot (ex: bot_estavel)
    """
    positions_file = Path("data/multibot_positions.json")
    
    if positions_file.exists():
        with open(positions_file, 'r') as f:
            positions = json.load(f)
        
        # Filtra posições do bot
        symbols_to_remove = [s for s, p in positions.items() if p.get('bot_type') == bot_type]
        
        # Remove
        for symbol in symbols_to_remove:
            del positions[symbol]
        
        # Salva
        with open(positions_file, 'w') as f:
            json.dump(positions, f, indent=2)
        
        # Log da ação
        log_file = Path("data/position_closures.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} | CLOSE_ALL | {bot_type} | {len(symbols_to_remove)} posições\n")
        
        return len(symbols_to_remove)
    
    return 0


def render():
    """Renderiza página de gerenciamento de posições"""
    st.markdown('<div class="main-header">📍 POSITION MANAGER - App R7</div>', unsafe_allow_html=True)
    
    positions = get_positions()
    config = get_config()
    
    if not positions:
        st.info("✅ Nenhuma posição aberta no momento")
        return
    
    st.success(f"📊 **{len(positions)} posições abertas**")
    
    st.markdown("---")
    
    # ===== CONTROLE POR BOT =====
    st.header("🤖 Controle por Bot")
    
    # Agrupa posições por bot
    positions_by_bot = {}
    for symbol, pos in positions.items():
        bot_type = pos.get('bot_type', 'unknown')
        if bot_type not in positions_by_bot:
            positions_by_bot[bot_type] = []
        positions_by_bot[bot_type].append({'symbol': symbol, **pos})
    
    bot_names = {
        'bot_estavel': '🔵 Bot Estável',
        'bot_medio': '🟢 Bot Médio',
        'bot_volatil': '🟡 Bot Volátil',
        'bot_meme': '🔴 Bot Meme',
        'bot_unico': '⚡ Bot Unico'
    }
    
    for bot_type, bot_positions in positions_by_bot.items():
        with st.expander(f"{bot_names.get(bot_type, bot_type)} - {len(bot_positions)} posições"):
            
            # Botão para fechar todas do bot
            if st.button(f"🚨 Fechar TODAS as posições do {bot_names.get(bot_type, bot_type)}", 
                        key=f"close_all_{bot_type}", 
                        type="secondary"):
                closed = close_all_positions_for_bot(bot_type)
                force_reload('positions')
                st.success(f"✅ {closed} posições fechadas!")
                st.rerun()
            
            st.markdown("---")
            
            # Lista posições
            for pos in bot_positions:
                symbol = pos['symbol']
                entry_price = pos.get('entry_price', 0)
                amount_usd = pos.get('amount_usd', 0)
                entry_time = pos.get('time', '')[:19] if pos.get('time') else 'N/A'
                
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{symbol}**")
                
                with col2:
                    st.write(f"Entrada: ${entry_price:.4f}")
                
                with col3:
                    st.write(f"Valor: ${amount_usd:.2f}")
                
                with col4:
                    st.write(f"⏰ {entry_time}")
                
                with col5:
                    if st.button("❌", key=f"close_{symbol}", help="Fechar posição"):
                        success = close_position(symbol, bot_type)
                        if success:
                            force_reload('positions')
                            st.success(f"✅ {symbol} fechado!")
                            st.rerun()
                        else:
                            st.error("❌ Erro ao fechar posição")
    
    st.markdown("---")
    
    # ===== TABELA COMPLETA =====
    st.header("📋 Todas as Posições")
    
    pos_data = []
    for symbol, pos in positions.items():
        pos_data.append({
            'Bot': bot_names.get(pos.get('bot_type', ''), pos.get('bot_type', '')),
            'Symbol': symbol,
            'Entrada': f"${pos.get('entry_price', 0):.4f}",
            'Valor': f"${pos.get('amount_usd', 0):.2f}",
            'Tempo Aberto': pos.get('time', '')[:19] if pos.get('time') else 'N/A'
        })
    
    df = pd.DataFrame(pos_data)
    st.dataframe(df, use_container_width=True, height=400)
    
    st.markdown("---")
    
    # ===== AÇÕES GLOBAIS =====
    st.header("🚨 Ações Globais")
    
    st.warning("⚠️ **CUIDADO**: Estas ações afetam TODAS as posições do sistema!")
    
    col1, col2, col3 = st.columns(3)
    
    with col2:
        if st.button("🔴 FECHAR TODAS AS POSIÇÕES", type="primary", use_container_width=True):
            # Confirmação adicional
            if st.button("⚠️ CONFIRMAR FECHAMENTO DE TODAS", key="confirm_close_all"):
                positions_file = Path("data/multibot_positions.json")
                
                # Salva backup
                backup_file = Path(f"data/backups/positions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                if positions_file.exists():
                    with open(positions_file, 'r') as f:
                        backup_data = json.load(f)
                    
                    with open(backup_file, 'w') as f:
                        json.dump(backup_data, f, indent=2)
                    
                    # Fecha todas
                    with open(positions_file, 'w') as f:
                        json.dump({}, f, indent=2)
                    
                    force_reload('positions')
                    st.success(f"✅ {len(positions)} posições fechadas! Backup salvo em {backup_file}")
                    st.rerun()


if __name__ == "__main__":
    render()
