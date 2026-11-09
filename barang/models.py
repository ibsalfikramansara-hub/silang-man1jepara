"""
Model modul Barang Hilang & Temuan.

Termasuk entitas LokasiPosBarang, BarangTemuan, LaporanKehilangan,
KlaimBarang, dan SerahTerimaBarang dengan alur status sesuai state diagram.
"""
from django.conf import settings
from django.db import models


class LokasiPosBarang(models.Model):
    """Titik pengumpulan barang temuan fisik di madrasah."""

    nama = models.CharField(max_length=100, unique=True)
    lokasi = models.CharField(max_length=200)
    petugas_penanggung_jawab = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'petugas_barang'},
        related_name='pos_dikelola',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Lokasi / Pos Barang'
        verbose_name_plural = 'Lokasi / Pos Barang'
        ordering = ['nama']

    def __str__(self):
        return self.nama


class BarangTemuan(models.Model):
    """Barang yang ditemukan dan diserahkan ke petugas."""

    STATUS_DILAPORKAN = 'dilaporkan'
    STATUS_DIPUBLIKASIKAN = 'dipublikasikan'
    STATUS_DIKLAIM_MENUNGGAU_VERIFIKASI = 'diklaim_menunggu_verifikasi'
    STATUS_TERVERIFIKASI_DISERAHkan = 'terverifikasi_diserahkan'
    STATUS_KLAIM_DITOLAK = 'klaim_ditolak'
    STATUS_SELESAI = 'selesai'

    STATUS_CHOICES = [
        (STATUS_DILAPORKAN, 'Dilaporkan'),
        (STATUS_DIPUBLIKASIKAN, 'Dipublikasikan'),
        (STATUS_DIKLAIM_MENUNGGAU_VERIFIKASI, 'Diklaim (Menunggu Verifikasi)'),
        (STATUS_TERVERIFIKASI_DISERAHkan, 'Terverifikasi & Diserahkan'),
        (STATUS_KLAIM_DITOLAK, 'Klaim Ditolak'),
        (STATUS_SELESAI, 'Selesai'),
    ]

    nama_barang = models.CharField(max_length=200)
    deskripsi = models.TextField()
    foto = models.ImageField(upload_to='barang_temuan/', blank=True, null=True)
    lokasi_ditemukan = models.CharField(max_length=200)
    tanggal_ditemukan = models.DateField()
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_DILAPORKAN,
    )
    dipublikasikan = models.BooleanField(
        default=False,
        help_text='Tampilkan di Papan Barang Temuan untuk civitas akademika.',
    )
    petugas_input = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='barang_diinput',
    )
    lokasi_pos = models.ForeignKey(
        LokasiPosBarang,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='barang_temuan',
    )
    tanggal_dipublikasikan = models.DateTimeField(null=True, blank=True)
    tanggal_diserahkan = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Barang Temuan'
        verbose_name_plural = 'Barang Temuan'
        ordering = ['-tanggal_ditemukan']

    def __str__(self):
        return f'{self.nama_barang} ({self.get_status_display()})'


class LaporanKehilangan(models.Model):
    """Laporan barang yang hilang oleh pelapor."""

    STATUS_AKTIF = 'aktif'
    STATUS_DITEMUKAN = 'ditemukan'
    STATUS_SELESAI = 'selesai'

    STATUS_CHOICES = [
        (STATUS_AKTIF, 'Aktif'),
        (STATUS_DITEMUKAN, 'Ditemukan (cocok dengan temuan)'),
        (STATUS_SELESAI, 'Selesai'),
    ]

    pelapor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='laporan_kehilangan',
    )
    # Laporan kehilangan WAJIB identitas asli (tidak bisa anonim)
    nama_barang = models.CharField(max_length=200)
    deskripsi = models.TextField()
    foto_referensi = models.ImageField(
        upload_to='kehilangan/',
        blank=True,
        null=True,
        help_text='Foto referensi barang yang hilang (jika ada).',
    )
    lokasi_terakhir_terlihat = models.CharField(max_length=200)
    tanggal_terakhir_terlihat = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AKTIF,
    )
    tanggal_diajukan = models.DateTimeField(auto_now_add=True)
    barang_cocok = models.ForeignKey(
        BarangTemuan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='laporan_kehilangan_cocok',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Laporan Kehilangan'
        verbose_name_plural = 'Laporan Kehilangan'
        ordering = ['-tanggal_diajukan']

    def __str__(self):
        return f'{self.nama_barang} ({self.get_status_display()})'


class KlaimBarang(models.Model):
    """Klaim kepemilikan barang temuan oleh pemilik yang berhak."""

    STATUS_MENUNGGU = 'menunggu'
    STATUS_TERVERIFIKASI = 'terverifikasi'
    STATUS_DITOLAK = 'ditolak'

    STATUS_CHOICES = [
        (STATUS_MENUNGGU, 'Menunggu Verifikasi'),
        (STATUS_TERVERIFIKASI, 'Terverifikasi'),
        (STATUS_DITOLAK, 'Ditolak'),
    ]

    barang_temuan = models.ForeignKey(
        BarangTemuan,
        on_delete=models.CASCADE,
        related_name='klaim',
    )
    pelapor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='klaim_barang',
    )
    alasan_klaim = models.TextField(
        help_text='Alasan mengapa barang ini milik Anda.',
    )
    detail_verifikasi = models.TextField(
        help_text='Ciri khusus barang yang hanya dikenal pemilik asli '
                  '(untuk verifikasi kepemilikan).',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_MENUNGGU,
    )
    petugas_verifikasi = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='klaim_diverifikasi',
    )
    catatan_verifikasi = models.TextField(blank=True)
    tanggal_klaim = models.DateTimeField(auto_now_add=True)
    tanggal_verifikasi = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Klaim Barang'
        verbose_name_plural = 'Klaim Barang'
        ordering = ['-tanggal_klaim']

    def __str__(self):
        return f'Klaim {self.barang_temuan.nama_barang} oleh {self.pelapor.username}'


class SerahTerimaBarang(models.Model):
    """Bukti penyerahan barang ke pemilik sah (foto & tanda tangan digital)."""

    klaim = models.OneToOneField(
        KlaimBarang,
        on_delete=models.CASCADE,
        related_name='serah_terima',
    )
    foto_bukti = models.ImageField(
        upload_to='serah_terima/',
        blank=True,
        null=True,
        help_text='Foto bukti penyerahan barang.',
    )
    tanda_tangan_digital = models.CharField(
        max_length=200,
        blank=True,
        help_text='Nama / tanda tangan digital penerima barang.',
    )
    catatan = models.TextField(blank=True)
    tanggal_serah_terima = models.DateTimeField(auto_now_add=True)
    petugas = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='serah_terima_dicatat',
    )

    class Meta:
        verbose_name = 'Serah Terima Barang'
        verbose_name_plural = 'Serah Terima Barang'

    def __str__(self):
        return f'Serah Terima: {self.klaim.barang_temuan.nama_barang}'
