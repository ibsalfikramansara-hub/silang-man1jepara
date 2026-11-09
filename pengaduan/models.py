"""
Model modul Pengaduan (kritik, saran, dan laporan pelanggaran).

Termasuk entitas KategoriPengaduan, Pengaduan, dan LogTindakLanjutPengaduan
untuk audit trail lengkap setiap perubahan status.
"""
from django.conf import settings
from django.db import models


class KategoriPengaduan(models.Model):
    """Kategori pengaduan dengan petugas penanggung jawab dan SLA."""

    nama = models.CharField(max_length=100, unique=True)
    deskripsi = models.TextField(blank=True)
    petugas_penanggung_jawab = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'petugas_pengaduan'},
        related_name='kategori_ditangani',
        help_text='Petugas yang bertanggung jawab menindaklanjuti kategori ini.',
    )
    sla_jam = models.PositiveIntegerField(
        default=24,
        help_text='Batas waktu tindak lanjut dalam jam.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kategori Pengaduan'
        verbose_name_plural = 'Kategori Pengaduan'
        ordering = ['nama']

    def __str__(self):
        return self.nama


class Pengaduan(models.Model):
    """Entitas pengaduan utama dengan alur status sesuai state diagram."""

    STATUS_DIAJUKAN = 'diajukan'
    STATUS_DALAM_PENANGANAN = 'dalam_penanganan'
    STATUS_ESKALASI = 'eskalasi'
    STATUS_SELESAI = 'selesai'

    STATUS_CHOICES = [
        (STATUS_DIAJUKAN, 'Diajukan'),
        (STATUS_DALAM_PENANGANAN, 'Dalam Penanganan'),
        (STATUS_ESKALASI, 'Eskalasi'),
        (STATUS_SELESAI, 'Selesai'),
    ]

    PRIORITAS_RENDAH = 'rendah'
    PRIORITAS_SEDANG = 'sedang'
    PRIORITAS_TINGGI = 'tinggi'

    PRIORITAS_CHOICES = [
        (PRIORITAS_RENDAH, 'Rendah'),
        (PRIORITAS_SEDANG, 'Sedang'),
        (PRIORITAS_TINGGI, 'Tinggi'),
    ]

    judul = models.CharField(max_length=200)
    kategori = models.ForeignKey(
        KategoriPengaduan,
        on_delete=models.PROTECT,
        related_name='pengaduan',
    )
    pelapor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pengaduan_diajukan',
    )
    # Opsi anonim: identitas disembunyikan dari petugas, tapi tetap tersimpan di DB
    is_anonim = models.BooleanField(default=False)
    isi_pengaduan = models.TextField()
    prioritas = models.CharField(
        max_length=10,
        choices=PRIORITAS_CHOICES,
        default=PRIORITAS_SEDANG,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DIAJUKAN,
    )
    petugas_penanganan = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pengaduan_ditangani',
    )
    catatan_petugas = models.TextField(blank=True)
    tanggal_diajukan = models.DateTimeField(auto_now_add=True)
    tanggal_diproses = models.DateTimeField(null=True, blank=True)
    tanggal_selesai = models.DateTimeField(null=True, blank=True)
    rating_kepuasan = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Rating kepuasan pelapor (1-5).',
    )
    ulasan_kepuasan = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Pengaduan'
        verbose_name_plural = 'Pengaduan'
        ordering = ['-tanggal_diajukan']

    def __str__(self):
        return f'{self.judul} ({self.get_status_display()})'

    def tampilkan_identitas_pelapor(self, user):
        """
        Tentukan apakah identitas pelapor boleh ditampilkan kepada `user`.
        Anonim disembunyikan dari petugas kecuali kepala madrasah/admin
        (untuk investigasi resmi).
        """
        if not self.is_anonim:
            return True
        if user.is_authenticated and (
            user.is_kepala_madrasah() or user.is_admin()
        ):
            return True
        return False


class LogTindakLanjutPengaduan(models.Model):
    """
    Audit trail: setiap perubahan status dan catatan penanganan pengaduan
    tercatat siapa yang mengubah dan kapan.
    """

    pengaduan = models.ForeignKey(
        Pengaduan,
        on_delete=models.CASCADE,
        related_name='logs',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    status_lama = models.CharField(max_length=20, blank=True)
    status_baru = models.CharField(max_length=20)
    catatan = models.TextField(blank=True)
    tanggal = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log Tindak Lanjut Pengaduan'
        verbose_name_plural = 'Log Tindak Lanjut Pengaduan'
        ordering = ['-tanggal']

    def __str__(self):
        return f'{self.pengaduan.judul} -> {self.status_baru} ({self.tanggal})'
