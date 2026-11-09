from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin untuk model User kustom dengan kolom role."""
    list_display = ('username', 'get_full_name', 'role', 'nip_nisn',
                    'instansi_unit', 'is_verified', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'nip_nisn', 'email')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Role & Identitas Madrasah', {
            'fields': ('role', 'nip_nisn', 'telepon', 'instansi_unit', 'is_verified'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Identitas Madrasah', {
            'fields': ('role', 'nip_nisn', 'telepon', 'instansi_unit', 'is_verified'),
        }),
    )
