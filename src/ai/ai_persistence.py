# -*- coding: utf-8 -*-
"""
R7_V1 - Persistência da IA
======================================

Módulo responsável por garantir que a IA não perca o que aprendeu.
Inclui:
- Backup automático dos modelos
- Exportação/importação de aprendizado
- Criptografia de dados sensíveis (opcional)
- Versionamento de modelos
"""

import os
import json
import pickle
import shutil
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Criptografia opcional
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger('AIPersistence')


class AIPersistence:
    """
    Gerenciador de persistência da IA.
    
    Garante que todos os dados aprendidos são salvos e podem ser recuperados.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ai_dir = os.path.join(data_dir, "ai")
        self.models_dir = os.path.join(data_dir, "ai_models")
        self.backup_dir = os.path.join(data_dir, "ai_backups")
        
        # Criar diretórios
        for d in [self.ai_dir, self.models_dir, self.backup_dir]:
            os.makedirs(d, exist_ok=True)
        
        # Chave de criptografia (opcional)
        self.crypto_key = None
        self._load_or_create_key()
        
        # Metadados
        self.metadata_file = os.path.join(self.ai_dir, "metadata.json")
        self.metadata = self._load_metadata()
    
    def _load_or_create_key(self):
        """Carrega ou cria chave de criptografia"""
        if not CRYPTO_AVAILABLE:
            return
        
        key_file = os.path.join(self.ai_dir, ".ai_key")
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.crypto_key = f.read()
        else:
            self.crypto_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.crypto_key)
    
    def _load_metadata(self) -> Dict:
        """Carrega metadados da IA"""
        default = {
            'version': '3.0',
            'created_at': datetime.now().isoformat(),
            'last_backup': None,
            'total_trainings': 0,
            'total_trades_learned': 0,
            'model_versions': {}
        }
        
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return {**default, **json.load(f)}
            except:
                pass
        return default
    
    def _save_metadata(self):
        """Salva metadados"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar metadados: {e}")
    
    def create_backup(self, reason: str = "manual") -> str:
        """
        Cria backup completo de todos os dados da IA.
        
        Args:
            reason: Razão do backup (manual, scheduled, before_update)
            
        Returns:
            Caminho do backup criado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"ai_backup_{timestamp}_{reason}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            # Copiar modelos
            models_file = os.path.join(self.models_dir, "models.pkl")
            if os.path.exists(models_file):
                shutil.copy(models_file, os.path.join(backup_path, "models.pkl"))
            
            # Copiar insights
            insights_file = os.path.join(self.models_dir, "insights.json")
            if os.path.exists(insights_file):
                shutil.copy(insights_file, os.path.join(backup_path, "insights.json"))
            
            # Copiar estado
            state_file = os.path.join(self.ai_dir, "ai_state.json")
            if os.path.exists(state_file):
                shutil.copy(state_file, os.path.join(backup_path, "ai_state.json"))
            
            # Copiar trades aprendidos
            trades_file = os.path.join(self.ai_dir, "completed_trades.json")
            if os.path.exists(trades_file):
                shutil.copy(trades_file, os.path.join(backup_path, "completed_trades.json"))
            
            # Copiar histórico de config
            config_history = os.path.join(self.data_dir, "config_history", "changes_history.json")
            if os.path.exists(config_history):
                shutil.copy(config_history, os.path.join(backup_path, "changes_history.json"))
            
            # Salvar info do backup
            backup_info = {
                'timestamp': timestamp,
                'reason': reason,
                'files': os.listdir(backup_path),
                'metadata': self.metadata
            }
            with open(os.path.join(backup_path, "backup_info.json"), 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            # Atualizar metadados
            self.metadata['last_backup'] = datetime.now().isoformat()
            self._save_metadata()
            
            logger.info(f"✅ Backup criado: {backup_path}")
            
            # Limpar backups antigos (manter últimos 10)
            self._cleanup_old_backups(keep=10)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return ""
    
    def _cleanup_old_backups(self, keep: int = 10):
        """Remove backups antigos"""
        try:
            backups = sorted([
                d for d in os.listdir(self.backup_dir)
                if d.startswith('ai_backup_')
            ])
            
            for old in backups[:-keep]:
                old_path = os.path.join(self.backup_dir, old)
                shutil.rmtree(old_path)
                logger.info(f"🗑️ Backup antigo removido: {old}")
        except Exception as e:
            logger.warning(f"Erro ao limpar backups: {e}")
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restaura um backup.
        
        Args:
            backup_name: Nome do backup a restaurar
            
        Returns:
            True se sucesso
        """
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup não encontrado: {backup_name}")
            return False
        
        try:
            # Criar backup do estado atual antes de restaurar
            self.create_backup(reason="before_restore")
            
            # Restaurar arquivos
            for filename in os.listdir(backup_path):
                if filename == "backup_info.json":
                    continue
                
                src = os.path.join(backup_path, filename)
                
                if filename in ["models.pkl", "insights.json"]:
                    dst = os.path.join(self.models_dir, filename)
                elif filename in ["ai_state.json", "completed_trades.json"]:
                    dst = os.path.join(self.ai_dir, filename)
                elif filename == "changes_history.json":
                    dst = os.path.join(self.data_dir, "config_history", filename)
                else:
                    continue
                
                shutil.copy(src, dst)
            
            logger.info(f"✅ Backup restaurado: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar backup: {e}")
            return False
    
    def list_backups(self) -> list:
        """Lista todos os backups disponíveis"""
        backups = []
        
        for name in sorted(os.listdir(self.backup_dir), reverse=True):
            if name.startswith('ai_backup_'):
                info_file = os.path.join(self.backup_dir, name, "backup_info.json")
                info = {'name': name}
                
                if os.path.exists(info_file):
                    try:
                        with open(info_file, 'r', encoding='utf-8') as f:
                            info.update(json.load(f))
                    except:
                        pass
                
                backups.append(info)
        
        return backups
    
    def export_learning(self, export_path: str = None) -> str:
        """
        Exporta todo o aprendizado para um arquivo único.
        Útil para transferir para outra máquina.
        
        Args:
            export_path: Caminho de exportação (opcional)
            
        Returns:
            Caminho do arquivo exportado
        """
        if export_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_path = os.path.join(self.data_dir, f"ai_export_{timestamp}.pkl")
        
        export_data = {
            'version': '3.0',
            'exported_at': datetime.now().isoformat(),
            'models': None,
            'scalers': None,
            'insights': None,
            'learning_history': None,
            'completed_trades': None,
            'config_changes': None
        }
        
        # Carregar modelos
        models_file = os.path.join(self.models_dir, "models.pkl")
        if os.path.exists(models_file):
            with open(models_file, 'rb') as f:
                data = pickle.load(f)
                export_data['models'] = data.get('models')
                export_data['scalers'] = data.get('scalers')
                export_data['learning_history'] = data.get('history')
        
        # Carregar insights
        insights_file = os.path.join(self.models_dir, "insights.json")
        if os.path.exists(insights_file):
            with open(insights_file, 'r', encoding='utf-8') as f:
                export_data['insights'] = json.load(f)
        
        # Carregar trades
        trades_file = os.path.join(self.ai_dir, "completed_trades.json")
        if os.path.exists(trades_file):
            with open(trades_file, 'r', encoding='utf-8') as f:
                export_data['completed_trades'] = json.load(f)
        
        # Carregar histórico de config
        config_file = os.path.join(self.data_dir, "config_history", "changes_history.json")
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                export_data['config_changes'] = json.load(f)
        
        # Salvar
        with open(export_path, 'wb') as f:
            pickle.dump(export_data, f)
        
        logger.info(f"✅ Aprendizado exportado: {export_path}")
        return export_path
    
    def import_learning(self, import_path: str) -> bool:
        """
        Importa aprendizado de um arquivo exportado.
        
        Args:
            import_path: Caminho do arquivo
            
        Returns:
            True se sucesso
        """
        if not os.path.exists(import_path):
            logger.error(f"Arquivo não encontrado: {import_path}")
            return False
        
        try:
            # Backup antes de importar
            self.create_backup(reason="before_import")
            
            with open(import_path, 'rb') as f:
                data = pickle.load(f)
            
            # Restaurar modelos
            if data.get('models') or data.get('scalers'):
                models_file = os.path.join(self.models_dir, "models.pkl")
                with open(models_file, 'wb') as f:
                    pickle.dump({
                        'models': data.get('models', {}),
                        'scalers': data.get('scalers', {}),
                        'history': data.get('learning_history', {})
                    }, f)
            
            # Restaurar insights
            if data.get('insights'):
                insights_file = os.path.join(self.models_dir, "insights.json")
                with open(insights_file, 'w') as f:
                    json.dump(data['insights'], f, indent=2)
            
            # Restaurar trades (merge com existentes)
            if data.get('completed_trades'):
                trades_file = os.path.join(self.ai_dir, "completed_trades.json")
                existing = []
                if os.path.exists(trades_file):
                    with open(trades_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                
                # Merge
                all_trades = existing + data['completed_trades']
                # Remover duplicados por timestamp
                seen = set()
                unique = []
                for t in all_trades:
                    key = f"{t.get('symbol')}_{t.get('exit_time', t.get('timestamp', ''))}"
                    if key not in seen:
                        seen.add(key)
                        unique.append(t)
                
                with open(trades_file, 'w') as f:
                    json.dump(unique[-1000:], f, indent=2)  # Manter últimos 1000
            
            logger.info(f"✅ Aprendizado importado de: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao importar: {e}")
            return False
    
    def get_learning_stats(self) -> Dict:
        """
        Retorna estatísticas do aprendizado.
        
        Returns:
            Dict com estatísticas
        """
        stats = {
            'total_trades_learned': 0,
            'total_trainings': self.metadata.get('total_trainings', 0),
            'models_trained': [],
            'last_backup': self.metadata.get('last_backup'),
            'insights_count': 0,
            'data_size_mb': 0
        }
        
        # Contar trades
        trades_file = os.path.join(self.ai_dir, "completed_trades.json")
        if os.path.exists(trades_file):
            try:
                with open(trades_file, 'r', encoding='utf-8') as f:
                    trades = json.load(f)
                    stats['total_trades_learned'] = len(trades)
            except:
                pass
        
        # Modelos treinados
        models_file = os.path.join(self.models_dir, "models.pkl")
        if os.path.exists(models_file):
            try:
                with open(models_file, 'rb') as f:
                    data = pickle.load(f)
                    stats['models_trained'] = list(data.get('models', {}).keys())
            except:
                pass
        
        # Insights
        insights_file = os.path.join(self.models_dir, "insights.json")
        if os.path.exists(insights_file):
            try:
                with open(insights_file, 'r', encoding='utf-8') as f:
                    insights = json.load(f)
                    stats['insights_count'] = sum([
                        len(insights.get('best_rsi_range', {})),
                        len(insights.get('best_hours', {})),
                        len(insights.get('dangerous_patterns', [])),
                        len(insights.get('crypto_performance', {}))
                    ])
            except:
                pass
        
        # Tamanho total
        total_size = 0
        for root, dirs, files in os.walk(self.ai_dir):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
        for root, dirs, files in os.walk(self.models_dir):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
        
        stats['data_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        return stats
    
    def verify_integrity(self) -> Dict:
        """
        Verifica integridade dos arquivos da IA.
        
        Returns:
            Dict com status de cada componente
        """
        status = {
            'models': {'exists': False, 'valid': False},
            'insights': {'exists': False, 'valid': False},
            'state': {'exists': False, 'valid': False},
            'trades': {'exists': False, 'valid': False}
        }
        
        # Modelos
        models_file = os.path.join(self.models_dir, "models.pkl")
        if os.path.exists(models_file):
            status['models']['exists'] = True
            try:
                with open(models_file, 'rb') as f:
                    pickle.load(f)
                status['models']['valid'] = True
            except:
                pass
        
        # Insights
        insights_file = os.path.join(self.models_dir, "insights.json")
        if os.path.exists(insights_file):
            status['insights']['exists'] = True
            try:
                with open(insights_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                status['insights']['valid'] = True
            except:
                pass
        
        # State
        state_file = os.path.join(self.ai_dir, "ai_state.json")
        if os.path.exists(state_file):
            status['state']['exists'] = True
            try:
                with open(state_file, 'r') as f:
                    json.load(f)
                status['state']['valid'] = True
            except:
                pass
        
        # Trades
        trades_file = os.path.join(self.ai_dir, "completed_trades.json")
        if os.path.exists(trades_file):
            status['trades']['exists'] = True
            try:
                with open(trades_file, 'r') as f:
                    json.load(f)
                status['trades']['valid'] = True
            except:
                pass
        
        return status


# Singleton
_persistence: Optional[AIPersistence] = None

def get_ai_persistence() -> AIPersistence:
    """Retorna instância singleton"""
    global _persistence
    if _persistence is None:
        _persistence = AIPersistence()
    return _persistence


# Teste
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    p = get_ai_persistence()
    
    print("\n📊 Estatísticas de Aprendizado:")
    stats = p.get_learning_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    
    print("\n🔍 Verificando integridade:")
    integrity = p.verify_integrity()
    for component, status in integrity.items():
        emoji = "✅" if status['valid'] else "⚠️" if status['exists'] else "❌"
        print(f"  {emoji} {component}: exists={status['exists']}, valid={status['valid']}")
    
    print("\n📦 Backups disponíveis:")
    backups = p.list_backups()
    for b in backups[:5]:
        print(f"  - {b.get('name')} ({b.get('reason', 'unknown')})")
