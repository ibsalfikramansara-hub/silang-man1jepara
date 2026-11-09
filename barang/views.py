"""
Views untuk modul Barang Hilang & Temuan.

Termasuk: input barang temuan (Petugas Barang), papan barang temuan (publik),
laporan kehilangan (Pelapor), klaim barang, verifikasi kepemilikan, dan
serah terima barang.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django import forms

from .models import (
    LokasiPosBarang, BarangTemuan, LaporanKehilangan,
    KlaimBarang, SerahTerimaBarang,
)
from .forms import (
    BarangTemuanForm, BarangTemuanUpdateForm, LaporanKehilanganForm,
    KlaimBarangForm, KlaimActionForm, SerahTerimaBarangForm,
    LokasiPosBarangForm,
)
from accounts.views import RoleRequiredMixin


def petugas_barang_can_handle(user):
    return user.is_superuser or user.is_admin() or user.is_kepala_madrasah() or user.is_petugas_barang()


# =============================================================================
# Barang Temuan - Petugas Barang Input & Kelola
# =============================================================================

class BarangTemuanCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """Petugas Barang input barang yang ditemukan dan diserahkan."""
    model = BarangTemuan
    form_class = BarangTemuanForm
    template_name = 'barang/form.html'
    allowed_roles = ['petugas_barang', 'admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Input Barang Temuan'
        context['lokasi_list'] = LokasiPosBarang.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        form.instance.petugas_input = self.request.user
        if form.cleaned_data.get('dipublikasikan'):
            form.instance.tanggal_dipublikasikan = timezone.now()
        response = super().form_valid(form)
        messages.success(self.request, 'Barang temuan berhasil dicatat.')
        return response

    def get_success_url(self):
        return reverse_lazy('barang:barang_temuan_detail', kwargs={'pk': self.object.pk})


class BarangTemuanListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Daftar barang temuan untuk Petugas Barang."""
    model = BarangTemuan
    template_name = 'barang/list.html'
    context_object_name = 'barang_list'
    allowed_roles = ['petugas_barang', 'admin', 'kepala_madrasah']
    paginate_by = 20

    def get_queryset(self):
        return BarangTemuan.objects.all().order_by('-tanggal_ditemukan')


class BarangTemuanDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    """Detail barang temuan (dapat diakses petugas maupun civitas publik)."""
    model = BarangTemuan
    template_name = 'barang/detail.html'
    context_object_name = 'barang'
    allowed_roles = ['petugas_barang', 'admin', 'kepala_madrasah']

    def test_func(self):
        # Jika diakses lewat rute publik papan temuan, seluruh pengguna terautentikasi diizinkan
        if self.request.resolver_match and self.request.resolver_match.url_name == 'barang_temuan_detail_public':
            return self.request.user.is_authenticated
        return super().test_func()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['klaim_list'] = self.object.klaim.all().order_by('-tanggal_klaim')
        context['bisa_verifikasi'] = petugas_barang_can_handle(self.request.user)
        return context


class BarangTemuanUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """Edit data barang temuan (Petugas Barang)."""
    model = BarangTemuan
    form_class = BarangTemuanUpdateForm
    template_name = 'barang/form.html'
    allowed_roles = ['petugas_barang', 'admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Ubah Barang Temuan'
        context['lokasi_list'] = LokasiPosBarang.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        if form.cleaned_data.get('dipublikasikan') and not self.object.tanggal_dipublikasikan:
            form.instance.tanggal_dipublikasikan = timezone.now()
        if form.cleaned_data.get('status') == 'terverifikasi_diserahkan' and not self.object.tanggal_diserahkan:
            form.instance.tanggal_diserahkan = timezone.now()
        messages.success(self.request, 'Barang temuan berhasil diperbarui.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('barang:barang_temuan_detail', kwargs={'pk': self.object.pk})


# =============================================================================
# Papan Barang Temuan (Publik untuk Civitas Akademika)
# =============================================================================

class PapanBarangTemuanView(ListView):
    """
    Papan barang temuan yang dipublikasikan. Akses untuk semua pengguna
    yang login (civitas akademika) untuk mencari barang yang hilang.
    """
    model = BarangTemuan
    template_name = 'barang/papan_temuan.html'
    context_object_name = 'barang_list'
    paginate_by = 20

    def get_queryset(self):
        queryset = BarangTemuan.objects.filter(
            dipublikasikan=True
        ).exclude(status__in=['terverifikasi_diserahkan', 'selesai']).order_by('-tanggal_ditemukan')

        q = self.request.GET.get('q')
        lokasi = self.request.GET.get('lokasi')
        if q:
            queryset = queryset.filter(
                Q(nama_barang__icontains=q) | Q(deskripsi__icontains=q) | Q(lokasi_ditemukan__icontains=q)
            )
        if lokasi:
            queryset = queryset.filter(lokasi_ditemukan__icontains=lokasi)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lokasi_list'] = LokasiPosBarang.objects.filter(is_active=True)
        context['query'] = self.request.GET.get('q', '')
        context['lokasi'] = self.request.GET.get('lokasi', '')
        return context


# =============================================================================
# Laporan Kehilangan - Pelapor
# =============================================================================

class LaporanKehilanganCreateView(LoginRequiredMixin, CreateView):
    """Pelapor melaporkan barang yang hilang (wajib identitas asli)."""
    model = LaporanKehilangan
    form_class = LaporanKehilanganForm
    template_name = 'barang/laporan_kehilangan_form.html'

    def form_valid(self, form):
        form.instance.pelapor = self.request.user
        # Coba cari kecocokan otomatis dengan barang temuan yang dipublikasikan dan aktif
        q_nama = form.cleaned_data.get('nama_barang', '')
        q_lokasi = form.cleaned_data.get('lokasi_terakhir_terlihat', '')
        cocok = BarangTemuan.objects.filter(
            dipublikasikan=True,
            status__in=['dilaporkan', 'dipublikasikan'],
            nama_barang__icontains=q_nama,
        )
        if q_lokasi:
            cocok = cocok.filter(lokasi_ditemukan__icontains=q_lokasi)
        cocok = cocok.first()
        if cocok:
            form.instance.barang_cocok = cocok
            messages.info(
                self.request,
                f'Ditemukan kecocokan dengan barang temuan "{cocok.nama_barang}". '
                'Silakan ajukan klaim jika barang ini milik Anda.'
            )
        response = super().form_valid(form)
        messages.success(self.request, 'Laporan kehilangan berhasil diajukan.')
        return response

    def get_success_url(self):
        return reverse_lazy('barang:barang_laporan_kehilangan_detail', kwargs={'pk': self.object.pk})


class LaporanKehilanganListView(LoginRequiredMixin, ListView):
    """Daftar laporan kehilangan milik pelapor yang login."""
    model = LaporanKehilangan
    template_name = 'barang/laporan_kehilangan_list.html'
    context_object_name = 'laporan_list'
    paginate_by = 15

    def get_queryset(self):
        return LaporanKehilangan.objects.filter(
            pelapor=self.request.user
        ).order_by('-tanggal_diajukan')


class LaporanKehilanganDetailView(LoginRequiredMixin, DetailView):
    """Detail laporan kehilangan."""
    model = LaporanKehilangan
    template_name = 'barang/laporan_kehilangan_detail.html'
    context_object_name = 'laporan'


# =============================================================================
# Klaim Barang
# =============================================================================

class KlaimBarangCreateView(LoginRequiredMixin, CreateView):
    """Pelapor mengajukan klaim kepemilikan pada barang temuan."""
    model = KlaimBarang
    form_class = KlaimBarangForm
    template_name = 'barang/klaim_form.html'

    def dispatch(self, request, *args, **kwargs):
        barang_id = kwargs.get('barang_id')
        if barang_id:
            self.barang_temuan = get_object_or_404(BarangTemuan, id=barang_id)
            # Cegah klaim duplikat yang masih menunggu
            if KlaimBarang.objects.filter(
                barang_temuan=self.barang_temuan,
                pelapor=request.user,
                status='menunggu',
            ).exists():
                messages.warning(request, 'Anda sudah mengajukan klaim untuk barang ini.')
                return redirect('barang:barang_temuan_detail_public', pk=barang_id)
        else:
            self.barang_temuan = None
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'barang_temuan') and self.barang_temuan:
            context['barang_temuan'] = self.barang_temuan
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if hasattr(self, 'barang_temuan') and self.barang_temuan:
            form.fields['barang_temuan'].initial = self.barang_temuan
            form.fields['barang_temuan'].widget = forms.HiddenInput()
            form.fields['barang_temuan'].required = False
        return form

    def form_valid(self, form):
        form.instance.pelapor = self.request.user
        if hasattr(self, 'barang_temuan') and self.barang_temuan:
            form.instance.barang_temuan = self.barang_temuan
        response = super().form_valid(form)
        # Ubah status barang temuan menjadi diklaim menunggu verifikasi
        bt = form.instance.barang_temuan
        if bt.status != 'diklaim_menunggu_verifikasi':
            bt.status = 'diklaim_menunggu_verifikasi'
            bt.save()
        messages.success(self.request, 'Klaim barang berhasil diajukan. Tunggu verifikasi petugas.')
        return redirect('barang:barang_laporan_kehilangan_list')

    def get_success_url(self):
        return reverse_lazy('barang:barang_laporan_kehilangan_list')


class KlaimBarangListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Daftar klaim yang menunggu verifikasi (Petugas Barang)."""
    model = KlaimBarang
    template_name = 'barang/klaim_list.html'
    context_object_name = 'klaim_list'
    allowed_roles = ['petugas_barang', 'admin']
    paginate_by = 20

    def get_queryset(self):
        return KlaimBarang.objects.filter(status='menunggu').order_by('-tanggal_klaim')


class KlaimBarangDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    """Detail klaim dengan opsi verifikasi (Petugas Barang)."""
    model = KlaimBarang
    template_name = 'barang/klaim_detail.html'
    context_object_name = 'klaim'
    allowed_roles = ['petugas_barang', 'admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['serah_terima'] = self.object.serah_terima
        except SerahTerimaBarang.DoesNotExist:
            context['serah_terima'] = None
        return context


# =============================================================================
# Verifikasi Klaim & Serah Terima Barang
# =============================================================================

class VerifikasiKlaimView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """
    Petugas Barang memverifikasi atau menolak klaim kepemilikan barang.
    """
    model = KlaimBarang
    form_class = KlaimActionForm
    template_name = 'barang/verifikasi_klaim.html'
    allowed_roles = ['petugas_barang', 'admin']

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status != 'menunggu':
            messages.error(request, 'Klaim sudah diproses sebelumnya.')
            return redirect('barang:barang_klaim_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        status_baru = form.cleaned_data.get('status')
        obj.status = status_baru
        obj.petugas_verifikasi = self.request.user
        obj.tanggal_verifikasi = timezone.now()
        obj.save()

        # Update status barang temuan
        bt = obj.barang_temuan
        if status_baru == 'terverifikasi':
            bt.status = 'terverifikasi_diserahkan'
        elif status_baru == 'ditolak':
            bt.status = 'klaim_ditolak'
        bt.save()

        messages.success(
            self.request,
            f'Klaim barang telah {status_baru}.'
        )
        return redirect('barang:barang_klaim_detail', pk=obj.pk)


class SerahTerimaBarangCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """
    Petugas Barang mencatat serah terima barang ke pemilik sah
    setelah klaim terverifikasi.
    """
    model = SerahTerimaBarang
    form_class = SerahTerimaBarangForm
    template_name = 'barang/serah_terima_form.html'
    allowed_roles = ['petugas_barang', 'admin']

    def dispatch(self, request, *args, **kwargs):
        klaim_id = kwargs.get('klaim_id')
        self.klaim = get_object_or_404(KlaimBarang, id=klaim_id)
        if self.klaim.status != 'terverifikasi':
            messages.error(request, 'Serah terima hanya dapat dilakukan pada klaim yang terverifikasi.')
            return redirect('barang:barang_klaim_detail', pk=self.klaim.pk)
        if hasattr(self.klaim, 'serah_terima'):
            messages.warning(request, 'Barang ini sudah diserahkan sebelumnya.')
            return redirect('barang:barang_klaim_detail', pk=self.klaim.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['klaim'] = self.klaim
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['klaim'].initial = self.klaim
        form.fields['klaim'].widget = forms.HiddenInput()
        form.fields['klaim'].required = False
        return form

    def form_valid(self, form):
        form.instance.petugas = self.request.user
        form.instance.klaim = self.klaim
        response = super().form_valid(form)

        # Update status barang temuan dan klaim
        bt = self.klaim.barang_temuan
        bt.status = 'selesai'
        bt.tanggal_diserahkan = timezone.now()
        bt.save()
        self.klaim.status = 'terverifikasi'  # tetap terverifikasi, sudah diserahkan
        self.klaim.save()

        # Update laporan kehilangan terkait jika ada
        LaporanKehilangan.objects.filter(barang_cocok=bt).update(status='selesai')

        messages.success(self.request, 'Serah terima barang berhasil dicatat.')
        return redirect('barang:barang_klaim_detail', pk=self.klaim.pk)

    def get_success_url(self):
        return reverse_lazy('barang:barang_klaim_detail', kwargs={'pk': self.klaim.pk})


# =============================================================================
# Quick Action & Cetak Bukti Serah Terima
# =============================================================================

class BarangTemuanTogglePublikasiView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    """Petugas toggle status publikasi barang temuan."""
    model = BarangTemuan
    allowed_roles = ['petugas_barang', 'admin']

    def post(self, request, *args, **kwargs):
        barang = self.get_object()
        barang.dipublikasikan = not barang.dipublikasikan
        if barang.dipublikasikan and not barang.tanggal_dipublikasikan:
            barang.tanggal_dipublikasikan = timezone.now()
        barang.save()
        status_txt = 'dipublikasikan di Papan Temuan' if barang.dipublikasikan else 'disembunyikan dari Papan Temuan'
        messages.success(request, f'Barang "{barang.nama_barang}" berhasil {status_txt}.')
        return redirect('barang:barang_temuan_list')


class CetakTandaTerimaKlaimView(LoginRequiredMixin, DetailView):
    """
    Format cetak resmi Berita Acara & Tanda Terima Penyerahan Barang Temuan
    antara Petugas dan Pemilik Sah di MAN 1 Jepara.
    """
    model = KlaimBarang
    template_name = 'barang/cetak_tanda_terima.html'
    context_object_name = 'klaim'

    def dispatch(self, request, *args, **kwargs):
        klaim = self.get_object()
        if request.user != klaim.pelapor and not (request.user.is_petugas_barang() or request.user.is_admin() or request.user.is_kepala_madrasah()):
            messages.error(request, 'Anda tidak berwenang mencetak tanda terima ini.')
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['serah_terima'] = self.object.serah_terima
        except SerahTerimaBarang.DoesNotExist:
            context['serah_terima'] = None
        context['tgl_cetak'] = timezone.now()
        return context


# =============================================================================
# Manajemen Lokasi / Pos Barang (Admin & Petugas Barang)
# =============================================================================

class LokasiPosBarangListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Daftar Pos Penitipan Barang Temuan di antarmuka Web UI."""
    model = LokasiPosBarang
    template_name = 'barang/pos_list.html'
    context_object_name = 'pos_list'
    allowed_roles = ['admin', 'petugas_barang']

    def get_queryset(self):
        return LokasiPosBarang.objects.all().order_by('nama')


class LokasiPosBarangCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """Tambah Pos Penitipan Barang baru."""
    model = LokasiPosBarang
    form_class = LokasiPosBarangForm
    template_name = 'barang/pos_form.html'
    success_url = reverse_lazy('barang:pos_list')
    allowed_roles = ['admin', 'petugas_barang']

    def form_valid(self, form):
        messages.success(self.request, f'Pos Penitipan "{form.instance.nama}" berhasil ditambahkan.')
        return super().form_valid(form)


class LokasiPosBarangUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """Edit Pos Penitipan Barang."""
    model = LokasiPosBarang
    form_class = LokasiPosBarangForm
    template_name = 'barang/pos_form.html'
    success_url = reverse_lazy('barang:pos_list')
    allowed_roles = ['admin', 'petugas_barang']

    def form_valid(self, form):
        messages.success(self.request, f'Pos Penitipan "{form.instance.nama}" berhasil diperbarui.')
        return super().form_valid(form)


class LokasiPosBarangDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    """Hapus Pos Penitipan Barang."""
    model = LokasiPosBarang
    template_name = 'barang/pos_confirm_delete.html'
    success_url = reverse_lazy('barang:pos_list')
    allowed_roles = ['admin', 'petugas_barang']

    def form_valid(self, form):
        messages.success(self.request, f'Pos Penitipan "{self.object.nama}" berhasil dihapus.')
        return super().form_valid(form)

