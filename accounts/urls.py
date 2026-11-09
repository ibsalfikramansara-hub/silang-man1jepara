"""URL routing untuk modul Accounts."""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Autentikasi
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),

    # Dashboard & Profil
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/ubah-password/', views.UserSelfPasswordChangeView.as_view(), name='password_change'),

    # Manajemen Pengguna (Admin)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/tambah/', views.UserCreateView.as_view(), name='user_tambah'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:pk>/hapus/', views.UserDeleteView.as_view(), name='user_hapus'),
    path('users/<int:pk>/toggle-aktif/', views.UserToggleActiveView.as_view(), name='user_toggle_aktif'),
    path('users/<int:pk>/reset-password/', views.AdminUserPasswordResetView.as_view(), name='user_reset_password'),
]
