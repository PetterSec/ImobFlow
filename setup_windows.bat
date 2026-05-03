@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   ImobFlow — Setup Local (Windows)
echo ============================================================
echo.

REM Verifica Python 3.12
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python 3.12 nao encontrado!
    echo.
    echo Instale em: https://www.python.org/downloads/release/python-3120/
    echo Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('py -3.12 --version') do set PYVER=%%i
echo [OK] %PYVER% encontrado

REM Remove venv antigo se existir
if exist venv (
    echo [INFO] Removendo venv antigo...
    rmdir /s /q venv
)

echo [INFO] Criando novo venv com Python 3.12...
py -3.12 -m venv venv
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao criar venv!
    pause
    exit /b 1
)

echo [OK] Ambiente virtual criado

echo [INFO] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo [INFO] Atualizando pip...
python -m pip install --upgrade pip --quiet

echo [INFO] Instalando dependencias...
pip install -r requirements-dev.txt
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias!
    pause
    exit /b 1
)

echo [OK] Dependencias instaladas

REM Cria .env se nao existir
if not exist .env (
    echo [INFO] Criando .env a partir do .env.example...
    copy .env.example .env >nul
    echo [ATENCAO] Revise o arquivo .env se necessario
)

echo.
echo ============================================================
echo   Pronto! Para rodar o projeto:
echo.
echo   1. venv\Scripts\activate
echo   2. python run.py
echo   3. Abra: http://localhost:5000
echo ============================================================
pause
