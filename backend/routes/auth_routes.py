"""
Rotas de autenticação
"""
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import auth_service
from ..config import settings, UserRole
from ..models import (
    Token, LoginRequest, UserCreate, UserResponse, 
    UserUpdate, APIResponse, UserInDB
)
from ..dependencies import get_current_user, require_role


router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=Token)
async def login(request: LoginRequest):
    """
    Fazer login e obter token JWT
    """
    user = auth_service.authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        user=user,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    """
    Obter dados do usuário logado
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )


@router.put("/me/password", response_model=APIResponse)
async def change_password(
    new_password: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Trocar própria senha
    """
    auth_service.update_user(current_user.username, password=new_password)
    
    return APIResponse(
        success=True,
        message="Senha alterada com sucesso"
    )


# ==================== ADMIN ROUTES ====================

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN]))
):
    """
    Listar todos os usuários (admin only)
    """
    users = auth_service.get_all_users()
    
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            last_login=u.last_login
        )
        for u in users
    ]


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN]))
):
    """
    Criar novo usuário (admin only)
    """
    try:
        user = auth_service.create_user(user_data)
        
        return UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/users/{username}", response_model=UserResponse)
async def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN]))
):
    """
    Atualizar usuário (admin only)
    """
    update_data = user_update.model_dump(exclude_unset=True)
    
    user = auth_service.update_user(username, **update_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.delete("/users/{username}", response_model=APIResponse)
async def delete_user(
    username: str,
    current_user: UserInDB = Depends(require_role([UserRole.ADMIN]))
):
    """
    Remover usuário (admin only)
    """
    try:
        if auth_service.delete_user(username):
            return APIResponse(
                success=True,
                message=f"Usuário {username} removido"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
