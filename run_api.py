"""
Script para iniciar a API FastAPI
"""
import sys
import os
import uvicorn

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    try:
        print("🚀 Iniciando FastAPI...")
        from backend.main import app
        print("✅ Backend carregado com sucesso")

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Erro ao iniciar FastAPI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
