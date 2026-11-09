#!/usr/bin/env bash
# Build script untuk platform hosting cloud (Render / Koyeb / Linux)
set -o errexit

echo "==> Menginstal dependensi Python..."
pip install -r requirements.txt

echo "==> Mengumpulkan berkas statis (collectstatic)..."
python manage.py collectstatic --no-input

echo "==> Menjalankan migrasi database..."
python manage.py migrate

echo "==> Memeriksa & menginisialisasi data awal cloud..."
python manage.py setup_cloud_db

echo "==> Build & Inisialisasi selesai!"
