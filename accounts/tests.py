from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User


class AccountsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.com',
            password='Password123!',
            role=User.ROLE_ADMIN,
        )
        self.pelapor_user = User.objects.create_user(
            username='siswa_test',
            email='siswa@test.com',
            password='Password123!',
            role=User.ROLE_PELAPOR,
        )
        self.petugas_user = User.objects.create_user(
            username='petugas_test',
            email='petugas@test.com',
            password='Password123!',
            role=User.ROLE_PETUGAS_PENGADUAN,
        )

    def test_user_roles_and_helpers(self):
        self.assertTrue(self.admin_user.is_admin())
        self.assertFalse(self.admin_user.is_pelapor())
        self.assertTrue(self.admin_user.can_manage_pengaduan())
        self.assertTrue(self.admin_user.can_manage_barang())

        self.assertTrue(self.pelapor_user.is_pelapor())
        self.assertFalse(self.pelapor_user.is_admin())
        self.assertFalse(self.pelapor_user.can_manage_pengaduan())

        self.assertTrue(self.petugas_user.is_petugas_pengaduan())
        self.assertTrue(self.petugas_user.can_manage_pengaduan())
        self.assertFalse(self.petugas_user.can_manage_barang())

    def test_login_flow(self):
        # GET login
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Masuk ke Sistem')
        self.assertContains(response, 'form-control')

        # Invalid login
        response = self.client.post(reverse('accounts:login'), {
            'username': 'siswa_test',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Username atau password salah.')

        # Valid login
        response = self.client.post(reverse('accounts:login'), {
            'username': 'siswa_test',
            'password': 'Password123!',
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_logout_flow_get_and_post(self):
        self.client.force_login(self.pelapor_user)
        # GET logout
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))

        # POST logout
        self.client.force_login(self.pelapor_user)
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))

    def test_dashboard_renders_for_each_role(self):
        # Pelapor
        self.client.force_login(self.pelapor_user)
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['section'], 'pelapor')

        # Petugas
        self.client.force_login(self.petugas_user)
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['section'], 'petugas_pengaduan')

        # Admin
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['section'], 'admin')

    def test_admin_user_crud(self):
        self.client.force_login(self.admin_user)

        # List
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 200)

        # Create user
        response = self.client.post(reverse('accounts:user_tambah'), {
            'username': 'guru_baru',
            'first_name': 'Ahmad',
            'last_name': 'Dahlan',
            'email': 'ahmad@madrasah.sch.id',
            'role': User.ROLE_PELAPOR,
            'nip_nisn': '198501012010011001',
            'telepon': '081234567890',
            'instansi_unit': 'Guru Matematika',
            'password': 'PasswordAhmad123!',
            'is_active': True,
        })
        self.assertRedirects(response, reverse('accounts:user_list'))
        new_user = User.objects.get(username='guru_baru')
        self.assertTrue(new_user.check_password('PasswordAhmad123!'))

        # Update user
        response = self.client.post(reverse('accounts:user_edit', kwargs={'pk': new_user.pk}), {
            'username': 'guru_baru',
            'first_name': 'Ahmad',
            'last_name': 'Dahlan, M.Pd.',
            'email': 'ahmad_updated@madrasah.sch.id',
            'role': User.ROLE_PELAPOR,
            'nip_nisn': '198501012010011001',
            'telepon': '081234567899',
            'instansi_unit': 'Guru Matematika & Wali Kelas',
            'is_active': True,
        })
        self.assertRedirects(response, reverse('accounts:user_list'))
        new_user.refresh_from_db()
        self.assertEqual(new_user.last_name, 'Dahlan, M.Pd.')

        # Toggle Active
        response = self.client.post(reverse('accounts:user_toggle_aktif', kwargs={'pk': new_user.pk}))
        self.assertRedirects(response, reverse('accounts:user_list'))
        new_user.refresh_from_db()
        self.assertFalse(new_user.is_active)

        # Delete user
        response = self.client.post(reverse('accounts:user_hapus', kwargs={'pk': new_user.pk}))
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.assertFalse(User.objects.filter(username='guru_baru').exists())

    def test_non_admin_cannot_access_user_management(self):
        self.client.force_login(self.pelapor_user)
        response = self.client.get(reverse('accounts:user_list'))
        # Should redirect to dashboard cleanly without 500 error
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_self_password_change(self):
        self.client.force_login(self.pelapor_user)
        # GET form
        response = self.client.get(reverse('accounts:password_change'))
        self.assertEqual(response.status_code, 200)

        # POST invalid old password
        response = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'WrongPassword123',
            'new_password1': 'NewSecretPass123!',
            'new_password2': 'NewSecretPass123!',
        })
        self.assertEqual(response.status_code, 200)

        # POST valid password change
        response = self.client.post(reverse('accounts:password_change'), {
            'old_password': 'Password123!',
            'new_password1': 'NewSecretPass123!',
            'new_password2': 'NewSecretPass123!',
        })
        self.assertRedirects(response, reverse('accounts:profile'))
        self.pelapor_user.refresh_from_db()
        self.assertTrue(self.pelapor_user.check_password('NewSecretPass123!'))

    def test_admin_reset_user_password(self):
        self.client.force_login(self.admin_user)
        # GET form
        response = self.client.get(reverse('accounts:user_reset_password', kwargs={'pk': self.pelapor_user.pk}))
        self.assertEqual(response.status_code, 200)

        # POST new password
        response = self.client.post(reverse('accounts:user_reset_password', kwargs={'pk': self.pelapor_user.pk}), {
            'new_password': 'AdminResetPass999!',
            'confirm_password': 'AdminResetPass999!',
        })
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.pelapor_user.refresh_from_db()
        self.assertTrue(self.pelapor_user.check_password('AdminResetPass999!'))

    def test_user_list_search_and_filter(self):
        self.client.force_login(self.admin_user)
        # Search query
        response = self.client.get(reverse('accounts:user_list'), {'q': 'siswa'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'siswa_test')
        self.assertNotContains(response, 'petugas_test')

        # Filter by role
        response = self.client.get(reverse('accounts:user_list'), {'role': User.ROLE_PETUGAS_PENGADUAN})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'petugas_test')
        self.assertNotContains(response, 'siswa_test')


