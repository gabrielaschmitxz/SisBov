@echo off
echo ========================================
echo   SISBOV - Versao Web
echo ========================================
echo.

REM Verificar se Flask esta instalado
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Flask nao encontrado. Instalando...
    pip install flask
    echo.
)

REM Executar o servidor
echo Iniciando servidor...
echo.
echo Acesse no navegador: http://localhost:5000
echo.
echo Para parar o servidor, pressione CTRL+C
echo ========================================
echo.

python app_web.py

pause

