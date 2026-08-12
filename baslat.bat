@echo off
title GestureFlow AI — Vision Studio Baslatici
cd /d "%~dp0"

echo ==================================================
echo         GestureFlow AI Baslatiliyor...
echo ==================================================
echo.

python app.py

if %errorlevel% neq 0 (
    echo.
    echo [BILGI] Uygulama sonlandi veya hata olustu.
    echo.
    pause
)
