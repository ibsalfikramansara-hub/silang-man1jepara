#!/usr/bin/env bash
# Build script untuk platform hosting cloud (Vercel / Render / Linux)
set -o errexit

echo "==> Memeriksa environment..."
PYTHON_BIN=$(command -v python3 || command -v python || echo "python")

if [ -z "$VERCEL" ]; then
    echo "==> Menginstal dependensi Python..."
    $PYTHON_BIN -m pip install -r requirements.txt
else
    echo "==> Lingkungan Vercel terdeteksi (pip dikelola oleh Vercel)"
fi

echo "==> Mengumpulkan berkas statis (collectstatic)..."
$PYTHON_BIN manage.py collectstatic --no-input || true

echo "==> Menjalankan migrasi database..."
$PYTHON_BIN manage.py migrate --no-input || true

echo "==> Memeriksa & menginisialisasi data awal cloud..."
$PYTHON_BIN manage.py setup_cloud_db || true

echo "==> Build & Inisialisasi selesai!"
