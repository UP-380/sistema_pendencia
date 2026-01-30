@echo off
echo ======================================
echo  REINICIANDO SERVIDOR UP380
echo ======================================
echo.

cd /d "%~dp0"

echo [1/3] Parando containers...
docker compose down

echo.
echo [2/3] Iniciando containers...
docker compose up -d

echo.
echo [3/3] Verificando status...
docker compose ps

echo.
echo ======================================
echo  SERVIDOR REINICIADO COM SUCESSO!
echo ======================================
echo.
echo Aguarde 10 segundos e atualize a pagina (Ctrl+F5)
echo.
pause








