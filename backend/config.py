"""
Configurações do Backend FastAPI
"""
import os
import secrets
from datetime import timedelta
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da API"""
    
    # Ambiente
    PROJECT_NAME: str = "R7 Trading Bot API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas
    
    # Database
    DATABASE_PATH: str = "data/app_leonardo.db"
    
    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:8501",  # Streamlit
        "http://localhost:3000",  # Frontend dev
        "http://127.0.0.1:8501",
        "*"  # Permitir todos por enquanto
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Paths
    CONFIG_PATH: str = "config/bots_config.yaml"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


# Roles disponíveis
class UserRole:
    ADMIN = "admin"
    VIEWER = "viewer"
    TRADER = "trader"


# Permissões por role
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        "read:all",
        "write:all",
        "manage:users",
        "manage:config",
        "execute:trades",
        "manage:bot",
    ],
    UserRole.TRADER: [
        "read:all",
        "execute:trades",
        "manage:config",
    ],
    UserRole.VIEWER: [
        "read:dashboard",
        "read:positions",
        "read:stats",
    ],
}
