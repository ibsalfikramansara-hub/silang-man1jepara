"""Konfigurasi URL root proyek pengaduan madrasah."""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', RedirectView.as_view(url='dashboard/', permanent=False)),  # Arahkan root ke dashboard
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),          # Login, logout, profil, dashboard
    path('pengaduan/', include('pengaduan.urls')),  # Modul pengaduan
    path('barang/', include('barang.urls')),       # Modul barang temuan & kehilangan
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
