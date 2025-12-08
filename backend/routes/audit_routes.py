"""
Rotas de Auditoria - Acesso aos logs de auditoria do sistema
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from ..models import APIResponse, UserInDB
from ..dependencies import get_current_user, require_permission
from ..config import UserRole
from src.audit import get_audit_logger

router = APIRouter(prefix="/audit", tags=["Audit"])
audit_logger = get_audit_logger()


@router.get("/events", response_model=APIResponse)
async def get_audit_events(
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retorna eventos de auditoria com filtros opcionais
    
    Parâmetros:
    - limit: número máximo de eventos (1-1000)
    - event_type: filtrar por tipo ('config_change', 'restart', 'stop', 'trade', 'error', 'position_change')
    - source: filtrar por origem ('api', 'watcher', 'bot', 'coordinator', 'user')
    - severity: filtrar por severidade ('info', 'warning', 'critical')
    """
    try:
        # Permissão: apenas admin ou auditor podem acessar logs
        if current_user.role not in [UserRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        events = audit_logger.get_recent_events(
            limit=limit,
            event_type=event_type,
            source=source,
            severity=severity
        )
        
        return APIResponse(
            success=True,
            data={
                'events': events,
                'total': len(events),
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Erro ao buscar eventos de auditoria: {str(e)}"
        )


@router.get("/events/summary", response_model=APIResponse)
async def get_audit_summary(
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retorna sumário de eventos de auditoria por tipo e severidade
    """
    try:
        if current_user.role not in [UserRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        events = audit_logger.get_recent_events(limit=10000)
        
        # Agrupa por tipo
        by_type = {}
        by_severity = {}
        by_source = {}
        
        for event in events:
            # Por tipo
            event_type = event.get('event_type', 'unknown')
            by_type[event_type] = by_type.get(event_type, 0) + 1
            
            # Por severidade
            severity = event.get('severity', 'unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # Por fonte
            source = event.get('source', 'unknown')
            by_source[source] = by_source.get(source, 0) + 1
        
        return APIResponse(
            success=True,
            data={
                'by_type': by_type,
                'by_severity': by_severity,
                'by_source': by_source,
                'total_events': len(events),
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Erro ao buscar sumário de auditoria: {str(e)}"
        )


@router.get("/events/{event_type}", response_model=APIResponse)
async def get_events_by_type(
    event_type: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retorna eventos de um tipo específico
    
    Tipos disponíveis:
    - config_change: Mudanças de configuração
    - restart: Reinícios de bots
    - stop: Paradas de bots
    - trade: Execução de trades
    - error: Erros do sistema
    - position_change: Mudanças de posições
    """
    try:
        if current_user.role not in [UserRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        events = audit_logger.get_recent_events(
            limit=limit,
            event_type=event_type
        )
        
        return APIResponse(
            success=True,
            data={
                'event_type': event_type,
                'events': events,
                'total': len(events),
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Erro ao buscar eventos: {str(e)}"
        )


@router.get("/critical", response_model=APIResponse)
async def get_critical_events(
    limit: int = Query(50, ge=1, le=500),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Retorna apenas eventos críticos (erros, restarts, etc)
    Útil para monitoramento e alertas
    """
    try:
        if current_user.role not in [UserRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        all_events = audit_logger.get_recent_events(limit=limit*5)
        critical = [e for e in all_events if e.get('severity') == 'critical'][:limit]
        
        return APIResponse(
            success=True,
            data={
                'critical_events': critical,
                'total': len(critical),
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Erro ao buscar eventos críticos: {str(e)}"
        )


@router.post("/export", response_model=APIResponse)
async def export_audit_logs(
    event_type: Optional[str] = Query(None),
    output_format: str = Query("json", regex="^(json|csv)$"),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Exporta logs de auditoria para arquivo
    
    Formatos suportados: json, csv
    """
    try:
        if current_user.role not in [UserRole.ADMIN]:
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        output_file = f"data/audit/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}"
        
        if output_format == "json":
            count = audit_logger.export_events(output_file, event_type=event_type)
        else:
            # CSV export would go here
            return APIResponse(
                success=False,
                error="Formato CSV ainda não implementado"
            )
        
        return APIResponse(
            success=True,
            data={
                'message': f'{count} eventos exportados',
                'output_file': output_file,
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=f"Erro ao exportar logs: {str(e)}"
        )
