"""
Dependências do FastAPI (autenticação, etc.)
"""
from typing import Optional, List
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth import auth_service
from .models import UserInDB, TokenData
from .config import settings, ROLE_PERMISSIONS


# Esquema de segurança Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInDB:
    """
    Obtém o usuário atual a partir do token JWT
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    token_data = auth_service.decode_token(token)
    
    if token_data is None:
        raise credentials_exception
    
    user = auth_service.get_user(token_data.username)
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """
    Garante que o usuário está ativo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    return current_user


def require_permission(permission: str):
    """
    Decorator para exigir permissão específica
    """
    async def permission_dependency(
        current_user: UserInDB = Depends(get_current_user)
    ) -> UserInDB:
        if not auth_service.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissão necessária: {permission}"
            )
        return current_user
    
    return permission_dependency


def require_role(roles: List[str]):
    """
    Decorator para exigir role específica
    """
    async def role_dependency(
        current_user: UserInDB = Depends(get_current_user)
    ) -> UserInDB:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role necessária: {', '.join(roles)}"
            )
        return current_user
    
    return role_dependency


# Dependências comuns
RequireAdmin = Depends(require_role(["admin"]))
RequireTrader = Depends(require_role(["admin", "trader"]))
RequireViewer = Depends(require_role(["admin", "trader", "viewer"]))

RequireManageBot = Depends(require_permission("manage:bot"))
RequireManageConfig = Depends(require_permission("manage:config"))
RequireExecuteTrades = Depends(require_permission("execute:trades"))
RequireReadAll = Depends(require_permission("read:all"))
