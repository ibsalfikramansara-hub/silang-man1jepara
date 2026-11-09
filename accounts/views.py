"""
Views untuk modul Accounts (Autentikasi, Dashboard, Profil, Manajemen Pengguna).

Semua view dilindungi dengan LoginRequiredMixin dan RoleRequiredMixin
untuk memastikan Role-Based Access Control (RBAC) sesuai dokumen workflow.
"""
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.views.generic import (
    TemplateView, ListView, CreateView, UpdateView, DeleteView, DetailView, FormView
)
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .models import User
from .forms import (
    CustomAuthenticationForm, UserCreateForm, UserUpdateForm,
    AdminPasswordResetForm, UserSelfPasswordChangeForm,
)
from pengaduan.models import Pengaduan
from barang.models import BarangTemuan, LaporanKehilangan, KlaimBarang

User = get_user_model()


class RoleRequiredMixin(UserPassesTestMixin):
    """
    Mixin untuk membatasi akses view berdasarkan role pengguna.
    Jika user tidak memiliki role yang diizinkan, akan diarahkan ke dashboard
    dengan pesan error.
    """
    allowed_roles = []

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in self.allowed_roles

    def handle_no_permission(self):
        messages.error(self.request, 'Anda tidak memiliki akses ke halaman ini.')
        return redirect('accounts:dashboard')


class CustomLoginView(LoginView):
    """View login dengan template kustom dan redirect otomatis ke dashboard."""
    form_class = CustomAuthenticationForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')

    def form_invalid(self, form):
        messages.error(self.request, 'Username atau password salah.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """View logout yang mengarahkan kembali ke halaman login."""
    next_page = reverse_lazy('accounts:login')

    def get(self, request, *args, **kwargs):
        """Mendukung logout via tautan GET serta POST standar."""
        return self.post(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Dashboard utama yang menampilkan konten berbeda sesuai role pengguna.
    Template dasar: dashboard.html, dengan section yang bervariasi per role.
    """
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Statistik umum untuk semua role
        context['user'] = user
        context['now'] = timezone.now()

        if user.is_pelapor():
            context['section'] = 'pelapor'
            context['my_pengaduan'] = Pengaduan.objects.filter(
                pelapor=user
            ).order_by('-tanggal_diajukan')[:5]
            context['my_laporan_kehilangan'] = LaporanKehilangan.objects.filter(
                pelapor=user
            ).order_by('-tanggal_diajukan')[:5]
            context['total_pengaduan'] = Pengaduan.objects.filter(pelapor=user).count()
            context['total_selesai'] = Pengaduan.objects.filter(
                pelapor=user, status='selesai'
            ).count()

        elif user.is_petugas_pengaduan():
            context['section'] = 'petugas_pengaduan'
            context['pengaduan_ditangani'] = Pengaduan.objects.filter(
                Q(petugas_penanganan=user) | Q(kategori__petugas_penanggung_jawab=user)
            ).exclude(status='selesai').order_by('-tanggal_diajukan')[:10]
            context['total_ditangani'] = Pengaduan.objects.filter(
                Q(petugas_penanganan=user) | Q(kategori__petugas_penanggung_jawab=user)
            ).exclude(status='selesai').count()
            context['total_selesai_bulan_ini'] = Pengaduan.objects.filter(
                Q(petugas_penanganan=user) | Q(kategori__petugas_penanggung_jawab=user),
                status='selesai',
                tanggal_selesai__month=timezone.now().month,
            ).count()

        elif user.is_petugas_barang():
            context['section'] = 'petugas_barang'
            context['barang_temuan_aktif'] = BarangTemuan.objects.exclude(
                status='selesai'
            ).order_by('-tanggal_ditemukan')[:10]
            context['klaim_menunggu'] = KlaimBarang.objects.filter(
                status='menunggu'
            ).order_by('-tanggal_klaim')[:10]
            context['total_barang_temuan'] = BarangTemuan.objects.count()
            context['total_klaim_menunggu'] = KlaimBarang.objects.filter(
                status='menunggu'
            ).count()

        elif user.is_kepala_madrasah():
            context['section'] = 'kepala_madrasah'
            context['pengaduan_eskalasi'] = Pengaduan.objects.filter(
                status='eskalasi'
            ).order_by('-tanggal_diajukan')[:10]
            context['total_eskalasi'] = Pengaduan.objects.filter(status='eskalasi').count()
            context['total_pengaduan_bulan_ini'] = Pengaduan.objects.filter(
                tanggal_diajukan__month=timezone.now().month
            ).count()

        elif user.is_admin():
            context['section'] = 'admin'
            context['total_users'] = User.objects.count()
            context['total_pengaduan'] = Pengaduan.objects.count()
            context['total_barang_temuan'] = BarangTemuan.objects.count()
            context['users_by_role'] = User.objects.values('role').annotate(
                total=Count('id')
            ).order_by('role')

        return context


class ProfileView(LoginRequiredMixin, DetailView):
    """Halaman profil pengguna yang login."""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self):
        return self.request.user


class UserSelfPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Ganti password mandiri oleh pengguna yang sedang login."""
    form_class = UserSelfPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        messages.success(self.request, 'Password Anda berhasil diperbarui.')
        return super().form_valid(form)


# =============================================================================
# Manajemen Pengguna (Admin only)
# =============================================================================

class UserListView(LoginRequiredMixin, RoleRequiredMixin, ListView):
    """Daftar semua pengguna dengan pencarian dan filter peran (hanya Admin)."""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    allowed_roles = ['admin']
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        q = self.request.GET.get('q', '').strip()
        role = self.request.GET.get('role', '').strip()
        status = self.request.GET.get('status', '').strip()

        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(nip_nisn__icontains=q) |
                Q(email__icontains=q) |
                Q(instansi_unit__icontains=q)
            )
        if role:
            queryset = queryset.filter(role=role)
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['selected_role'] = self.request.GET.get('role', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['roles'] = User.ROLE_CHOICES
        return context


class UserCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    """Tambah pengguna baru (hanya Admin)."""
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        user = form.save(commit=False)
        if form.cleaned_data.get('password'):
            user.set_password(form.cleaned_data['password'])
        user.save()
        messages.success(self.request, f'Pengguna {user.username} berhasil dibuat.')
        return redirect(self.success_url)


class UserUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    """Edit data pengguna (hanya Admin)."""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Pengguna {self.object.username} berhasil diperbarui.')
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    """Nonaktifkan/hapus pengguna (hanya Admin)."""
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')
    allowed_roles = ['admin']

    def form_valid(self, form):
        messages.success(self.request, f'Pengguna {self.object.username} berhasil dihapus.')
        return super().form_valid(form)


class UserToggleActiveView(LoginRequiredMixin, RoleRequiredMixin, DetailView):
    """
    Aktifkan/nonaktifkan akun pengguna (toggle is_active).
    Hanya Admin. Diakses via POST.
    """
    model = User
    allowed_roles = ['admin']

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            messages.error(request, 'Tidak dapat menonaktifkan akun sendiri.')
        else:
            user.is_active = not user.is_active
            user.save()
            status = 'diaktifkan' if user.is_active else 'dinonaktifkan'
            messages.success(request, f'Akun {user.username} berhasil {status}.')
        return redirect('accounts:user_list')


class AdminUserPasswordResetView(LoginRequiredMixin, RoleRequiredMixin, FormView):
    """Admin mereset password akun pengguna lain."""
    template_name = 'accounts/user_reset_password.html'
    form_class = AdminPasswordResetForm
    allowed_roles = ['admin']

    def dispatch(self, request, *args, **kwargs):
        self.target_user = get_object_or_404(User, pk=kwargs.get('pk'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_user'] = self.target_user
        return context

    def form_valid(self, form):
        new_password = form.cleaned_data['new_password']
        self.target_user.set_password(new_password)
        self.target_user.save()
        messages.success(self.request, f'Password pengguna {self.target_user.username} berhasil direset.')
        return redirect('accounts:user_list')
