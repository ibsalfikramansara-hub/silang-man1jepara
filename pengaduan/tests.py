from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from pengaduan.models import KategoriPengaduan, Pengaduan, LogTindakLanjutPengaduan


class PengaduanFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.pelapor = User.objects.create_user(
            username='siswa_ali',
            password='Password123!',
            role=User.ROLE_PELAPOR,
            first_name='Ali',
            last_name='Fikri',
        )
        self.petugas = User.objects.create_user(
            username='petugas_bk',
            password='Password123!',
            role=User.ROLE_PETUGAS_PENGADUAN,
            first_name='Ustadz',
            last_name='Hasan',
        )
        self.kepala = User.objects.create_user(
            username='kepala_madrasah',
            password='Password123!',
            role=User.ROLE_KEPALA_MADRASAH,
            first_name='Drs.',
            last_name='Mansur',
        )
        self.kategori = KategoriPengaduan.objects.create(
            nama='Bimbingan Konseling & Kedisiplinan',
            petugas_penanggung_jawab=self.petugas,
            sla_jam=48,
        )

    def test_pengaduan_creation_and_auto_assign(self):
        self.client.force_login(self.pelapor)
        response = self.client.post(reverse('pengaduan:pengaduan_buat'), {
            'judul': 'Keluhan Interaksi di Asrama',
            'kategori': self.kategori.pk,
            'prioritas': 'sedang',
            'isi_pengaduan': 'Terjadi perselisihan antar santri di asrama lantai 2 kamar 10.',
            'is_anonim': True,
        })
        pengaduan = Pengaduan.objects.first()
        self.assertIsNotNone(pengaduan)
        self.assertRedirects(response, reverse('pengaduan:pengaduan_detail', kwargs={'pk': pengaduan.pk}))
        # Cek auto assign ke petugas kategori
        self.assertEqual(pengaduan.petugas_penanganan, self.petugas)
        self.assertEqual(pengaduan.status, 'diajukan')
        self.assertTrue(pengaduan.is_anonim)

        # Cek audit trail awal tercatat
        self.assertEqual(pengaduan.logs.count(), 1)
        self.assertEqual(pengaduan.logs.first().status_baru, 'diajukan')

    def test_pengaduan_anonim_visibility(self):
        pengaduan = Pengaduan.objects.create(
            judul='Kasus Sensitif Anonim',
            kategori=self.kategori,
            pelapor=self.pelapor,
            is_anonim=True,
            isi_pengaduan='Isi rahasia',
        )
        # Petugas penanganan biasa: identitas anonim tersembunyi
        self.assertFalse(pengaduan.tampilkan_identitas_pelapor(self.petugas))

        # Kepala Madrasah & Admin: identitas anonim dapat dilihat untuk investigasi
        self.assertTrue(pengaduan.tampilkan_identitas_pelapor(self.kepala))

    def test_petugas_action_and_escalate_flow(self):
        pengaduan = Pengaduan.objects.create(
            judul='Fasilitas Rusak',
            kategori=self.kategori,
            pelapor=self.pelapor,
            petugas_penanganan=self.petugas,
            status='diajukan',
            isi_pengaduan='Meja belajar patah',
        )

        # Petugas update status -> dalam_penanganan
        self.client.force_login(self.petugas)
        response = self.client.post(reverse('pengaduan:pengaduan_tindak_lanjuti', kwargs={'pk': pengaduan.pk}), {
            'status': 'dalam_penanganan',
            'petugas_penanganan': self.petugas.pk,
            'catatan_petugas': 'Sedang dikoordinasikan dengan bagian perlengkapan.',
        })
        self.assertRedirects(response, reverse('pengaduan:pengaduan_petugas_detail', kwargs={'pk': pengaduan.pk}))
        pengaduan.refresh_from_db()
        self.assertEqual(pengaduan.status, 'dalam_penanganan')
        self.assertIsNotNone(pengaduan.tanggal_diproses)

        # Petugas eskalasi ke Kepala Madrasah
        response = self.client.post(reverse('pengaduan:pengaduan_eskalasi', kwargs={'pk': pengaduan.pk}), {
            'catatan_petugas': 'Perlu persetujuan anggaran perbaikan besar dari Kepala Madrasah.',
        })
        self.assertRedirects(response, reverse('pengaduan:pengaduan_petugas_detail', kwargs={'pk': pengaduan.pk}))
        pengaduan.refresh_from_db()
        self.assertEqual(pengaduan.status, 'eskalasi')

        # Kepala madrasah memantau halaman eskalasi
        self.client.force_login(self.kepala)
        response = self.client.get(reverse('pengaduan:pengaduan_kepala_eskalasi'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fasilitas Rusak')

        # Petugas selesaikan pengaduan
        self.client.force_login(self.petugas)
        response = self.client.post(reverse('pengaduan:pengaduan_tindak_lanjuti', kwargs={'pk': pengaduan.pk}), {
            'status': 'selesai',
            'petugas_penanganan': self.petugas.pk,
            'catatan_petugas': 'Perbaikan selesai dilaksanakan oleh tim sarpras.',
        })
        self.assertRedirects(response, reverse('pengaduan:pengaduan_petugas_detail', kwargs={'pk': pengaduan.pk}))
        pengaduan.refresh_from_db()
        self.assertEqual(pengaduan.status, 'selesai')
        self.assertIsNotNone(pengaduan.tanggal_selesai)

        # Pelapor memberikan rating kepuasan
        self.client.force_login(self.pelapor)
        response = self.client.post(reverse('pengaduan:pengaduan_rating', kwargs={'pk': pengaduan.pk}), {
            'rating_kepuasan': 5,
            'ulasan_kepuasan': 'Respon sangat cepat dan perbaikan rapi.',
        })
        self.assertRedirects(response, reverse('pengaduan:pengaduan_detail', kwargs={'pk': pengaduan.pk}))
        pengaduan.refresh_from_db()
        self.assertEqual(pengaduan.rating_kepuasan, 5)

    def test_pelapor_update_delete_permission(self):
        pengaduan = Pengaduan.objects.create(
            judul='Salah Tulis Judul',
            kategori=self.kategori,
            pelapor=self.pelapor,
            status='diajukan',
            isi_pengaduan='Akan diubah',
        )
        self.client.force_login(self.pelapor)

        # Edit diizinkan saat status 'diajukan'
        response = self.client.post(reverse('pengaduan:pengaduan_edit', kwargs={'pk': pengaduan.pk}), {
            'judul': 'Judul Sudah Diperbaiki',
            'kategori': self.kategori.pk,
            'prioritas': 'rendah',
            'isi_pengaduan': 'Isi sudah diperbarui.',
        })
        self.assertRedirects(response, reverse('pengaduan:pengaduan_detail', kwargs={'pk': pengaduan.pk}))
        pengaduan.refresh_from_db()
        self.assertEqual(pengaduan.judul, 'Judul Sudah Diperbaiki')

        # Jika sudah 'dalam_penanganan', pelapor dilarang mengedit
        pengaduan.status = 'dalam_penanganan'
        pengaduan.save()
        response = self.client.get(reverse('pengaduan:pengaduan_edit', kwargs={'pk': pengaduan.pk}))
        self.assertRedirects(response, reverse('pengaduan:pengaduan_detail', kwargs={'pk': pengaduan.pk}))

    def test_rbac_petugas_views_restricted_for_pelapor(self):
        self.client.force_login(self.pelapor)
        response = self.client.get(reverse('pengaduan:pengaduan_petugas_list'))
        # Harus terlempar ke dashboard tanpa error 500
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_kategori_crud_by_admin(self):
        admin_user = User.objects.create_superuser(
            username='admin_pengaduan',
            email='adminp@test.com',
            password='Password123!',
            role=User.ROLE_ADMIN,
        )
        self.client.force_login(admin_user)

        # 1. List
        response = self.client.get(reverse('pengaduan:kategori_list'))
        self.assertEqual(response.status_code, 200)

        # 2. Tambah
        response = self.client.post(reverse('pengaduan:kategori_tambah'), {
            'nama': 'Sarana & Prasarana Kelas',
            'deskripsi': 'Keluhan terkait AC, LCD, dan kursi kelas',
            'sla_jam': 24,
            'is_aktif': True,
        })
        self.assertRedirects(response, reverse('pengaduan:kategori_list'))
        kat_baru = KategoriPengaduan.objects.get(nama='Sarana & Prasarana Kelas')
        self.assertEqual(kat_baru.sla_jam, 24)

        # 3. Edit
        response = self.client.post(reverse('pengaduan:kategori_edit', kwargs={'pk': kat_baru.pk}), {
            'nama': 'Sarpras & IT Kelas',
            'deskripsi': 'Keluhan sarana kelas dan laboratorium komputer',
            'sla_jam': 36,
            'is_aktif': True,
        })
        self.assertRedirects(response, reverse('pengaduan:kategori_list'))
        kat_baru.refresh_from_db()
        self.assertEqual(kat_baru.nama, 'Sarpras & IT Kelas')

        # 4. Hapus
        response = self.client.post(reverse('pengaduan:kategori_hapus', kwargs={'pk': kat_baru.pk}))
        self.assertRedirects(response, reverse('pengaduan:kategori_list'))
        self.assertFalse(KategoriPengaduan.objects.filter(nama='Sarpras & IT Kelas').exists())

    def test_kategori_denied_for_pelapor(self):
        self.client.force_login(self.pelapor)
        response = self.client.get(reverse('pengaduan:kategori_list'))
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_laporan_rekap_access(self):
        admin_user = User.objects.create_superuser(
            username='admin_rekap',
            email='adminr@test.com',
            password='Password123!',
            role=User.ROLE_ADMIN,
        )
        # Admin can access
        self.client.force_login(admin_user)
        response = self.client.get(reverse('pengaduan:laporan_rekap'))
        self.assertEqual(response.status_code, 200)

        # Kepala Madrasah can access
        self.client.force_login(self.kepala)
        response = self.client.get(reverse('pengaduan:laporan_rekap'))
        self.assertEqual(response.status_code, 200)

        # Pelapor denied
        self.client.force_login(self.pelapor)
        response = self.client.get(reverse('pengaduan:laporan_rekap'))
        self.assertRedirects(response, reverse('accounts:dashboard'))


