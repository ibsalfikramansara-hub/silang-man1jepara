"""
Views untuk modul Pengaduan (kritik, saran, dan laporan pelanggaran).

Termasuk alur lengkap: Pelapor membuat pengaduan, Petugas menindaklanjuti,
Kepala Madrasah menangani eskalasi, serta rating kepuasan penyelesaian.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import HttpResponseForbidden
from datetime import datetime

from .models import KategoriPengaduan, Pengaduan, LogTindakLanjutPengaduan
from .forms import (
    PengaduanForm, PengaduanActionForm,
    EskalasiPengaduanForm, RatingKepuasanForm,
    KategoriPengaduanForm,
)
from accounts.views import RoleRequiredMixin


def petugas_can_handle(petugas, pengaduan):
    """Cek apakah petugas berwenang menindaklanjuti pengaduan ini."""
    if petugas.is_superuser or petugas.is_admin() or petugas.is_kepala_madrasah():
        return True
    if petugas.is_petugas_pengaduan():
        # Jika belum ada petugas penanganan atau penanggung jawab kategori, petugas pengaduan dapat mengambil kasus
        if not pengaduan.petugas_penanganan_id and not (pengaduan.kategori and pengaduan.kategori.petugas_penanggung_jawab_id):
            return True
        return (
            pengaduan.petugas_penanganan_id == petugas.id
            or (pengaduan.kategori and pengaduan.kategori.petugas_penanggung_jawab_id == petugas.id)
        )
    return False


# =============================================================================
# Pelapor Views
# =============================================================================

class PengaduanCreateView(LoginRequiredMixin, CreateView):
    """Pelapor membuat pengaduan baru (dengan opsi anonim)."""
    model = Pengaduan
    form_class = PengaduanForm
    template_name = 'pengaduan/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Buat Pengaduan'
        context['kategori_list'] = KategoriPengaduan.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        form.instance.pelapor = self.request.user
        # Auto-assign ke petugas penanggung jawab kategori jika belum ditetapkan
        if form.instance.kategori and form.instance.kategori.petugas_penanggung_jawab:
            form.instance.petugas_penanganan = form.instance.kategori.petugas_penanggung_jawab

        response = super().form_valid(form)
        LogTindakLanjutPengaduan.objects.create(
            pengaduan=self.object,
            user=self.request.user,
            status_baru=self.object.status,
            catatan='Pengaduan diajukan oleh pelapor.'
        )
        messages.success(self.request, 'Pengaduan berhasil diajukan.')
        return response

    def get_success_url(self):
        return reverse_lazy('pengaduan:pengaduan_detail', kwargs={'pk': self.object.pk})


class PengaduanListView(LoginRequiredMixin, ListView):
    """Daftar pengaduan milik pelapor yang login."""
    model = Pengaduan
    template_name = 'pengaduan/list.html'
    context_object_name = 'pengaduan_list'
    paginate_by = 15

    def get_queryset(self):
        return Pengaduan.objects.filter(
            pelapor=self.request.user
        ).order_by('-tanggal_diajukan')


class PengaduanDetailView(LoginRequiredMixin, DetailView):
    """Detail pengaduan dengan log tindak lanjut."""
    model = Pengaduan
    template_name = 'pengaduan/detail.html'
    context_object_name = 'pengaduan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = self.object.logs.all()
        context['bisa_diubah'] = (
            self.object.pelapor == self.request.user
            and self.object.status == 'diajukan'
        )
        context['tampilkan_identitas'] = self.object.tampilkan_identitas_pelapor(
            self.request.user
        )
        return context


class PengaduanUpdateView(LoginRequiredMixin, UpdateView):
    """Pengeditan pengaduan (hanya pelapor sendiri, status masih 'diajukan')."""
    model = Pengaduan
    form_class = PengaduanForm
    template_name = 'pengaduan/form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.pelapor != request.user or obj.status != 'diajukan':
            messages.error(request, 'Pengaduan tidak dapat diubah.')
            return redirect('pengaduan:pengaduan_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Ubah Pengaduan'
        return context

    def get_success_url(self):
        messages.success(self.request, 'Pengaduan berhasil diperbarui.')
        return reverse_lazy('pengaduan:pengaduan_detail', kwargs={'pk': self.object.pk})


class PengaduanDeleteView(LoginRequiredMixin, DeleteView):
    """Menghapus pengaduan (hanya pelapor sendiri, status masih 'diajukan')."""
    model = Pengaduan
    template_name = 'pengaduan/confirm_delete.html'
    success_url = reverse_lazy('pengaduan:pengaduan_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.pelapor != request.user or obj.status != 'diajukan':
            messages.error(request, 'Pengaduan tidak dapat dihapus.')
            return redirect('pengaduan:pengaduan_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Pengaduan berhasil dihapus.')
        return super().form_valid(form)


# =============================================================================
# Petugas Penanganan Pengaduan Views
# =============================================================================

class PetugasPengaduanListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Daftar pengaduan yang ditangani petugas (Petugas Pengaduan / Kepala / Admin)."""
    model = Pengaduan
    template_name = 'pengaduan/petugas_list.html'
    context_object_name = 'pengaduan_list'
    allowed_roles = ['petugas_pengaduan', 'admin', 'kepala_madrasah']
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_admin() or user.is_kepala_madrasah():
            return Pengaduan.objects.all().order_by('-tanggal_diajukan')
        return Pengaduan.objects.filter(
            Q(petugas_penanganan=user) | Q(kategori__petugas_penanggung_jawab=user)
        ).order_by('-tanggal_diajukan')


class PetugasPengaduanDetailView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    """Detail pengaduan untuk petugas dengan opsi tindak lanjuti."""
    model = Pengaduan
    template_name = 'pengaduan/petugas_detail.html'
    context_object_name = 'pengaduan'
    allowed_roles = ['petugas_pengaduan', 'admin', 'kepala_madrasah']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = self.object.logs.all()
        context['bisa_ditindaklanjuti'] = petugas_can_handle(
            self.request.user, self.object
        )
        context['tampilkan_identitas'] = self.object.tampilkan_identitas_pelapor(
            self.request.user
        )
        return context


class PengaduanActionView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """
    Petugas mengubah status, catatan, dan petugas penanganan pengaduan.
    Digunakan dari halaman detail petugas.
    """
    model = Pengaduan
    form_class = PengaduanActionForm
    template_name = 'pengaduan/action_form.html'
    allowed_roles = ['petugas_pengaduan', 'admin', 'kepala_madrasah']

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not petugas_can_handle(request.user, obj):
            return HttpResponseForbidden('Anda tidak berwenang menindaklanjuti pengaduan ini.')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        status_lama = self.get_object().status
        status_baru = form.cleaned_data.get('status')
        catatan = form.cleaned_data.get('catatan_petugas', '')

        self.object = form.save()

        # Catat waktu diproses / selesai
        now = timezone.now()
        if status_baru == 'dalam_penanganan' and not self.object.tanggal_diproses:
            self.object.tanggal_diproses = now
        if status_baru == 'selesai' and not self.object.tanggal_selesai:
            self.object.tanggal_selesai = now
        self.object.save()

        LogTindakLanjutPengaduan.objects.create(
            pengaduan=self.object,
            user=self.request.user,
            status_lama=status_lama,
            status_baru=status_baru,
            catatan=catatan,
        )
        messages.success(self.request, f'Status pengaduan diubah menjadi {self.object.get_status_display()}.')
        return redirect('pengaduan:pengaduan_petugas_detail', pk=self.object.pk)


class EskalasiPengaduanView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """
    Petugas mengeskalasi pengaduan ke Kepala Madrasah (status = eskalasi).
    """
    model = Pengaduan
    form_class = EskalasiPengaduanForm
    template_name = 'pengaduan/escalate_form.html'
    allowed_roles = ['petugas_pengaduan', 'admin']

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not petugas_can_handle(request.user, obj):
            return HttpResponseForbidden('Anda tidak berwenang mengeskalasi pengaduan ini.')
        if obj.status == 'selesai':
            messages.error(request, 'Pengaduan yang sudah selesai tidak dapat dieskalasi.')
            return redirect('pengaduan:pengaduan_petugas_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        obj = form.save(commit=False)
        status_lama = obj.status
        obj.status = 'eskalasi'
        obj.save()

        LogTindakLanjutPengaduan.objects.create(
            pengaduan=obj,
            user=self.request.user,
            status_lama=status_lama,
            status_baru='eskalasi',
            catatan=form.cleaned_data.get('catatan_petugas', 'Dieskalasi ke Kepala Madrasah.'),
        )
        messages.success(self.request, 'Pengaduan berhasil dieskalasi ke Kepala Madrasah.')
        return redirect('pengaduan:pengaduan_petugas_detail', pk=obj.pk)


# =============================================================================
# Kepala Madrasah Views
# =============================================================================

class KepalaMadrasahEskalasiListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Daftar pengaduan yang dieskalasi (Kepala Madrasah)."""
    model = Pengaduan
    template_name = 'pengaduan/kepala_eskalasi_list.html'
    context_object_name = 'pengaduan_list'
    allowed_roles = ['kepala_madrasah', 'admin']
    paginate_by = 20

    def get_queryset(self):
        return Pengaduan.objects.filter(status='eskalasi').order_by('-tanggal_diajukan')


# =============================================================================
# Rating Kepuasan (Pelapor)
# =============================================================================

class RatingKepuasanView(LoginRequiredMixin, UpdateView):
    """Pelapor memberi rating kepuasan pada pengaduan yang selesai."""
    model = Pengaduan
    form_class = RatingKepuasanForm
    template_name = 'pengaduan/rating.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.pelapor != request.user or obj.status != 'selesai':
            messages.error(request, 'Rating hanya dapat diberikan pada pengaduan yang sudah selesai.')
            return redirect('pengaduan:pengaduan_detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Terima kasih atas rating dan ulasan Anda.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('pengaduan:pengaduan_detail', kwargs={'pk': self.object.pk})


# =============================================================================
# Rekapitulasi Laporan Terpadu (Kepala Madrasah & Admin)
# =============================================================================

class LaporanRekapitulasiView(LoginRequiredMixin, RoleRequiredMixin, TemplateView):
    """
    Laporan rekapitulasi periodik pengaduan dan barang hilang/temuan
    yang siap cetak dan diunduh (Kepala Madrasah & Admin).
    """
    template_name = 'pengaduan/laporan_rekap.html'
    allowed_roles = ['kepala_madrasah', 'admin']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from barang.models import BarangTemuan, LaporanKehilangan, KlaimBarang

        dari_tgl = self.request.GET.get('dari', '')
        sampai_tgl = self.request.GET.get('sampai', '')

        p_qs = Pengaduan.objects.all()
        b_qs = BarangTemuan.objects.all()
        l_qs = LaporanKehilangan.objects.all()
        k_qs = KlaimBarang.objects.all()

        if dari_tgl:
            try:
                dt_from = datetime.strptime(dari_tgl, '%Y-%m-%d')
                p_qs = p_qs.filter(tanggal_diajukan__date__gte=dt_from)
                b_qs = b_qs.filter(tanggal_ditemukan__gte=dt_from)
                l_qs = l_qs.filter(tanggal_diajukan__date__gte=dt_from)
                k_qs = k_qs.filter(tanggal_klaim__date__gte=dt_from)
            except ValueError:
                pass

        if sampai_tgl:
            try:
                dt_to = datetime.strptime(sampai_tgl, '%Y-%m-%d')
                p_qs = p_qs.filter(tanggal_diajukan__date__lte=dt_to)
                b_qs = b_qs.filter(tanggal_ditemukan__lte=dt_to)
                l_qs = l_qs.filter(tanggal_diajukan__date__lte=dt_to)
                k_qs = k_qs.filter(tanggal_klaim__date__lte=dt_to)
            except ValueError:
                pass

        # Statistik Pengaduan
        context['total_pengaduan'] = p_qs.count()
        context['pengaduan_selesai'] = p_qs.filter(status='selesai').count()
        context['pengaduan_proses'] = p_qs.filter(status='dalam_penanganan').count()
        context['pengaduan_eskalasi'] = p_qs.filter(status='eskalasi').count()
        context['pengaduan_diajukan'] = p_qs.filter(status='diajukan').count()
        context['avg_rating'] = p_qs.filter(rating_kepuasan__isnull=False).aggregate(avg=Avg('rating_kepuasan'))['avg']
        context['pengaduan_list'] = p_qs.order_by('-tanggal_diajukan')[:50]

        # Statistik Barang
        context['total_barang_temuan'] = b_qs.count()
        context['barang_selesai'] = b_qs.filter(status='selesai').count()
        context['barang_aktif'] = b_qs.exclude(status='selesai').count()
        context['total_laporan_kehilangan'] = l_qs.count()
        context['total_klaim'] = k_qs.count()
        context['klaim_terverifikasi'] = k_qs.filter(status='terverifikasi').count()
        context['barang_list'] = b_qs.order_by('-tanggal_ditemukan')[:50]

        context['dari_tgl'] = dari_tgl
        context['sampai_tgl'] = sampai_tgl
        context['tgl_cetak'] = timezone.now()
        return context


# =============================================================================
# Manajemen Kategori Pengaduan (Admin only)
# =============================================================================

class KategoriPengaduanListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Daftar Kategori Pengaduan di antarmuka Web UI."""
    model = KategoriPengaduan
    template_name = 'pengaduan/kategori_list.html'
    context_object_name = 'kategori_list'
    allowed_roles = ['admin']

    def get_queryset(self):
        return KategoriPengaduan.objects.all().order_by('nama')


class KategoriPengaduanCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """Tambah Kategori Pengaduan baru."""
    model = KategoriPengaduan
    form_class = KategoriPengaduanForm
    template_name = 'pengaduan/kategori_form.html'
    success_url = reverse_lazy('pengaduan:kategori_list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Kategori "{form.instance.nama}" berhasil ditambahkan.')
        return super().form_valid(form)


class KategoriPengaduanUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """Edit Kategori Pengaduan."""
    model = KategoriPengaduan
    form_class = KategoriPengaduanForm
    template_name = 'pengaduan/kategori_form.html'
    success_url = reverse_lazy('pengaduan:kategori_list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Kategori "{form.instance.nama}" berhasil diperbarui.')
        return super().form_valid(form)


class KategoriPengaduanDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    """Hapus Kategori Pengaduan."""
    model = KategoriPengaduan
    template_name = 'pengaduan/kategori_confirm_delete.html'
    success_url = reverse_lazy('pengaduan:kategori_list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Kategori "{self.object.nama}" berhasil dihapus.')
        return super().form_valid(form)

