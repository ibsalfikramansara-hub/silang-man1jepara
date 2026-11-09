"""
Model manajemen akun & role untuk aplikasi Pengaduan Madrasah.

Model User kustom memperpanjang AbstractUser Django dengan menambahkan
field 'role' untuk mendukung Role-Based Access Control (RBAC) sesuai
dokumen workflow (5 role: Pelapor, Petugas Pengaduan, Petugas Barang,
Kepala Madrasah, Admin/TU).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Pengguna sistem dengan peran (role) yang menentukan hak akses menu.
    """

    ROLE_PELAPOR = 'pelapor'
    ROLE_PETUGAS_PENGADUAN = 'petugas_pengaduan'
    ROLE_PETUGAS_BARANG = 'petugas_barang'
    ROLE_KEPALA_MADRASAH = 'kepala_madrasah'
    ROLE_ADMIN = 'admin'

    ROLE_CHOICES = [
        (ROLE_PELAPOR, 'Pelapor (Siswa/Guru/Karyawan/Orang Tua)'),
        (ROLE_PETUGAS_PENGADUAN, 'Petugas Penanganan Pengaduan (Kesiswaan/BK)'),
        (ROLE_PETUGAS_BARANG, 'Petugas Barang Hilang/Temuan (TU/Satpam)'),
        (ROLE_KEPALA_MADRASAH, 'Kepala Madrasah / Pimpinan'),
        (ROLE_ADMIN, 'Admin / TU'),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default=ROLE_PELAPOR,
        help_text='Peran pengguna yang menentukan menu dan aksi yang tersedia.',
    )
    nip_nisn = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        unique=True,
        help_text='NIS / NISN / NIP / Nomor identitas instansi.',
    )
    telepon = models.CharField(max_length=20, blank=True, help_text='Nomor telepon kontak.')
    instansi_unit = models.CharField(
        max_length=100,
        blank=True,
        help_text='Kelas / jurusan / bagian / unit kerja di madrasah.',
    )
    is_verified = models.BooleanField(
        default=False,
        help_text='Apakah akun telah diverifikasi oleh admin.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Hindari benturan related_name dengan model User bawaan Django
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_groups',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_permissions',
        related_query_name='custom_user',
    )

    class Meta:
        verbose_name = 'Pengguna'
        verbose_name_plural = 'Pengguna'
        ordering = ['-date_joined']

    # ---- Helper role (untuk pengecekan hak akses di template & view) ----

    def is_pelapor(self):
        return self.role == self.ROLE_PELAPOR and not self.is_superuser

    def is_petugas_pengaduan(self):
        return self.role == self.ROLE_PETUGAS_PENGADUAN

    def is_petugas_barang(self):
        return self.role == self.ROLE_PETUGAS_BARANG

    def is_kepala_madrasah(self):
        return self.role == self.ROLE_KEPALA_MADRASAH

    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def can_manage_pengaduan(self):
        """Petugas pengaduan, kepala madrasah, atau admin dapat mengelola pengaduan."""
        return self.is_superuser or self.role in (
            self.ROLE_PETUGAS_PENGADUAN,
            self.ROLE_KEPALA_MADRASAH,
            self.ROLE_ADMIN,
        )

    def can_manage_barang(self):
        """Petugas barang, kepala madrasah, atau admin dapat mengelola barang."""
        return self.is_superuser or self.role in (
            self.ROLE_PETUGAS_BARANG,
            self.ROLE_KEPALA_MADRASAH,
            self.ROLE_ADMIN,
        )

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'
