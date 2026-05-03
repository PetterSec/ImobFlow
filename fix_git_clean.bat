@echo off
chcp 65001 >nul
echo.
echo ============================================================
echo   ImobFlow — Limpeza do Git
echo ============================================================
echo.
echo [INFO] Removendo __pycache__ do rastreamento git...
git rm -r --cached __pycache__ 2>nul
git rm -r --cached app/__pycache__ 2>nul
git rm -r --cached app/routes/__pycache__ 2>nul
git rm -r --cached app/services/__pycache__ 2>nul
git rm -r --cached app/middleware/__pycache__ 2>nul

echo [INFO] Removendo banco SQLite local do git...
git rm -r --cached instance/ 2>nul

echo [INFO] Removendo .env do git se rastreado...
git rm --cached .env 2>nul

echo.
echo [INFO] Commitando limpeza...
git add .gitignore
git commit -m "chore: remove __pycache__ e instance do git tracking"

echo [INFO] Fazendo push...
git push

echo.
echo ============================================================
echo   Limpeza concluida!
echo ============================================================
pause
