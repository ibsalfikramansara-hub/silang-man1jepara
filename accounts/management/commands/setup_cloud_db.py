"""
Management command untuk inisialisasi database di lingkungan cloud (production).
Hanya mengisi data awal jika database masih kosong, sehingga aman dijalankan
pada setiap deployment (idempotent).
"""
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from accounts.models import User


class Command(BaseCommand):
    help = 'Inisialisasi database production dengan data awal jika database masih kosong'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Memeriksa status database production...'))
        
        # Cek apakah user admin sudah ada
        admin_exists = User.objects.filter(is_superuser=True).exists()
        total_users = User.objects.count()

        if total_users == 0:
            self.stdout.write(self.style.NOTICE('Database kosong. Memuat data awal dari initial_data.json...'))
            try:
                call_command('loaddata', 'initial_data.json')
                self.stdout.write(self.style.SUCCESS('[OK] Data awal berhasil dimuat ke database cloud.'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Gagal memuat initial_data.json: {e}. Membuat admin manual...'))
                User.objects.create_superuser(
                    username='admin',
                    email='admin@madrasah.sch.id',
                    password=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123'),
                    role=User.ROLE_ADMIN,
                )
                self.stdout.write(self.style.SUCCESS('[OK] Superuser admin berhasil dibuat.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'[OK] Database sudah memiliki {total_users} pengguna. Melewati seed data.'))

        # Pastikan superuser admin selalu memiliki role ROLE_ADMIN
        admin = User.objects.filter(username='admin').first()
        if admin and admin.role != User.ROLE_ADMIN:
            admin.role = User.ROLE_ADMIN
            admin.save()
            self.stdout.write(self.style.SUCCESS('[OK] Role admin diselaraskan ke ROLE_ADMIN.'))
