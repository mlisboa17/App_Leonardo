"""
R7 Trading Bot API - FastAPI Application
=========================================
API REST com autenticação JWT para controle do bot de trading.

Endpoints:
- /api/auth - Autenticação (login, logout, usuários)
- /api/dashboard - Estatísticas e dados do dashboard
- /api/config - Configurações do bot
- /api/actions - Ações (start, stop, liquidar)
- /docs - Documentação Swagger
"""

import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime
import time
import os
import json

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routes import auth_routes, dashboard_routes, config_routes, actions_routes, bot_control_routes, audit_routes


# Lifespan para startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia startup e shutdown"""
    app.startup_time = time.time()
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           R7 TRADING BOT API - v{settings.VERSION}                ║
╠═══════════════════════════════════════════════════════════╣
║  🚀 Servidor iniciando...                                 ║
║  📍 URL: http://{settings.HOST}:{settings.PORT}                         ║
║  📚 Docs: http://{settings.HOST}:{settings.PORT}/docs                   ║
║  🔐 Auth: JWT Bearer Token                                ║
╚═══════════════════════════════════════════════════════════╝
    """)
    yield
    print("\n⚠️ Servidor encerrando...")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## R7 Trading Bot API

API REST para controle e monitoramento do bot de trading.

### Autenticação
Todas as rotas (exceto login) requerem token JWT no header:
```
Authorization: Bearer <token>
```

### Níveis de Acesso
- **admin**: Acesso total (gerenciar usuários, configurar, liquidar)
- **trader**: Operar e configurar (sem gerenciar usuários)
- **viewer**: Apenas visualização

### Endpoints Principais
- `POST /api/auth/login` - Fazer login
- `GET /api/dashboard/summary` - Resumo do dashboard
- `GET /api/dashboard/positions` - Posições abertas
- `POST /api/actions/bot/start` - Iniciar bot
- `POST /api/actions/bot/stop` - Parar bot
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Erro interno do servidor",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# Registrar rotas
app.include_router(auth_routes.router, prefix="/api")
app.include_router(dashboard_routes.router, prefix="/api")
app.include_router(config_routes.router, prefix="/api")
app.include_router(actions_routes.router, prefix="/api")
app.include_router(bot_control_routes.router, prefix="/api")
app.include_router(audit_routes.router, prefix="/api")


# Rota raiz
@app.get("/")
async def root():
    """Informações da API"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs",
        "health": "/health",
        "timestamp": datetime.now().isoformat()
    }


# Health check
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Verificação de saúde completa da API"""
    uptime_seconds = int(time.time() - app.startup_time) if hasattr(app, 'startup_time') else 0
    
    # Verificar se arquivos de dados existem
    data_exists = os.path.exists("data")
    config_exists = os.path.exists("config/bots_config.yaml")
    
    # Calcular uso de disco
    try:
        total, used, free = os.statvfs("/") if os.name != 'nt' else (0, 0, 0)
        disk_usage = round((used / total * 100), 2) if total > 0 else 0
    except:
        disk_usage = 0
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m",
        "environment": {
            "debug": settings.DEBUG,
            "host": settings.HOST,
            "port": settings.PORT,
        },
        "data": {
            "data_dir_exists": data_exists,
            "config_exists": config_exists,
        },
        "system": {
            "disk_usage_percent": disk_usage,
            "python_version": "3.11+",
        }
    }


# Função para rodar standalone
def run_api():
    """Inicia o servidor da API"""
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    run_api()
