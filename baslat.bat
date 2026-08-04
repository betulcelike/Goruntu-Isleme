@echo off
title GestureFlow AI - Baslatici
echo ==================================================
echo         GestureFlow AI Baslatiliyor...
echo ==================================================
echo.

:: Sanal ortam kontrolü ve çalıştırma
if exist venv\Scripts\python.exe (
    echo Windows Sanal Ortami (venv) aktif ediliyor...
    venv\Scripts\python.exe app.py
) else (
    echo Sistem Python kullanilarak baslatiliyor...
    python app.py
)

if %errorlevel% neq 0 (
    echo.
    echo [HATA] Uygulama baslatilamadi! Lutfen Python'in yuklu oldugundan ve
    echo        gerekli kutuphanelerin (requirements.txt) yuklendiginden emin olun.
    echo.
)
pause
