"""URL routing untuk modul Barang Hilang & Temuan."""
from django.urls import path
from . import views

app_name = 'barang'

urlpatterns = [
    # Papan Barang Temuan (publik untuk civitas akademika)
    path('papan-temuan/', views.PapanBarangTemuanView.as_view(), name='papan_barang_temuan'),
    path('papan-temuan/<int:pk>/', views.BarangTemuanDetailView.as_view(), name='barang_temuan_detail_public'),
    path('papan-temuan/<int:barang_id>/klaim/', views.KlaimBarangCreateView.as_view(), name='klaim_barang'),

    # Petugas Barang - Manajemen barang temuan
    path('petugas/input/', views.BarangTemuanCreateView.as_view(), name='barang_temuan_input'),
    path('petugas/', views.BarangTemuanListView.as_view(), name='barang_temuan_list'),
    path('petugas/<int:pk>/', views.BarangTemuanDetailView.as_view(), name='barang_temuan_detail'),
    path('petugas/<int:pk>/edit/', views.BarangTemuanUpdateView.as_view(), name='barang_temuan_edit'),
    path('petugas/<int:pk>/toggle-publikasi/', views.BarangTemuanTogglePublikasiView.as_view(), name='barang_temuan_toggle_publikasi'),

    # Laporan Kehilangan (Pelapor)
    path('kehilangan/buat/', views.LaporanKehilanganCreateView.as_view(), name='laporan_kehilangan_buat'),
    path('kehilangan/', views.LaporanKehilanganListView.as_view(), name='barang_laporan_kehilangan_list'),
    path('kehilangan/<int:pk>/', views.LaporanKehilanganDetailView.as_view(), name='barang_laporan_kehilangan_detail'),

    # Klaim Barang
    path('klaim/', views.KlaimBarangListView.as_view(), name='barang_klaim_list'),
    path('klaim/<int:pk>/', views.KlaimBarangDetailView.as_view(), name='barang_klaim_detail'),

    # Verifikasi & Serah Terima (Petugas Barang)
    path('klaim/<int:pk>/verifikasi/', views.VerifikasiKlaimView.as_view(), name='klaim_verifikasi'),
    path('klaim/<int:klaim_id>/serah-terima/', views.SerahTerimaBarangCreateView.as_view(), name='serah_terima_barang'),
    path('klaim/<int:pk>/cetak-tanda-terima/', views.CetakTandaTerimaKlaimView.as_view(), name='klaim_cetak_tanda_terima'),

    # Manajemen Lokasi / Pos Barang (Admin & Petugas Barang)
    path('pos/', views.LokasiPosBarangListView.as_view(), name='pos_list'),
    path('pos/tambah/', views.LokasiPosBarangCreateView.as_view(), name='pos_tambah'),
    path('pos/<int:pk>/edit/', views.LokasiPosBarangUpdateView.as_view(), name='pos_edit'),
    path('pos/<int:pk>/hapus/', views.LokasiPosBarangDeleteView.as_view(), name='pos_hapus'),
]
