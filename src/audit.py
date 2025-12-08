"""
MÓDULO DE AUDITORIA - Registro detalhado de todas as ações do sistema
Todos os eventos críticos são registrados para rastreabilidade e debugging
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
import threading


@dataclass
class AuditEvent:
    """Representa um evento de auditoria"""
    timestamp: str
    event_type: str  # 'config_change', 'restart', 'stop', 'trade', 'error', etc
    severity: str  # 'info', 'warning', 'critical'
    source: str  # 'api', 'watcher', 'bot', 'coordinator', 'user'
    target: str  # bot_type, symbol, ou 'system'
    action: str  # ação específica
    details: Dict[str, Any]  # contexto adicional
    user_id: Optional[str] = None  # ID do usuário se aplicável
    
    def to_dict(self):
        return asdict(self)


class AuditLogger:
    """Logger de auditoria com persistência e análise"""
    
    def __init__(self, audit_dir: str = "data/audit"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger('Audit')
        self.logger.setLevel(logging.DEBUG)
        
        # Handler de arquivo (JSON) para auditoria
        self.audit_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.file_handler = logging.FileHandler(self.audit_file)
        self.file_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(self.file_handler)
        
        # Handler de console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - [%(levelname)s] %(message)s'
        ))
        self.logger.addHandler(console_handler)
        
        # Lock para thread-safety
        self.lock = threading.RLock()
        
        # Cache de eventos recentes (últimos 1000)
        self.recent_events = []
        self.max_recent = 1000
    
    def log_event(self, event: AuditEvent):
        """Registra um evento de auditoria"""
        with self.lock:
            # Salva em arquivo JSONL
            self.logger.info(json.dumps(event.to_dict(), ensure_ascii=False))
            
            # Mantém em cache
            self.recent_events.append(event)
            if len(self.recent_events) > self.max_recent:
                self.recent_events.pop(0)
    
    def log_config_change(self, bot_type: str, old_config: Dict, new_config: Dict, 
                         source: str = 'api', user_id: Optional[str] = None):
        """Registra mudança de configuração"""
        # Identifica quais campos mudaram
        changed_fields = {}
        for key in new_config:
            if key not in old_config or old_config[key] != new_config[key]:
                changed_fields[key] = {
                    'old': old_config.get(key),
                    'new': new_config[key]
                }
        
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type='config_change',
            severity='critical',
            source=source,
            target=bot_type,
            action='config_updated',
            details={
                'changed_fields': changed_fields,
                'num_changes': len(changed_fields)
            },
            user_id=user_id
        )
        self.log_event(event)
    
    def log_restart(self, bot_type: Optional[str], reason: str, source: str = 'watcher',
                   user_id: Optional[str] = None):
        """Registra reinício de bot"""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type='restart',
            severity='warning',
            source=source,
            target=bot_type or 'all_bots',
            action='restart_initiated',
            details={'reason': reason},
            user_id=user_id
        )
        self.log_event(event)
    
    def log_stop(self, bot_type: Optional[str], reason: str, source: str = 'watcher',
                user_id: Optional[str] = None):
        """Registra parada de bot"""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type='stop',
            severity='warning',
            source=source,
            target=bot_type or 'all_bots',
            action='stop_initiated',
            details={'reason': reason},
            user_id=user_id
        )
        self.log_event(event)
    
    def log_trade(self, symbol: str, bot_type: str, action: str, price: float, 
                 quantity: float, pnl: Optional[float] = None, details: Optional[Dict] = None):
        """Registra execução de trade"""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type='trade',
            severity='info',
            source='bot',
            target=symbol,
            action=action,  # 'buy', 'sell', 'close'
            details={
                'bot_type': bot_type,
                'price': price,
                'quantity': quantity,
                'pnl': pnl,
                **(details or {})
            }
        )
        self.log_event(event)
    
    def log_error(self, error_type: str, bot_type: Optional[str], message: str, 
                 traceback: Optional[str] = None, source: str = 'bot'):
        """Registra erro no sistema"""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type='error',
            severity='critical',
            source=source,
            target=bot_type or 'system',
            action=error_type,
            details={
                'message': message,
                'traceback': traceback
            }
        )
        self.log_event(event)
    
    def log_position_change(self, bot_type: str, symbol: str, action: str, 
                           position_size: float, entry_price: float, details: Optional[Dict] = None):
        """Registra mudança de posição aberta"""
        event = AuditEvent(
            timestamp=datetime.now().isoformat(),
            event_type='position_change',
            severity='info',
            source='bot',
            target=symbol,
            action=action,  # 'open', 'close', 'adjust'
            details={
                'bot_type': bot_type,
                'position_size': position_size,
                'entry_price': entry_price,
                **(details or {})
            }
        )
        self.log_event(event)
    
    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None,
                         source: Optional[str] = None, severity: Optional[str] = None) -> list:
        """Retorna eventos recentes com filtros opcionais"""
        with self.lock:
            events = list(reversed(self.recent_events))[:limit]
            
            # Aplicar filtros
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            if source:
                events = [e for e in events if e.source == source]
            if severity:
                events = [e for e in events if e.severity == severity]
            
            return [e.to_dict() for e in events]
    
    def export_events(self, output_file: str, event_type: Optional[str] = None, 
                     days: int = 7):
        """Exporta eventos para arquivo JSON"""
        with self.lock:
            events = [e.to_dict() for e in self.recent_events]
            
            if event_type:
                events = [e for e in events if e['event_type'] == event_type]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=2, ensure_ascii=False, default=str)
            
            return len(events)


# Instância global de auditoria
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Retorna instância global do logger de auditoria"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
