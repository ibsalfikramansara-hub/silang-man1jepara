@echo off
:: ============================================================================
:: online_tunnel.bat - Menjadikan SILANG MAN 1 Jepara Online ke Internet
:: Menggunakan Cloudflare Tunnel (100% Gratis, Tanpa Daftar, Auto HTTPS)
:: ============================================================================

setlocal enabledelayedexpansion
title SILANG MAN 1 Jepara - Online Cloudflare Tunnel
cd /d "%~dp0"

cls
echo ==============================================================================
echo       SILANG - Sistem Informasi Laporan Barang Hilang MAN 1 Jepara
echo                  MENGAKTIFKAN AKSES ONLINE PUBLIK (INTERNET)
echo ==============================================================================
echo.
echo [1/3] Memeriksa virtual environment & database...
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment belum ditemukan.
    pause
    exit /b 1
)

.\venv\Scripts\python.exe manage.py migrate --no-input >nul 2>&1
.\venv\Scripts\python.exe manage.py setup_cloud_db >nul 2>&1
echo       [OK] Database lokal siap digunakan.
echo.

echo [2/3] Memulai server Django SILANG di latar belakang...
start "SILANG - Django Server" /min cmd /c ".\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"
timeout /t 2 >nul
echo       [OK] Django Server berjalan di http://127.0.0.1:8000
echo.

echo [3/3] Menghubungkan ke Jaringan Global Cloudflare...
echo ==============================================================================
echo   MOHON TUNGGU SEBENTAR...
echo   Cloudflare sedang membuat tautan HTTPS Publik yang aman untuk aplikasi Anda.
echo   Cari baris tautan yang berakhiran: .trycloudflare.com di bawah ini:
echo ==============================================================================
echo.

cloudflared tunnel --url http://127.0.0.1:8000

echo.
echo Menghentikan server...
taskkill /f /im python.exe >nul 2>&1
pause
exit /b 0
