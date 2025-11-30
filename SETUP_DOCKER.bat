@echo off
echo ========================================
echo   🐳 SETUP - Docker Services
echo ========================================
echo.
echo Este script configura PostgreSQL e Redis via Docker
echo.
pause

echo.
echo 📦 Instalando PostgreSQL...
docker run --name postgres-trading ^
  -e POSTGRES_USER=leonardo ^
  -e POSTGRES_PASSWORD=trading123 ^
  -e POSTGRES_DB=trading_bot ^
  -p 5432:5432 ^
  -d postgres:15

echo.
echo 🚀 Instalando Redis...
docker run --name redis-trading ^
  -p 6379:6379 ^
  -d redis:7

echo.
echo ========================================
echo   ✅ DOCKER SERVICES RODANDO!
echo ========================================
echo.
echo PostgreSQL: localhost:5432
echo   User: leonardo
echo   Password: trading123
echo   Database: trading_bot
echo.
echo Redis: localhost:6379
echo.
echo Para parar:
echo   docker stop postgres-trading redis-trading
echo.
echo Para iniciar novamente:
echo   docker start postgres-trading redis-trading
echo ========================================
pause
