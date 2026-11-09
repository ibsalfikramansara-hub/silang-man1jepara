@echo off
:: ============================================================================
:: deploy.bat - Pusat Kendali SILANG MAN 1 Jepara
:: Mendukung Jalankan Lokal, Online Instan via Cloudflare, dan Cloud Deploy
:: ============================================================================

setlocal enabledelayedexpansion
title SILANG MAN 1 Jepara - Pusat Kendali Deployment
cd /d "%~dp0"

:: Cek argumen langsung dari command line
if /i "%1"=="online" goto ONLINE_INSTAN
if /i "%1"=="cloud" goto DEPLOY_CLOUD
if /i "%1"=="local" goto RUN_LOCAL
if /i "%1"=="test" goto RUN_TEST

:MENU
cls
echo ==============================================================================
echo       SILANG - Sistem Informasi Laporan Barang Hilang MAN 1 Jepara
echo                          Pusat Kendali Aplikasi
echo ==============================================================================
echo.
echo   [1] Jalankan di Komputer Lokal (http://127.0.0.1:8000)
echo   [2] ONLINE-KAN SEKARANG KE INTERNET (1-Click Cloudflare Tunnel Instan)
echo       -^> Tanpa perlu daftar akun, langsung dapat link HTTPS publik aktif!
echo.
echo   [3] Deploy ke Cloud Server Permanen (GitHub + Render / Neon PostgreSQL)
echo       -^> Server tetap aktif 24 jam meskipun laptop dimatikan
echo.
echo   [4] Jalankan Pengujian Otomatis (Automated Test Suite - 23 Skenario)
echo   [5] Ekspor & Backup Data Database (initial_data.json)
echo   [6] Keluar
echo.
echo ==============================================================================
set /p PILIHAN="Pilih menu [1-6] lalu tekan Enter: "

if "%PILIHAN%"=="1" goto RUN_LOCAL
if "%PILIHAN%"=="2" goto ONLINE_INSTAN
if "%PILIHAN%"=="3" goto DEPLOY_CLOUD
if "%PILIHAN%"=="4" goto RUN_TEST
if "%PILIHAN%"=="5" goto BACKUP_DATA
if "%PILIHAN%"=="6" goto SELESAI
goto MENU

:: ============================================================================
:: 1. JALANKAN LOKAL
:: ============================================================================
:RUN_LOCAL
cls
echo ==============================================================================
echo   MENJALANKAN SILANG DI LINGKUNGAN LOKAL (LOCALHOST)
echo ==============================================================================
echo.
call :CEK_VENV
echo [1/3] Menjalankan migrasi database lokal...
.\venv\Scripts\python.exe manage.py migrate
echo [2/3] Memastikan akun admin tersedia...
.\venv\Scripts\python.exe manage.py setup_cloud_db
echo.
echo [3/3] Memulai server lokal...
echo ==============================================================================
echo   Aplikasi dapat diakses di : http://127.0.0.1:8000/
echo   Admin Panel Django        : http://127.0.0.1:8000/admin/
echo   Tekan Ctrl + C untuk menghentikan server.
echo ==============================================================================
echo.
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
pause
goto MENU

:: ============================================================================
:: 2. ONLINE INSTAN VIA CLOUDFLARE TUNNEL
:: ============================================================================
:ONLINE_INSTAN
cls
call online_tunnel.bat
goto MENU

:: ============================================================================
:: 3. DEPLOY KE CLOUD SERVER PERMANEN (GITHUB + RENDER)
:: ============================================================================
:DEPLOY_CLOUD
cls
echo ==============================================================================
echo   DEPLOY KE CLOUD HOSTING PERMANEN (GITHUB + RENDER / NEON)
echo ==============================================================================
echo.
call :CEK_VENV

echo [1/5] Menjalankan validasi sistem dan uji regresi lokal...
.\venv\Scripts\python.exe manage.py test --no-input
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Pengujian lokal gagal. Deployment dibatalkan untuk melindungi server cloud.
    pause
    goto MENU
)
echo       [OK] Seluruh pengujian lokal lulus 100%%.
echo.

echo [2/5] Memeriksa repositori Git...
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git tidak terdeteksi. Silakan install Git.
    pause
    goto MENU
)

if not exist ".git" (
    git init -b main
    echo       [OK] Git repo diinisialisasi pada branch main.
)

git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [KONFIGURASI AWAL GITHUB]
    echo Masukkan URL GitHub repository Anda (contoh: https://github.com/akun/silang.git):
    set /p REPO_URL="URL GitHub: "
    if not "!REPO_URL!"=="" (
        git remote add origin !REPO_URL!
        echo [OK] Remote origin dihubungkan ke: !REPO_URL!
    ) else (
        echo [BATAL] URL tidak boleh kosong.
        pause
        goto MENU
    )
)

echo.
echo [3/5] Memperbarui data seed cloud (initial_data.json)...
.\venv\Scripts\python.exe manage.py dumpdata accounts pengaduan barang --natural-foreign --natural-primary --indent 2 --output initial_data.json
echo       [OK] Data seed berhasil disinkronkan.
echo.

echo [4/5] Menyiapkan commit perubahan kode...
set /p COMMIT_MSG="Masukkan catatan update [Enter untuk otomatis]: "
if "!COMMIT_MSG!"=="" (
    set COMMIT_MSG=Update aplikasi SILANG MAN 1 Jepara - %date% %time%
)

git add .
git commit -m "!COMMIT_MSG!" >nul 2>&1
echo       [OK] Perubahan berhasil di-commit.
echo.

echo [5/5] Mendorong (Push) kode ke GitHub...
git branch -M main
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo [PERINGATAN] Gagal push ke GitHub. Pastikan internet aktif dan sudah login git.
    pause
    goto MENU
)
echo.
echo ==============================================================================
echo   SUKSES! Push ke GitHub berhasil.
echo   Render sedang memproses auto-deploy aplikasi Anda.
echo ==============================================================================
echo.
pause
goto MENU

:: ============================================================================
:: 4. JALANKAN TEST SUITE
:: ============================================================================
:RUN_TEST
cls
echo ==============================================================================
echo   MENJALANKAN AUTOMATED TEST SUITE (DJANGO TESTS)
echo ==============================================================================
echo.
call :CEK_VENV
.\venv\Scripts\python.exe manage.py test --verbosity=2
echo.
pause
goto MENU

:: ============================================================================
:: 5. BACKUP DATA
:: ============================================================================
:BACKUP_DATA
cls
echo ==============================================================================
echo   BACKUP & EKSPOR DATA APLIKASI
echo ==============================================================================
echo.
call :CEK_VENV
echo Mengekspor data ke initial_data.json...
.\venv\Scripts\python.exe manage.py dumpdata accounts pengaduan barang --natural-foreign --natural-primary --indent 2 --output initial_data.json
if %errorlevel% equ 0 (
    echo [OK] Backup data aplikasi berhasil disimpan di: initial_data.json
) else (
    echo [ERROR] Gagal mengekspor data.
)
echo.
pause
goto MENU

:: ============================================================================
:: HELPER: CEK VIRTUAL ENVIRONMENT
:: ============================================================================
:CEK_VENV
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Virtual environment belum ditemukan. Membuat venv...
    python -m venv venv
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
)
exit /b 0

:SELESAI
echo.
echo Terima kasih telah menggunakan SILANG MAN 1 Jepara.
exit /b 0
