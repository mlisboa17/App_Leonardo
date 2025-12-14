"""
OBSERVABILIDADE - Métricas, logging e monitoramento do sistema
"""
import logging
import time
from functools import wraps
from datetime import datetime
from typing import Callable, Any, Dict, Optional
from pathlib import Path
import json


class MetricsCollector:
    """Coleta métricas de performance do sistema"""
    
    def __init__(self):
        self.metrics = {
            'restarts': {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'by_bot': {},
                'duration_ms': []
            },
            'stops': {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'by_bot': {},
            },
            'api_requests': {
                'total': 0,
                'by_endpoint': {},
                'response_time_ms': []
            },
            'trades': {
                'total': 0,
                'wins': 0,
                'losses': 0,
                'by_bot': {}
            },
            'errors': {
                'total': 0,
                'by_type': {},
                'by_source': {}
            }
        }
        self.logger = logging.getLogger('Metrics')
    
    def record_restart(self, bot_type: str, success: bool, duration_ms: float):
        """Registra métrica de restart"""
        self.metrics['restarts']['total'] += 1
        if success:
            self.metrics['restarts']['successful'] += 1
        else:
            self.metrics['restarts']['failed'] += 1
        
        if bot_type not in self.metrics['restarts']['by_bot']:
            self.metrics['restarts']['by_bot'][bot_type] = {'total': 0, 'success': 0, 'fail': 0}
        
        self.metrics['restarts']['by_bot'][bot_type]['total'] += 1
        if success:
            self.metrics['restarts']['by_bot'][bot_type]['success'] += 1
        else:
            self.metrics['restarts']['by_bot'][bot_type]['fail'] += 1
        
        self.metrics['restarts']['duration_ms'].append(duration_ms)
        
        self.logger.debug(f"Restart metrics recorded: {bot_type} - {duration_ms:.0f}ms - {'OK' if success else 'FAILED'}")
    
    def record_stop(self, bot_type: str, success: bool):
        """Registra métrica de stop"""
        self.metrics['stops']['total'] += 1
        if success:
            self.metrics['stops']['successful'] += 1
        else:
            self.metrics['stops']['failed'] += 1
        
        if bot_type not in self.metrics['stops']['by_bot']:
            self.metrics['stops']['by_bot'][bot_type] = {'total': 0, 'success': 0, 'fail': 0}
        
        self.metrics['stops']['by_bot'][bot_type]['total'] += 1
        if success:
            self.metrics['stops']['by_bot'][bot_type]['success'] += 1
        else:
            self.metrics['stops']['by_bot'][bot_type]['fail'] += 1
    
    def record_api_request(self, endpoint: str, response_time_ms: float, status_code: int):
        """Registra métrica de requisição API"""
        self.metrics['api_requests']['total'] += 1
        
        if endpoint not in self.metrics['api_requests']['by_endpoint']:
            self.metrics['api_requests']['by_endpoint'][endpoint] = {
                'count': 0,
                'avg_time_ms': 0,
                'errors': 0
            }
        
        endpoint_metrics = self.metrics['api_requests']['by_endpoint'][endpoint]
        endpoint_metrics['count'] += 1
        endpoint_metrics['avg_time_ms'] = (
            (endpoint_metrics['avg_time_ms'] * (endpoint_metrics['count'] - 1) + response_time_ms) /
            endpoint_metrics['count']
        )
        
        if status_code >= 400:
            endpoint_metrics['errors'] += 1
        
        self.metrics['api_requests']['response_time_ms'].append(response_time_ms)
    
    def record_trade(self, bot_type: str, win: bool):
        """Registra métrica de trade"""
        self.metrics['trades']['total'] += 1
        if win:
            self.metrics['trades']['wins'] += 1
        else:
            self.metrics['trades']['losses'] += 1
        
        if bot_type not in self.metrics['trades']['by_bot']:
            self.metrics['trades']['by_bot'][bot_type] = {'total': 0, 'wins': 0, 'losses': 0}
        
        self.metrics['trades']['by_bot'][bot_type]['total'] += 1
        if win:
            self.metrics['trades']['by_bot'][bot_type]['wins'] += 1
        else:
            self.metrics['trades']['by_bot'][bot_type]['losses'] += 1
    
    def record_error(self, error_type: str, source: str):
        """Registra métrica de erro"""
        self.metrics['errors']['total'] += 1
        self.metrics['errors']['by_type'][error_type] = self.metrics['errors']['by_type'].get(error_type, 0) + 1
        self.metrics['errors']['by_source'][source] = self.metrics['errors']['by_source'].get(source, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna sumário das métricas"""
        return {
            'timestamp': datetime.now().isoformat(),
            'restarts': {
                'total': self.metrics['restarts']['total'],
                'successful': self.metrics['restarts']['successful'],
                'failed': self.metrics['restarts']['failed'],
                'success_rate': (
                    self.metrics['restarts']['successful'] / self.metrics['restarts']['total'] * 100
                    if self.metrics['restarts']['total'] > 0 else 0
                ),
                'avg_duration_ms': (
                    sum(self.metrics['restarts']['duration_ms']) / len(self.metrics['restarts']['duration_ms'])
                    if self.metrics['restarts']['duration_ms'] else 0
                ),
                'by_bot': self.metrics['restarts']['by_bot']
            },
            'stops': {
                'total': self.metrics['stops']['total'],
                'successful': self.metrics['stops']['successful'],
                'failed': self.metrics['stops']['failed'],
                'success_rate': (
                    self.metrics['stops']['successful'] / self.metrics['stops']['total'] * 100
                    if self.metrics['stops']['total'] > 0 else 0
                ),
                'by_bot': self.metrics['stops']['by_bot']
            },
            'api_requests': {
                'total': self.metrics['api_requests']['total'],
                'avg_response_time_ms': (
                    sum(self.metrics['api_requests']['response_time_ms']) / len(self.metrics['api_requests']['response_time_ms'])
                    if self.metrics['api_requests']['response_time_ms'] else 0
                ),
                'by_endpoint': self.metrics['api_requests']['by_endpoint']
            },
            'trades': {
                'total': self.metrics['trades']['total'],
                'wins': self.metrics['trades']['wins'],
                'losses': self.metrics['trades']['losses'],
                'win_rate': (
                    self.metrics['trades']['wins'] / self.metrics['trades']['total'] * 100
                    if self.metrics['trades']['total'] > 0 else 0
                ),
                'by_bot': self.metrics['trades']['by_bot']
            },
            'errors': {
                'total': self.metrics['errors']['total'],
                'by_type': self.metrics['errors']['by_type'],
                'by_source': self.metrics['errors']['by_source']
            }
        }
    
    def save_metrics(self, output_file: str):
        """Salva métricas em arquivo JSON"""
        metrics_data = self.get_summary()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, default=str)
        
        self.logger.info(f"Métricas salvas em {output_file}")


# Decorator para medir tempo de execução
def measure_execution_time(metrics: Optional[MetricsCollector] = None):
    """Decorator que mede tempo de execução de uma função"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                
                if metrics:
                    # Registra no metrics se disponível
                    pass
                
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                if metrics:
                    metrics.record_error(type(e).__name__, func.__module__)
                raise
        
        return wrapper
    return decorator


# Decorator para logging de função
def log_function_call(logger: logging.Logger, level: int = logging.DEBUG):
    """Decorator que registra chamadas de função"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger.log(level, f"[CALL] {func.__module__}.{func.__name__} - args: {len(args)}, kwargs: {list(kwargs.keys())}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"[RETURN] {func.__module__}.{func.__name__} - OK")
                return result
            except Exception as e:
                logger.log(level, f"[ERROR] {func.__module__}.{func.__name__} - {type(e).__name__}: {str(e)}")
                raise
        
        return wrapper
    return decorator


# Configuração de logging estruturado
class StructuredLogger:
    """Logger com suporte a logging estruturado"""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler com JSON
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log com contexto"""
        context = f" | {json.dumps(kwargs)}" if kwargs else ""
        self.logger.info(f"{message}{context}")
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log de erro com stack trace"""
        context = f" | {json.dumps(kwargs)}" if kwargs else ""
        if exception:
            self.logger.error(f"{message}{context}", exc_info=True)
        else:
            self.logger.error(f"{message}{context}")
    
    def warning(self, message: str, **kwargs):
        """Log de aviso"""
        context = f" | {json.dumps(kwargs)}" if kwargs else ""
        self.logger.warning(f"{message}{context}")
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        context = f" | {json.dumps(kwargs)}" if kwargs else ""
        self.logger.debug(f"{message}{context}")


# Instância global de métricas
_metrics_instance: Optional[MetricsCollector] = None

def get_metrics() -> MetricsCollector:
    """Retorna instância global de métricas"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance
