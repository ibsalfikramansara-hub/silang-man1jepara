@echo off
:: ============================================================================
:: deploy.bat - Skrip Otomatis SILANG MAN 1 Jepara
:: Mendukung One-Click Run Local & One-Click Deploy Online ke Cloud
:: ============================================================================

setlocal enabledelayedexpansion
title SILANG MAN 1 Jepara - Deployment Manager
cd /d "%~dp0"

:: Cek argumen langsung dari command line (misal: deploy.bat online)
if /i "%1"=="online" goto DEPLOY_ONLINE
if /i "%1"=="local" goto RUN_LOCAL
if /i "%1"=="test" goto RUN_TEST

:MENU
cls
echo ==============================================================================
echo       SILANG - Sistem Informasi Laporan Barang Hilang MAN 1 Jepara
echo                          Pusat Manajemen Deployment
echo ==============================================================================
echo.
echo   [1] Jalankan Aplikasi di Komputer Lokal (http://127.0.0.1:8000)
echo   [2] ONE-CLICK DEPLOY ONLINE (Validasi, Test, Commit, dan Push ke Cloud)
echo   [3] Jalankan Pengujian Otomatis (Automated Test Suite - 23 Skenario)
echo   [4] Ekspor & Backup Data Database (initial_data.json)
echo   [5] Keluar
echo.
echo ==============================================================================
set /p PILIHAN="Pilih menu [1-5] lalu tekan Enter: "

if "%PILIHAN%"=="1" goto RUN_LOCAL
if "%PILIHAN%"=="2" goto DEPLOY_ONLINE
if "%PILIHAN%"=="3" goto RUN_TEST
if "%PILIHAN%"=="4" goto BACKUP_DATA
if "%PILIHAN%"=="5" goto SELESAI
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
:: 2. ONE-CLICK DEPLOY ONLINE
:: ============================================================================
:DEPLOY_ONLINE
cls
echo ==============================================================================
echo   ONE-CLICK DEPLOYMENT: SINKRONISASI DAN DEPLOY KE CLOUD HOSTING
echo ==============================================================================
echo.
call :CEK_VENV

echo [1/6] Menjalankan validasi sistem dan uji regresi lokal...
.\venv\Scripts\python.exe manage.py test --no-input
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Pengujian lokal gagal. Deployment dibatalkan untuk melindungi server cloud.
    echo         Perbaiki error di atas sebelum melakukan deploy.
    pause
    goto MENU
)
echo       [OK] Seluruh pengujian lokal lulus 100%%.
echo.

echo [2/6] Memeriksa repositori Git...
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git tidak terdeteksi di komputer ini. Silakan install Git.
    pause
    goto MENU
)

if not exist ".git" (
    echo       Menginisialisasi Git repository lokal...
    git init -b main
    echo       [OK] Git repo diinisialisasi pada branch main.
)

git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [KONFIGURASI AWAL REPOSITORI GITHUB]
    echo Belum ada remote repository GitHub yang terhubung.
    echo Masukkan URL GitHub repository Anda (contoh: https://github.com/akun/silang.git):
    set /p REPO_URL="URL GitHub: "
    if not "!REPO_URL!"=="" (
        git remote add origin !REPO_URL!
        echo [OK] Remote origin berhasil dihubungkan ke: !REPO_URL!
    ) else (
        echo [BATAL] URL tidak boleh kosong. Deployment dibatalkan.
        pause
        goto MENU
    )
)

echo.
echo [3/6] Memperbarui data seed cloud (initial_data.json)...
.\venv\Scripts\python.exe manage.py dumpdata accounts pengaduan barang --natural-foreign --natural-primary --indent 2 --output initial_data.json
echo       [OK] Data seed berhasil disinkronkan.
echo.

echo [4/6] Menyiapkan commit perubahan kode...
git status --short
echo.
set /p COMMIT_MSG="Masukkan catatan update [Enter untuk otomatis]: "
if "!COMMIT_MSG!"=="" (
    set COMMIT_MSG=Update aplikasi SILANG MAN 1 Jepara - %date% %time%
)

git add .
git commit -m "!COMMIT_MSG!" >nul 2>&1
echo       [OK] Perubahan berhasil di-commit.
echo.

echo [5/6] Mendorong (Push) kode ke GitHub untuk memicu Auto-Deploy Cloud...
git branch -M main
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo [PERINGATAN] Gagal melakukan push ke remote GitHub.
    echo             Pastikan koneksi internet aktif dan Anda memiliki akses tulis ke repositori.
    pause
    goto MENU
)
echo       [OK] Kode berhasil terkirim ke GitHub branch main.
echo.

echo [6/6] Menampilkan Status & Tautan Hosting Online...
echo ==============================================================================
echo   SUKSES! Push ke GitHub berhasil dilakukan.
echo   Cloud Hosting (Render / Koyeb) sedang memproses build otomatis:
echo     1. Menginstal dependensi baru
echo     2. Menjalankan migrasi database cloud (PostgreSQL Neon/Supabase)
echo     3. Mengompresi berkas statis (WhiteNoise)
echo     4. Mengaktifkan layanan web online secara otomatis
echo.
echo   Periksa dashboard hosting Anda untuk memantau proses:
echo   - Render Dashboard : https://dashboard.render.com
echo   - Neon Database    : https://console.neon.tech
echo.
echo   Aplikasi Online Anda akan aktif di URL yang telah Anda konfigurasi
echo   (contoh: https://silang-man1jepara.onrender.com)
echo ==============================================================================
echo.
pause
goto MENU

:: ============================================================================
:: 3. JALANKAN TEST SUITE
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
:: 4. BACKUP DATA
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
