"""
Serviço de autenticação com JWT
"""
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from pathlib import Path

from jose import JWTError, jwt

from .config import settings, UserRole, ROLE_PERMISSIONS
from .models import UserInDB, UserCreate, TokenData

# Arquivo de usuários (JSON simples para começar)
USERS_FILE = Path("data/users.json")


class AuthService:
    """Serviço de autenticação"""
    
    def __init__(self):
        self._ensure_users_file()
        self._ensure_admin_user()
    
    def _ensure_users_file(self):
        """Cria arquivo de usuários se não existir"""
        if not USERS_FILE.exists():
            USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._save_users({})
    
    def _ensure_admin_user(self):
        """Garante que existe um usuário admin"""
        users = self._load_users()
        
        if "admin" not in users:
            # Senha padrão: trocar depois!
            default_password = os.getenv("ADMIN_PASSWORD", "admin123")
            
            users["admin"] = {
                "id": 1,
                "username": "admin",
                "hashed_password": self.hash_password(default_password),
                "role": UserRole.ADMIN,
                "is_active": True,
                "created_at": datetime.now().isoformat(),
                "last_login": None
            }
            self._save_users(users)
            print(f"⚠️ Usuário admin criado com senha padrão. TROQUE A SENHA!")
    
    def _load_users(self) -> dict:
        """Carrega usuários do arquivo"""
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_users(self, users: dict):
        """Salva usuários no arquivo"""
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2, default=str)
    
    def hash_password(self, password: str) -> str:
        """Hash de senha usando SHA-256 com salt"""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((password + salt).encode())
        return f"{salt}${hash_obj.hexdigest()}"
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica senha"""
        try:
            salt, stored_hash = hashed_password.split('$')
            hash_obj = hashlib.sha256((plain_password + salt).encode())
            return hash_obj.hexdigest() == stored_hash
        except:
            return False
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """Busca usuário por username"""
        users = self._load_users()
        
        if username not in users:
            return None
        
        user_data = users[username]
        return UserInDB(**user_data)
    
    def get_all_users(self) -> List[UserInDB]:
        """Lista todos os usuários"""
        users = self._load_users()
        return [UserInDB(**u) for u in users.values()]
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Autentica usuário"""
        user = self.get_user(username)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        # Atualiza último login
        users = self._load_users()
        users[username]["last_login"] = datetime.now().isoformat()
        self._save_users(users)
        
        return user
    
    def create_user(self, user_data: UserCreate) -> UserInDB:
        """Cria novo usuário"""
        users = self._load_users()
        
        if user_data.username in users:
            raise ValueError("Usuário já existe")
        
        # Gerar ID
        max_id = max([u.get("id", 0) for u in users.values()], default=0)
        new_id = max_id + 1
        
        new_user = {
            "id": new_id,
            "username": user_data.username,
            "hashed_password": self.hash_password(user_data.password),
            "role": user_data.role,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        users[user_data.username] = new_user
        self._save_users(users)
        
        return UserInDB(**new_user)
    
    def update_user(self, username: str, **kwargs) -> Optional[UserInDB]:
        """Atualiza usuário"""
        users = self._load_users()
        
        if username not in users:
            return None
        
        for key, value in kwargs.items():
            if value is not None:
                if key == "password":
                    users[username]["hashed_password"] = self.hash_password(value)
                else:
                    users[username][key] = value
        
        self._save_users(users)
        return UserInDB(**users[username])
    
    def delete_user(self, username: str) -> bool:
        """Remove usuário"""
        if username == "admin":
            raise ValueError("Não é possível remover o admin")
        
        users = self._load_users()
        
        if username not in users:
            return False
        
        del users[username]
        self._save_users(users)
        return True
    
    def create_access_token(self, user: UserInDB, expires_delta: Optional[timedelta] = None) -> str:
        """Cria token JWT"""
        permissions = ROLE_PERMISSIONS.get(user.role, [])
        
        to_encode = {
            "sub": user.username,
            "role": user.role,
            "permissions": permissions,
            "iat": datetime.utcnow(),
        }
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode["exp"] = expire
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decodifica token JWT"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            permissions: List[str] = payload.get("permissions", [])
            
            if username is None:
                return None
            
            return TokenData(username=username, role=role, permissions=permissions)
            
        except JWTError:
            return None
    
    def has_permission(self, user: UserInDB, permission: str) -> bool:
        """Verifica se usuário tem permissão"""
        user_permissions = ROLE_PERMISSIONS.get(user.role, [])
        
        # Admin tem todas as permissões
        if "write:all" in user_permissions or "read:all" in user_permissions:
            return True
        
        return permission in user_permissions


# Instância global
auth_service = AuthService()
