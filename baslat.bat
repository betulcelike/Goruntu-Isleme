@echo off
title GestureFlow AI — Vision Studio Baslatici
cd /d "%~dp0"

echo ==================================================
echo         GestureFlow AI Baslatiliyor...
echo ==================================================
echo.

if exist venv\Scripts\python.exe (
    echo [BILGI] Sanal ortam (venv) aktiflestiriliyor...
    venv\Scripts\python.exe app.py
) else (
    echo [UYARI] Sanal ortam bulunamadi, sistem Python'i kullaniliyor...
    python app.py
)

if %errorlevel% neq 0 (
    echo.
    echo [BILGI] Uygulama sonlandi veya hata olustu.
    echo.
    pause
)
