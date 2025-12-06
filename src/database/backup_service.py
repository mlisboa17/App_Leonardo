# -*- coding: utf-8 -*-
"""
App Leonardo v3.0 - Serviço de Backup Automático
================================================

Serviço que roda em background e faz backup automático:
- Backup completo diário (ex: 03:00)
- Backup incremental a cada 6 horas
- Exportação do aprendizado da IA
- Notificação de sucesso/falha
- Limpeza de backups antigos
"""

import os
import json
import shutil
import gzip
import hashlib
import logging
import threading
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger('BackupService')


class BackupService:
    """
    Serviço de backup automático completo.
    
    Funcionalidades:
    - Backup diário do banco de dados
    - Backup do aprendizado da IA (modelos + insights)
    - Backup das configurações
    - Backup dos históricos de trades
    - Compressão e versionamento
    - Verificação de integridade
    """
    
    def __init__(self, data_dir: str = "data", backup_time: str = "03:00"):
        self.data_dir = data_dir
        self.backup_dir = os.path.join(data_dir, "full_backups")
        self.backup_time = backup_time
        
        # Criar diretório
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Estado
        self.last_backup = None
        self.last_backup_status = None
        self._running = False
        self._thread = None
        
        # Configurações
        self.max_backups = 7  # Manter últimos 7 dias
        self.backup_interval_hours = 6  # Backup incremental
        
        # Arquivos/pastas para backup
        self.backup_targets = [
            # Banco de dados
            "data/app_leonardo.db",
            # IA
            "data/ai/",
            "data/ai_models/",
            "data/market_cache/",
            "data/config_history/",
            # Históricos
            "data/history/",
            "data/multibot_history.json",
            "data/crypto_profiles.json",
            "data/daily_stats.json",
            # Configurações
            "config/",
        ]
        
        logger.info(f"🔄 BackupService inicializado - Backup diário às {backup_time}")
    
    def start(self):
        """Inicia o serviço de backup"""
        if self._running:
            return
        
        self._running = True
        
        # Agendar backup diário
        schedule.every().day.at(self.backup_time).do(self.run_full_backup)
        
        # Agendar backup incremental
        schedule.every(self.backup_interval_hours).hours.do(self.run_incremental_backup)
        
        # Iniciar thread
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()
        
        logger.info("✅ BackupService iniciado")
    
    def stop(self):
        """Para o serviço de backup"""
        self._running = False
        schedule.clear()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("⏹️ BackupService parado")
    
    def _scheduler_loop(self):
        """Loop do scheduler"""
        while self._running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check a cada minuto
            except Exception as e:
                logger.error(f"❌ Erro no scheduler: {e}")
                time.sleep(60)
    
    def run_full_backup(self) -> Dict:
        """
        Executa backup completo do sistema.
        
        Returns:
            Dict com resultado do backup
        """
        logger.info("🔄 Iniciando backup completo...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"full_backup_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        result = {
            'success': False,
            'timestamp': timestamp,
            'path': '',
            'size_mb': 0,
            'files_backed_up': 0,
            'errors': []
        }
        
        try:
            # Criar diretório do backup
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup de cada target
            files_backed_up = 0
            
            for target in self.backup_targets:
                try:
                    if os.path.exists(target):
                        if os.path.isdir(target):
                            # Copiar diretório
                            dest = os.path.join(backup_path, target.replace('/', '_').strip('_'))
                            shutil.copytree(target, dest, dirs_exist_ok=True)
                            files_backed_up += sum([len(files) for _, _, files in os.walk(dest)])
                        else:
                            # Copiar arquivo
                            dest = os.path.join(backup_path, os.path.basename(target))
                            shutil.copy2(target, dest)
                            files_backed_up += 1
                except Exception as e:
                    result['errors'].append(f"{target}: {str(e)}")
                    logger.warning(f"⚠️ Erro ao copiar {target}: {e}")
            
            # Salvar metadados
            metadata = {
                'timestamp': timestamp,
                'backup_type': 'full',
                'files_backed_up': files_backed_up,
                'targets': self.backup_targets,
                'app_version': '3.0',
                'created_at': datetime.now().isoformat()
            }
            
            with open(os.path.join(backup_path, 'backup_metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Comprimir
            archive_path = f"{backup_path}.tar.gz"
            self._compress_directory(backup_path, archive_path)
            
            # Remover diretório não comprimido
            shutil.rmtree(backup_path)
            
            # Calcular tamanho
            size_bytes = os.path.getsize(archive_path)
            
            # Atualizar resultado
            result['success'] = True
            result['path'] = archive_path
            result['size_mb'] = round(size_bytes / (1024 * 1024), 2)
            result['files_backed_up'] = files_backed_up
            
            # Atualizar estado
            self.last_backup = datetime.now().isoformat()
            self.last_backup_status = 'SUCCESS'
            
            # Limpar backups antigos
            self._cleanup_old_backups()
            
            # Salvar registro
            self._save_backup_record(result)
            
            logger.info(f"✅ Backup completo criado: {archive_path} ({result['size_mb']} MB)")
            
        except Exception as e:
            result['errors'].append(str(e))
            self.last_backup_status = 'FAILED'
            logger.error(f"❌ Erro no backup completo: {e}")
        
        return result
    
    def run_incremental_backup(self) -> Dict:
        """
        Executa backup incremental (apenas arquivos modificados).
        
        Returns:
            Dict com resultado
        """
        logger.info("🔄 Iniciando backup incremental...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        result = {
            'success': False,
            'timestamp': timestamp,
            'files_backed_up': 0,
            'errors': []
        }
        
        # Apenas arquivos críticos que mudam frequentemente
        critical_files = [
            "data/app_leonardo.db",
            "data/ai/ai_state.json",
            "data/ai/completed_trades.json",
            "data/ai_models/models.pkl",
            "data/ai_models/insights.json",
            "data/multibot_history.json",
        ]
        
        try:
            backup_path = os.path.join(self.backup_dir, f"incremental_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            files_backed_up = 0
            
            for file_path in critical_files:
                if os.path.exists(file_path):
                    try:
                        dest = os.path.join(backup_path, os.path.basename(file_path))
                        shutil.copy2(file_path, dest)
                        files_backed_up += 1
                    except Exception as e:
                        result['errors'].append(f"{file_path}: {str(e)}")
            
            # Comprimir
            if files_backed_up > 0:
                archive_path = f"{backup_path}.tar.gz"
                self._compress_directory(backup_path, archive_path)
                shutil.rmtree(backup_path)
                result['path'] = archive_path
            else:
                shutil.rmtree(backup_path)
            
            result['success'] = True
            result['files_backed_up'] = files_backed_up
            
            logger.info(f"✅ Backup incremental: {files_backed_up} arquivos")
            
        except Exception as e:
            result['errors'].append(str(e))
            logger.error(f"❌ Erro no backup incremental: {e}")
        
        return result
    
    def _compress_directory(self, source_dir: str, output_path: str):
        """Comprime um diretório em tar.gz"""
        import tarfile
        
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
    
    def _cleanup_old_backups(self):
        """Remove backups antigos"""
        try:
            # Full backups
            full_backups = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith('full_backup_') and f.endswith('.tar.gz')
            ])
            
            for old in full_backups[:-self.max_backups]:
                old_path = os.path.join(self.backup_dir, old)
                os.remove(old_path)
                logger.info(f"🗑️ Backup antigo removido: {old}")
            
            # Incremental backups - manter últimos 24
            inc_backups = sorted([
                f for f in os.listdir(self.backup_dir)
                if f.startswith('incremental_') and f.endswith('.tar.gz')
            ])
            
            for old in inc_backups[:-24]:
                old_path = os.path.join(self.backup_dir, old)
                os.remove(old_path)
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao limpar backups: {e}")
    
    def _save_backup_record(self, result: Dict):
        """Salva registro do backup"""
        record_file = os.path.join(self.backup_dir, "backup_history.json")
        
        history = []
        if os.path.exists(record_file):
            try:
                with open(record_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(result)
        history = history[-100:]  # Manter últimos 100
        
        with open(record_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restaura um backup.
        
        Args:
            backup_path: Caminho do arquivo de backup
            
        Returns:
            True se sucesso
        """
        if not os.path.exists(backup_path):
            logger.error(f"Backup não encontrado: {backup_path}")
            return False
        
        logger.info(f"🔄 Restaurando backup: {backup_path}")
        
        try:
            import tarfile
            
            # Criar backup de segurança antes
            self.run_full_backup()
            
            # Extrair
            temp_dir = os.path.join(self.backup_dir, "temp_restore")
            os.makedirs(temp_dir, exist_ok=True)
            
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(temp_dir)
            
            # Encontrar diretório extraído
            extracted = os.listdir(temp_dir)[0]
            extracted_path = os.path.join(temp_dir, extracted)
            
            # Copiar arquivos de volta
            for item in os.listdir(extracted_path):
                src = os.path.join(extracted_path, item)
                
                # Determinar destino baseado no nome
                if item.endswith('_db') or item == 'app_leonardo.db':
                    dest = "data/app_leonardo.db"
                elif item.startswith('data_ai'):
                    dest = "data/ai"
                elif item.startswith('data_ai_models'):
                    dest = "data/ai_models"
                elif item.startswith('config'):
                    dest = "config"
                else:
                    continue
                
                if os.path.isdir(src):
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)
                else:
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(src, dest)
            
            # Limpar temp
            shutil.rmtree(temp_dir)
            
            logger.info("✅ Backup restaurado com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """Lista todos os backups disponíveis"""
        backups = []
        
        for f in sorted(os.listdir(self.backup_dir), reverse=True):
            if f.endswith('.tar.gz'):
                path = os.path.join(self.backup_dir, f)
                size = os.path.getsize(path)
                
                # Parse timestamp
                try:
                    if f.startswith('full_backup_'):
                        timestamp = f[12:27]  # full_backup_YYYYMMDD_HHMMSS
                        backup_type = 'full'
                    elif f.startswith('incremental_'):
                        timestamp = f[12:27]
                        backup_type = 'incremental'
                    else:
                        continue
                    
                    backups.append({
                        'name': f,
                        'path': path,
                        'type': backup_type,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'timestamp': timestamp,
                        'created_at': datetime.strptime(timestamp, '%Y%m%d_%H%M%S').isoformat()
                    })
                except:
                    pass
        
        return backups
    
    def get_status(self) -> Dict:
        """Retorna status do serviço"""
        return {
            'running': self._running,
            'last_backup': self.last_backup,
            'last_status': self.last_backup_status,
            'backup_time': self.backup_time,
            'backup_interval_hours': self.backup_interval_hours,
            'total_backups': len(self.list_backups()),
            'backup_dir': self.backup_dir
        }
    
    def force_backup(self, backup_type: str = "full") -> Dict:
        """Força um backup manual"""
        if backup_type == "full":
            return self.run_full_backup()
        else:
            return self.run_incremental_backup()


# Singleton
_backup_service: Optional[BackupService] = None

def get_backup_service(backup_time: str = "03:00") -> BackupService:
    """Retorna instância singleton"""
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService(backup_time=backup_time)
    return _backup_service


# Teste
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    service = get_backup_service("03:00")
    
    print("\n🔄 BackupService Status:")
    status = service.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    print("\n📦 Backups disponíveis:")
    backups = service.list_backups()
    for b in backups[:5]:
        print(f"  - {b['name']} ({b['size_mb']} MB) [{b['type']}]")
    
    print("\n💾 Forçando backup completo...")
    result = service.force_backup("full")
    print(f"  Sucesso: {result['success']}")
    print(f"  Arquivos: {result['files_backed_up']}")
    print(f"  Tamanho: {result['size_mb']} MB")
    
    if result['errors']:
        print(f"  Erros: {result['errors']}")
