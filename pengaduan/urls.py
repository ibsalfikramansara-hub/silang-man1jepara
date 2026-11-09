"""URL routing untuk modul Pengaduan."""
from django.urls import path
from . import views

app_name = 'pengaduan'

urlpatterns = [
    # Pelapor
    path('buat/', views.PengaduanCreateView.as_view(), name='pengaduan_buat'),
    path('', views.PengaduanListView.as_view(), name='pengaduan_list'),
    path('<int:pk>/', views.PengaduanDetailView.as_view(), name='pengaduan_detail'),
    path('<int:pk>/edit/', views.PengaduanUpdateView.as_view(), name='pengaduan_edit'),
    path('<int:pk>/hapus/', views.PengaduanDeleteView.as_view(), name='pengaduan_hapus'),
    path('<int:pk>/rating/', views.RatingKepuasanView.as_view(), name='pengaduan_rating'),

    # Petugas Penanganan Pengaduan
    path('petugas/', views.PetugasPengaduanListView.as_view(), name='pengaduan_petugas_list'),
    path('petugas/<int:pk>/', views.PetugasPengaduanDetailView.as_view(), name='pengaduan_petugas_detail'),
    path('petugas/<int:pk>/tindak-lanjuti/', views.PengaduanActionView.as_view(), name='pengaduan_tindak_lanjuti'),
    path('petugas/<int:pk>/eskalasi/', views.EskalasiPengaduanView.as_view(), name='pengaduan_eskalasi'),

    # Kepala Madrasah & Laporan
    path('kepala/eskalasi/', views.KepalaMadrasahEskalasiListView.as_view(), name='pengaduan_kepala_eskalasi'),
    path('rekap-laporan/', views.LaporanRekapitulasiView.as_view(), name='laporan_rekap'),

    # Manajemen Kategori Pengaduan (Admin)
    path('kategori/', views.KategoriPengaduanListView.as_view(), name='kategori_list'),
    path('kategori/tambah/', views.KategoriPengaduanCreateView.as_view(), name='kategori_tambah'),
    path('kategori/<int:pk>/edit/', views.KategoriPengaduanUpdateView.as_view(), name='kategori_edit'),
    path('kategori/<int:pk>/hapus/', views.KategoriPengaduanDeleteView.as_view(), name='kategori_hapus'),
]
