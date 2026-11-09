from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from barang.models import (
    LokasiPosBarang, BarangTemuan, LaporanKehilangan,
    KlaimBarang, SerahTerimaBarang,
)
import datetime


class BarangLifecycleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.pelapor = User.objects.create_user(
            username='siswa_budi',
            password='Password123!',
            role=User.ROLE_PELAPOR,
            first_name='Budi',
            last_name='Santoso',
        )
        self.petugas_barang = User.objects.create_user(
            username='satpam_joko',
            password='Password123!',
            role=User.ROLE_PETUGAS_BARANG,
            first_name='Joko',
            last_name='Susilo',
        )
        self.pos = LokasiPosBarang.objects.create(
            nama='Pos Satpam Gerbang Utama',
            lokasi='Gerbang Depan',
            petugas_penanggung_jawab=self.petugas_barang,
        )

    def test_barang_temuan_dan_papan_temuan(self):
        self.client.force_login(self.petugas_barang)

        # Petugas mencatat barang temuan
        response = self.client.post(reverse('barang:barang_temuan_input'), {
            'nama_barang': 'Kacamata Frame Hitam',
            'deskripsi': 'Kacamata minus merk Rayban dengan kotak biru.',
            'lokasi_ditemukan': 'Perpustakaan Lt. 1',
            'tanggal_ditemukan': datetime.date.today().isoformat(),
            'lokasi_pos': self.pos.pk,
            'dipublikasikan': True,
        })
        barang = BarangTemuan.objects.first()
        self.assertIsNotNone(barang)
        self.assertRedirects(response, reverse('barang:barang_temuan_detail', kwargs={'pk': barang.pk}))
        self.assertTrue(barang.dipublikasikan)

        # Papan temuan publik menampilkan barang
        response = self.client.get(reverse('barang:papan_barang_temuan'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kacamata Frame Hitam')

        # Pelapor mengakses detail publik papan temuan
        self.client.force_login(self.pelapor)
        response = self.client.get(reverse('barang:barang_temuan_detail_public', kwargs={'pk': barang.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kacamata Frame Hitam')

    def test_laporan_kehilangan_auto_match_and_klaim_workflow(self):
        # 1. Petugas menginput barang temuan
        barang = BarangTemuan.objects.create(
            nama_barang='Jam Tangan Casio G-Shock',
            deskripsi='Warna hitam doff dengan strap karet.',
            lokasi_ditemukan='Lapangan Basket',
            tanggal_ditemukan=datetime.date.today(),
            lokasi_pos=self.pos,
            dipublikasikan=True,
            status='dipublikasikan',
            petugas_input=self.petugas_barang,
        )

        # 2. Pelapor membuat laporan kehilangan yang cocok
        self.client.force_login(self.pelapor)
        response = self.client.post(reverse('barang:laporan_kehilangan_buat'), {
            'nama_barang': 'Jam Tangan Casio',
            'deskripsi': 'Jam tangan Casio warna hitam, tertinggal saat olahraga basket.',
            'lokasi_terakhir_terlihat': 'Lapangan Basket',
            'tanggal_terakhir_terlihat': datetime.date.today().isoformat(),
        })
        laporan = LaporanKehilangan.objects.first()
        self.assertIsNotNone(laporan)
        self.assertRedirects(response, reverse('barang:barang_laporan_kehilangan_detail', kwargs={'pk': laporan.pk}))
        # Sistem otomatis mencocokkan
        self.assertEqual(laporan.barang_cocok, barang)

        # 3. Pelapor mengajukan klaim atas barang temuan
        response = self.client.post(reverse('barang:klaim_barang', kwargs={'barang_id': barang.pk}), {
            'alasan_klaim': 'Jam tangan tersebut tertinggal setelah main basket kemarin sore.',
            'detail_verifikasi': 'Di bagian belakang ada goresan tipis dekat tulisan Water Resist 200M.',
        })
        self.assertRedirects(response, reverse('barang:barang_laporan_kehilangan_list'))
        klaim = KlaimBarang.objects.first()
        self.assertIsNotNone(klaim)
        self.assertEqual(klaim.status, 'menunggu')
        barang.refresh_from_db()
        self.assertEqual(barang.status, 'diklaim_menunggu_verifikasi')

        # Cegah klaim ganda yang masih menunggu
        response = self.client.get(reverse('barang:klaim_barang', kwargs={'barang_id': barang.pk}))
        self.assertRedirects(response, reverse('barang:barang_temuan_detail_public', kwargs={'pk': barang.pk}))

        # 4. Petugas memeriksa & memverifikasi klaim
        self.client.force_login(self.petugas_barang)
        response = self.client.get(reverse('barang:barang_klaim_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jam Tangan Casio G-Shock')

        response = self.client.post(reverse('barang:klaim_verifikasi', kwargs={'pk': klaim.pk}), {
            'status': 'terverifikasi',
            'catatan_verifikasi': 'Pelapor menyebutkan goresan di backcase dengan tepat saat wawancara verifikasi.',
        })
        self.assertRedirects(response, reverse('barang:barang_klaim_detail', kwargs={'pk': klaim.pk}))
        klaim.refresh_from_db()
        self.assertEqual(klaim.status, 'terverifikasi')
        self.assertIsNotNone(klaim.tanggal_verifikasi)

        # 5. Petugas mencatat Serah Terima Barang
        response = self.client.post(reverse('barang:serah_terima_barang', kwargs={'klaim_id': klaim.pk}), {
            'tanda_tangan_digital': 'Budi Santoso (NIS 12345)',
            'catatan': 'Barang diserahkan dalam kondisi baik dan hidup di pos satpam.',
        })
        self.assertRedirects(response, reverse('barang:barang_klaim_detail', kwargs={'pk': klaim.pk}))
        serah_terima = SerahTerimaBarang.objects.first()
        self.assertIsNotNone(serah_terima)
        self.assertEqual(serah_terima.petugas, self.petugas_barang)

        # Cek barang temuan dan laporan kehilangan berubah jadi selesai
        barang.refresh_from_db()
        self.assertEqual(barang.status, 'selesai')
        laporan.refresh_from_db()
        self.assertEqual(laporan.status, 'selesai')

    def test_rbac_barang_petugas_restricted(self):
        self.client.force_login(self.pelapor)
        response = self.client.get(reverse('barang:barang_temuan_input'))
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_pos_crud_by_petugas_barang(self):
        self.client.force_login(self.petugas_barang)

        # 1. List
        response = self.client.get(reverse('barang:pos_list'))
        self.assertEqual(response.status_code, 200)

        # 2. Tambah Pos
        response = self.client.post(reverse('barang:pos_tambah'), {
            'nama': 'Pos Satpam Asrama Putra',
            'lokasi': 'Gedung Asrama Putra Lt. 1',
            'kontak': '081298765432',
            'is_aktif': True,
        })
        self.assertRedirects(response, reverse('barang:pos_list'))
        pos_baru = LokasiPosBarang.objects.get(nama='Pos Satpam Asrama Putra')
        self.assertEqual(pos_baru.lokasi, 'Gedung Asrama Putra Lt. 1')

        # 3. Edit Pos
        response = self.client.post(reverse('barang:pos_edit', kwargs={'pk': pos_baru.pk}), {
            'nama': 'Pos Satpam Asrama Putri & Putra',
            'lokasi': 'Gedung Asrama Terpadu',
            'kontak': '081298765432',
            'is_aktif': True,
        })
        self.assertRedirects(response, reverse('barang:pos_list'))
        pos_baru.refresh_from_db()
        self.assertEqual(pos_baru.nama, 'Pos Satpam Asrama Putri & Putra')

        # 4. Hapus Pos
        response = self.client.post(reverse('barang:pos_hapus', kwargs={'pk': pos_baru.pk}))
        self.assertRedirects(response, reverse('barang:pos_list'))
        self.assertFalse(LokasiPosBarang.objects.filter(nama='Pos Satpam Asrama Putri & Putra').exists())

    def test_toggle_publikasi_barang(self):
        barang = BarangTemuan.objects.create(
            nama_barang='Flashdisk Kingston 32GB',
            lokasi_ditemukan='Lab Komputer',
            tanggal_ditemukan=datetime.date.today(),
            lokasi_pos=self.pos,
            dipublikasikan=False,
            petugas_input=self.petugas_barang,
        )
        self.client.force_login(self.petugas_barang)
        response = self.client.post(reverse('barang:barang_temuan_toggle_publikasi', kwargs={'pk': barang.pk}))
        self.assertRedirects(response, reverse('barang:barang_temuan_list'))
        barang.refresh_from_db()
        self.assertTrue(barang.dipublikasikan)

    def test_cetak_tanda_terima(self):
        barang = BarangTemuan.objects.create(
            nama_barang='Buku Paket Matematika',
            lokasi_ditemukan='Kelas X-A',
            tanggal_ditemukan=datetime.date.today(),
            lokasi_pos=self.pos,
            dipublikasikan=True,
            petugas_input=self.petugas_barang,
        )
        klaim = KlaimBarang.objects.create(
            barang_temuan=barang,
            pelapor=self.pelapor,
            alasan_klaim='Buku tertinggal di laci meja.',
            status='terverifikasi',
        )
        # Petugas can access cetak tanda terima
        self.client.force_login(self.petugas_barang)
        response = self.client.get(reverse('barang:klaim_cetak_tanda_terima', kwargs={'pk': klaim.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BERITA ACARA & TANDA TERIMA SERAH TERIMA BARANG')

        # Pelapor pemilik klaim can also view / print receipt
        self.client.force_login(self.pelapor)
        response = self.client.get(reverse('barang:klaim_cetak_tanda_terima', kwargs={'pk': klaim.pk}))
        self.assertEqual(response.status_code, 200)

        # Other pelapor is forbidden
        other_pelapor = User.objects.create_user(
            username='siswa_lain',
            password='Password123!',
            role=User.ROLE_PELAPOR,
        )
        self.client.force_login(other_pelapor)
        response = self.client.get(reverse('barang:klaim_cetak_tanda_terima', kwargs={'pk': klaim.pk}))
        self.assertRedirects(response, reverse('accounts:dashboard'))


