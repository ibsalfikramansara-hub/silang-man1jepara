# SILANG - Sistem Informasi Laporan Barang Hilang MAN 1 Jepara

Aplikasi web berbasis Python (Django) untuk mengelola pelaporan dan klaim barang hilang/ditemukan serta pengaduan (kritik & saran) bagi civitas akademika MAN 1 Jepara.

## Tech Stack

- **Backend:** Python + Django 4.2
- **Database:** SQLite (development), dapat diganti PostgreSQL
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **ORM:** Django ORM

## Struktur Proyek

```
pengaduan_madrasah/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── README.md
├── config/                   # Konfigurasi proyek Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/                 # Modul akun, autentikasi & role (RBAC)
│   ├── models.py             # User kustom (5 role)
│   ├── views.py              # Login, logout, dashboard, manajemen user
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   └── templates/accounts/
│       ├── profile.html
│       ├── user_list.html
│       ├── user_form.html
│       └── user_confirm_delete.html
├── pengaduan/                # Modul pengaduan (kritik/saran)
│   ├── models.py             # KategoriPengaduan, Pengaduan, LogTindakLanjut
│   ├── views.py              # CRUD pengaduan, petugas, eskalasi, rating
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   └── templates/pengaduan/
│       ├── form.html
│       ├── list.html
│       ├── detail.html
│       ├── confirm_delete.html
│       ├── petugas_list.html
│       ├── petugas_detail.html
│       ├── action_form.html
│       ├── escalate_form.html
│       ├── kepala_eskalasi_list.html
│       └── rating.html
├── barang/                   # Modul barang hilang & temuan
│   ├── models.py             # BarangTemuan, LaporanKehilangan, Klaim, SerahTerima
│   ├── views.py              # Input barang, papan temuan, klaim, verifikasi, serah terima
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   └── templates/barang/
│       ├── form.html
│       ├── list.html
│       ├── detail.html
│       ├── papan_temuan.html
│       ├── laporan_kehilangan_form.html
│       ├── laporan_kehilangan_list.html
│       ├── laporan_kehilangan_detail.html
│       ├── klaim_form.html
│       ├── klaim_list.html
│       ├── klaim_detail.html
│       ├── verifikasi_klaim.html
│       └── serah_terima_form.html
├── templates/                # Template global
│   ├── base.html
│   ├── dashboard.html
│   └── registration/login.html
├── static/                   # Aset statis
│   ├── css/style.css
│   ├── js/
│   └── images/
└── media/                    # Unggahan pengguna
```

## Peran Pengguna (Role)

| Role | Kode | Hak Akses |
|------|------|-----------|
| Pelapor | `pelapor` | Buat pengaduan (anonim opsi), lapor barang hilang, lihat papan temuan, ajukan klaim, rating |
| Petugas Penanganan Pengaduan | `petugas_pengaduan` | Tindak lanjuti pengaduan, ubah status, eskalasi ke kepala |
| Petugas Barang Hilang/Temuan | `petugas_barang` | Input barang temuan, verifikasi klaim, serah terima barang |
| Kepala Madrasah / Pimpinan | `kepala_madrasah` | Pantau eskalasi, statistik keseluruhan |
| Admin / TU | `admin` | Kelola pengguna, kategori, akses penuh ke admin Django |

## Cara Instalasi & Menjalankan Secara Lokal

### 1. Persyaratan
Pastikan Python 3.10+ telah terinstal.

### 2. Buat virtual environment dan aktifkan

```powershell
cd E:\PROYEK E4\Pengaduan\pengaduan_madrasah
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Instal dependensi

```powershell
pip install -r requirements.txt
```

### 4. Migrasi database & buat superuser

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 5. Jalankan server development

```powershell
python manage.py runserver
```

Buka browser di: `http://127.0.0.1:8000/`

Admin Django: `http://127.0.0.1:8000/admin/`

### Akun Default (hasil createsuperuser contoh)
- Username: `admin`
- Password: `admin123` (ganti setelah login pertama kali)

## Alur Kerja Singkat

1. **Login** → sistem mengarahkan ke dashboard sesuai role.
2. **Pelapor** membuat pengaduan (dengan opsi anonim) atau lapor barang hilang/ditemukan.
3. **Petugas Pengaduan** menindaklanjuti pengaduan, mengubah status, atau mengeskalasi ke Kepala Madrasah.
4. **Petugas Barang** memverifikasi klaim kepemilikan dan mencatat serah terima barang dengan foto bukti.
5. **Kepala Madrasah** memantau kasus eskalasi dan statistik.
6. **Admin** mengelola pengguna, kategori, dan pengaturan sistem.

## Catatan Keamanan (berdasarkan workflow)

- Opsi anonim hanya untuk pengaduan; identitas tetap tersimpan di database untuk audit.
- Laporan barang hilang/ditemukan wajib identitas asli.
- Verifikasi kepemilikan barang wajib dilakukan sebelum serah terima.
- Setiap perubahan status mencatat siapa dan kapan (audit trail via `LogTindakLanjutPengaduan`).
- Hak akses dibatasi per role (RBAC) melalui `RoleRequiredMixin`.

## Fitur Utama

- ✅ Autentikasi & manajemen sesi (login/logout)
- ✅ Role-Based Access Control (5 role)
- ✅ CRUD pengaduan (create, read, update, delete)
- ✅ CRUD barang temuan & laporan kehilangan
- ✅ Klaim & verifikasi kepemilikan barang
- ✅ Serah terima barang dengan foto bukti & tanda tangan digital
- ✅ Audit trail setiap perubahan status
- ✅ Papan barang temuan publik dengan pencarian & filter
- ✅ Dashboard berbeda per role
- ✅ Rating kepuasan penyelesaian pengaduan
- ✅ Validasi form (frontend HTML5 + backend Django)
- ✅ Penanganan error & pesan flash (messages)

## Lisensi

Dibangun untuk kebutuhan akademik madrasah. Silakan dikembangkan lebih lanjut.
