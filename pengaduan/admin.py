from django.contrib import admin
from .models import KategoriPengaduan, Pengaduan, LogTindakLanjutPengaduan


@admin.register(KategoriPengaduan)
class KategoriPengaduanAdmin(admin.ModelAdmin):
    list_display = ('nama', 'petugas_penanggung_jawab', 'sla_jam', 'is_active')
    list_filter = ('is_active', 'petugas_penanggung_jawab')
    search_fields = ('nama', 'deskripsi')


@admin.register(Pengaduan)
class PengaduanAdmin(admin.ModelAdmin):
    list_display = ('judul', 'kategori', 'pelapor', 'is_anonim', 'status',
                    'prioritas', 'petugas_penanganan', 'tanggal_diajukan')
    list_filter = ('status', 'prioritas', 'is_anonim', 'kategori')
    search_fields = ('judul', 'isi_pengaduan', 'pelapor__username')
    date_hierarchy = 'tanggal_diajukan'


@admin.register(LogTindakLanjutPengaduan)
class LogTindakLanjutPengaduanAdmin(admin.ModelAdmin):
    list_display = ('pengaduan', 'user', 'status_lama', 'status_baru', 'tanggal')
    list_filter = ('status_baru', 'tanggal')
    search_fields = ('pengaduan__judul', 'catatan')
