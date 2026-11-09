from django import forms
from .models import (
    BarangTemuan, LaporanKehilangan, KlaimBarang,
    SerahTerimaBarang, LokasiPosBarang,
)
from accounts.models import User


class BarangTemuanForm(forms.ModelForm):
    """Form input & update barang temuan oleh Petugas Barang."""

    class Meta:
        model = BarangTemuan
        fields = [
            'nama_barang', 'deskripsi', 'foto', 'lokasi_ditemukan',
            'tanggal_ditemukan', 'lokasi_pos', 'dipublikasikan',
        ]
        widgets = {
            'nama_barang': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Dompet Kulit Cokelat, Flashdisk 32GB',
            }),
            'deskripsi': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Jelaskan ciri khusus, merek, kondisi fisik barang temuan...',
            }),
            'foto': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'lokasi_ditemukan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Masjid madrasah lantai 2, Kantin barat',
            }),
            'tanggal_ditemukan': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'lokasi_pos': forms.Select(attrs={
                'class': 'form-select',
            }),
            'dipublikasikan': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lokasi_pos'].queryset = LokasiPosBarang.objects.filter(is_active=True)


class BarangTemuanUpdateForm(BarangTemuanForm):
    """Form update barang temuan dengan pilihan status."""

    class Meta(BarangTemuanForm.Meta):
        fields = BarangTemuanForm.Meta.fields + ['status']
        widgets = {
            **BarangTemuanForm.Meta.widgets,
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class LaporanKehilanganForm(forms.ModelForm):
    """Form pelaporan barang hilang oleh civitas akademika."""

    class Meta:
        model = LaporanKehilangan
        fields = [
            'nama_barang', 'deskripsi', 'foto_referensi',
            'lokasi_terakhir_terlihat', 'tanggal_terakhir_terlihat',
        ]
        widgets = {
            'nama_barang': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Kunci motor Honda gantungan merah',
            }),
            'deskripsi': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Sebutkan ciri khusus, warna, merek, isi atau tanda unik yang hanya Anda ketahui...',
            }),
            'foto_referensi': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'lokasi_terakhir_terlihat': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Parkiran motor timur, Perpustakaan meja 4',
            }),
            'tanggal_terakhir_terlihat': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }


class KlaimBarangForm(forms.ModelForm):
    """Form pengajuan klaim barang temuan."""

    class Meta:
        model = KlaimBarang
        fields = ['barang_temuan', 'alasan_klaim', 'detail_verifikasi']
        widgets = {
            'alasan_klaim': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Jelaskan mengapa Anda yakin barang tersebut milik Anda...',
            }),
            'detail_verifikasi': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Sebutkan detail tersembunyi yang membuktikan kepemilikan Anda (misal: isi dompet, goresan khusus, nomor seri)...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'barang_temuan' in self.fields:
            self.fields['barang_temuan'].required = False


class KlaimActionForm(forms.ModelForm):
    """Form verifikasi klaim kepemilikan oleh Petugas Barang."""

    class Meta:
        model = KlaimBarang
        fields = ['status', 'catatan_verifikasi']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'catatan_verifikasi': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Catatan hasil verifikasi kepemilikan dengan pelapor...',
            }),
        }


class SerahTerimaBarangForm(forms.ModelForm):
    """Form serah terima barang ke pemilik sah."""

    class Meta:
        model = SerahTerimaBarang
        fields = ['klaim', 'foto_bukti', 'tanda_tangan_digital', 'catatan']
        widgets = {
            'foto_bukti': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'tanda_tangan_digital': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama terang atau kode verifikasi penerima barang',
            }),
            'catatan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Catatan serah terima fisik (kondisi barang saat diserahkan, identitas KTP/Kartu Pelajar penerima, dll)...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'klaim' in self.fields:
            self.fields['klaim'].required = False


class LokasiPosBarangForm(forms.ModelForm):
    """Form kelola Pos Penitipan Barang Temuan oleh Admin / Petugas Barang."""

    class Meta:
        model = LokasiPosBarang
        fields = ['nama', 'lokasi', 'petugas_penanggung_jawab', 'is_active']
        widgets = {
            'nama': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama Pos (misal: Pos Satpam Gerbang Utama)',
            }),
            'lokasi': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lokasi Fisik (misal: Gerbang Depan Gedung A)',
            }),
            'petugas_penanggung_jawab': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['petugas_penanggung_jawab'].queryset = User.objects.filter(
            role__in=['petugas_barang', 'admin'],
            is_active=True,
        )
