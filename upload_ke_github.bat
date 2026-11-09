@echo off
title Upload ke GitHub - SILANG MAN 1 Jepara
cd /d "%~dp0"

cls
echo ==============================================================================
echo       SILANG - Sistem Informasi Laporan Barang Hilang MAN 1 Jepara
echo                MENGUNGGAH KODE KE REPOSITORI GITHUB
echo ==============================================================================
echo.
echo Repositori Target: https://github.com/ibsalfikramansara-hub/silang-man1jepara.git
echo.
echo Sedang melakukan sinkronisasi dan push ke GitHub...
echo (Jika muncul jendela pop-up otentikasi browser, silakan klik 'Sign in with your browser' / 'Authorize')
echo.

git branch -M main
git push -u origin main

echo.
if %errorlevel% equ 0 (
    echo ==============================================================================
    echo   [BERHASIL] Seluruh kode aplikasi dan konfigurasi cloud berhasil diunggah!
    echo   Silakan cek repositori Anda di:
    echo   https://github.com/ibsalfikramansara-hub/silang-man1jepara
    echo ==============================================================================
) else (
    echo ==============================================================================
    echo   [GAGAL] Terjadi kendala saat push. Pastikan koneksi internet aktif.
    echo ==============================================================================
)
echo.
pause
