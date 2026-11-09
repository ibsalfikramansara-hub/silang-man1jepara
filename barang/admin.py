from django.contrib import admin
from .models import (
    LokasiPosBarang, BarangTemuan, LaporanKehilangan,
    KlaimBarang, SerahTerimaBarang,
)


@admin.register(LokasiPosBarang)
class LokasiPosBarangAdmin(admin.ModelAdmin):
    list_display = ('nama', 'lokasi', 'petugas_penanggung_jawab', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('nama', 'lokasi')


@admin.register(BarangTemuan)
class BarangTemuanAdmin(admin.ModelAdmin):
    list_display = ('nama_barang', 'status', 'dipublikasikan',
                    'petugas_input', 'tanggal_ditemukan')
    list_filter = ('status', 'dipublikasikan', 'tanggal_ditemukan')
    search_fields = ('nama_barang', 'deskripsi', 'lokasi_ditemukan')


@admin.register(LaporanKehilangan)
class LaporanKehilanganAdmin(admin.ModelAdmin):
    list_display = ('nama_barang', 'pelapor', 'status', 'tanggal_diajukan')
    list_filter = ('status', 'tanggal_diajukan')
    search_fields = ('nama_barang', 'deskripsi', 'pelapor__username')


@admin.register(KlaimBarang)
class KlaimBarangAdmin(admin.ModelAdmin):
    list_display = ('barang_temuan', 'pelapor', 'status',
                    'petugas_verifikasi', 'tanggal_klaim')
    list_filter = ('status', 'tanggal_klaim')
    search_fields = ('barang_temuan__nama_barang', 'pelapor__username')


@admin.register(SerahTerimaBarang)
class SerahTerimaBarangAdmin(admin.ModelAdmin):
    list_display = ('klaim', 'petugas', 'tanggal_serah_terima')
    search_fields = ('klaim__barang_temuan__nama_barang',)
