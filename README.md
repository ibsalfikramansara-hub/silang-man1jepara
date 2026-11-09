# SILANG - Sistem Informasi Laporan Barang Hilang MAN 1 Jepara

Aplikasi web berbasis Python (Django 4.2) untuk mengelola pelaporan dan klaim barang hilang/ditemukan serta pengaduan (kritik, saran & aspirasi) bagi civitas akademika **MAN 1 Jepara**.

---

## 🚀 Arsitektur & Teknologi Cloud (100% Free Tier & Persisten)

Aplikasi dirancang dengan arsitektur **Zero-Cost Production** yang stabil, aman, dan persisten tanpa kartu kredit atau biaya langganan:

1. **Web Application Hosting**:
   - **Render.com** (Web Service Free Tier, Region Singapore)
   - Dukungan native Python 3.11, WSGI Gunicorn, dan WhiteNoise static compression.
   - Terkoneksi otomatis dengan GitHub repository (**Auto-Deploy on Git Push**).
   - Dilengkapi sertifikat SSL HTTPS otomatis dari Let's Encrypt.
2. **Cloud Database (Persisten Permanen)**:
   - **Neon Tech (neon.tech)** atau **Supabase (supabase.com)**
   - Serverless PostgreSQL (Free Tier permanen 0.5 GB, SSL terintegrasi).
   - Database cloud dipisah total dari database SQLite lokal.
3. **Penyajian Berkas Statis**:
   - **WhiteNoise**: Menyajikan seluruh aset CSS, JS, dan ikon secara terkompresi langsung dari Gunicorn tanpa perlu bucket S3 berbayar.
4. **Data Seed & Migration**:
   - `build.sh` dan `setup_cloud_db.py` mengurus migrasi skema dan inisialisasi akun bawaan secara otomatis pada deployment pertama.

---

## ⚡ One-Click Deployment (`deploy.bat`)

Sistem dilengkapi dengan skrip otomatisasi satu klik untuk Windows (`deploy.bat`). Anda cukup melakukan double-click pada file tersebut:

```text
==============================================================================
      SILANG - Sistem Informasi Laporan Barang Hilang MAN 1 Jepara
                         Pusat Manajemen Deployment
==============================================================================

  [1] Jalankan Aplikasi di Komputer Lokal (http://127.0.0.1:8000)
  [2] ONE-CLICK DEPLOY ONLINE (Validasi, Test, Commit, dan Push ke Cloud)
  [3] Jalankan Pengujian Otomatis (Automated Test Suite - 23 Skenario)
  [4] Ekspor & Backup Data Database (initial_data.json)
  [5] Keluar
==============================================================================
```

### Keunggulan One-Click Deploy (Menu 2):
1. **Safety Pre-Check**: Menjalankan 23 automated unit test lokal terlebih dahulu. Jika ada error, proses dihentikan otomatis untuk mencegah kode rusak naik ke cloud.
2. **Auto Seed Export**: Mengekspor data master lokal ke `initial_data.json`.
3. **Auto Git Commit & Push**: Melacak perubahan kode, membuat commit, dan mendorong branch `main` ke GitHub.
4. **Auto-Trigger Cloud Build**: GitHub webhook langsung memicu Render/Koyeb untuk membuild dan mengaktifkan versi terbaru tanpa intervensi manual!

---

## 📋 Langkah Awal Deployment ke Internet (Setup 1 Kali)

### Langkah 1: Buat Database Cloud Gratis (Neon.tech)
1. Buka [https://neon.tech](https://neon.tech) dan daftar/login dengan akun GitHub atau Google (Gratis selamanya).
2. Buat project baru dengan nama `silang-man1jepara` (pilih region terdekat: `Singapore / AWS ap-southeast-1`).
3. Salin **Connection String** yang diberikan (format: `postgresql://user:password@ep-xxxx.neon.tech/neondb?sslmode=require`).

### Langkah 2: Buat Repositori GitHub & Push Kode
1. Buat repositori baru di [GitHub](https://github.com/new) (beri nama misalnya `silang-man1jepara`, pilih Private atau Public).
2. Buka PowerShell / Terminal di folder proyek ini, lalu jalankan:
   ```powershell
   git remote add origin https://github.com/<username-anda>/silang-man1jepara.git
   git push -u origin main
   ```
   *(Atau cukup double-click `deploy.bat` dan pilih menu 2, lalu masukkan URL GitHub tersebut).*

### Langkah 3: Hubungkan ke Render.com (Web Service)
1. Buka [https://dashboard.render.com](https://dashboard.render.com) dan login dengan akun GitHub Anda.
2. Klik tombol **New +** $\rightarrow$ pilih **Web Service**.
3. Pilih repositori `silang-man1jepara` yang baru Anda push.
4. Konfigurasi service (atau gunakan `render.yaml`):
   - **Name**: `silang-man1jepara`
   - **Region**: `Singapore`
   - **Runtime**: `Python 3`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn config.wsgi:application --log-file -`
   - **Instance Type**: `Free`
5. Masukkan **Environment Variables**:
   - `DATABASE_URL`: *(Tempel URL connection string Neon dari Langkah 1)*
   - `DJANGO_SECRET_KEY`: *(Ketik kunci acak yang panjang)*
   - `DJANGO_DEBUG`: `False`
   - `DJANGO_ALLOWED_HOSTS`: `.onrender.com`
   - `CSRF_TRUSTED_ORIGINS`: `https://*.onrender.com`
   - `SECURE_SSL_REDIRECT`: `True`
6. Klik **Create Web Service**. Render akan otomatis menginstal dependensi, menjalankan migrasi database Neon, menginisialisasi akun bawaan, dan menampilkan URL publik Anda:
   `https://silang-man1jepara.onrender.com`

---

## 🔐 Akun Bawaan (Default Seed Data)

Setelah deployment berhasil, seluruh akun dan role siap digunakan secara langsung:

| Role | Username | Password Bawaan | Hak Akses Utama |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Kendali penuh, User Management, Kategori, Pos, Rekapitulasi |
| **Petugas Pengaduan** | `petugas_pengaduan` | `password123` | Penanganan laporan pengaduan, eskalasi ke pimpinan |
| **Petugas Barang** | `petugas_barang` | `password123` | Input temuan, Papan temuan, verifikasi klaim, Berita Acara |
| **Kepala Madrasah** | `kepala_madrasah` | `password123` | Monitoring statistik, penanganan kasus eskalasi |
| **Pelapor (Siswa)** | `pelapor` | `password123` | Buat laporan pengaduan/kehilangan, klaim barang, rating |

> **Catatan Keamanan:** Setelah login pertama kali di lingkungan online, silakan ubah password akun `admin` melalui menu **Profil $\rightarrow$ Ubah Password**.

---

## 🛡️ Kebijakan Keamanan & Backup Data

1. **Pemisahan Database**:
   - File `db.sqlite3` di komputer lokal tidak pernah terunggah ke repositori online (terlindungi oleh `.gitignore`).
   - Server cloud hanya terhubung ke PostgreSQL cloud via environment variable `DATABASE_URL`.
2. **Kerahasiaan Kredensial**:
   - Kunci rahasia dan password database dikonfigurasi melalui platform cloud environment variables, bukan hardcoded di kode sumber.
3. **Persistensi Data**:
   - Database PostgreSQL di Neon bersifat persisten permanen.
   - Setiap redeployment kode **tidak akan pernah menghapus** data laporan, pengaduan, atau pengguna yang tersimpan di cloud.
4. **Mekanisme Backup**:
   - Gunakan menu `[4]` pada `deploy.bat` untuk mengekspor snapshot data lokal/cloud secara berkala ke berkas JSON.

---

## 🧪 Menjalankan Pengujian Lokal (Test Suite)

```powershell
.\venv\Scripts\python.exe manage.py test
```
*Total 23 skenario uji mencakup seluruh alur bisnis, RBAC, CRUD, dan pencetakan tanda terima dengan status kelulusan 100% OK.*
