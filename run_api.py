"""
Script para iniciar a API FastAPI
"""
import sys
import os
import uvicorn

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from backend.main import app
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001, 
        reload=False,
        log_level="info"
    )
