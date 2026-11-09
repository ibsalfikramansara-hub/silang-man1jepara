from django import forms
from .models import Pengaduan, KategoriPengaduan
from accounts.models import User


class PengaduanForm(forms.ModelForm):
    """Form untuk mengajukan atau memperbarui pengaduan."""

    class Meta:
        model = Pengaduan
        fields = ['judul', 'kategori', 'is_anonim', 'prioritas', 'isi_pengaduan']
        widgets = {
            'judul': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contoh: Kerusakan fasilitas AC ruang kelas X-A',
            }),
            'kategori': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_anonim': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'prioritas': forms.Select(attrs={
                'class': 'form-select',
            }),
            'isi_pengaduan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Jelaskan kronologi, detail kejadian, atau masukan saran secara lengkap...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['kategori'].queryset = KategoriPengaduan.objects.filter(is_active=True)


class PengaduanActionForm(forms.ModelForm):
    """Form penanganan petugas pengaduan (ubah status, petugas, dan catatan)."""

    class Meta:
        model = Pengaduan
        fields = ['status', 'petugas_penanganan', 'catatan_petugas']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'petugas_penanganan': forms.Select(attrs={'class': 'form-select'}),
            'catatan_petugas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Catatan perkembangan tindak lanjut pengaduan...',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['petugas_penanganan'].queryset = User.objects.filter(
            role__in=['petugas_pengaduan', 'admin', 'kepala_madrasah'],
            is_active=True,
        )


class EskalasiPengaduanForm(forms.ModelForm):
    """Form eskalasi pengaduan ke Kepala Madrasah."""

    class Meta:
        model = Pengaduan
        fields = ['catatan_petugas']
        widgets = {
            'catatan_petugas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tuliskan alasan eskalasi serta pertimbangan kasus untuk pimpinan...',
            }),
        }
        labels = {
            'catatan_petugas': 'Alasan Eskalasi',
        }


class RatingKepuasanForm(forms.ModelForm):
    """Form pemberian rating kepuasan oleh pelapor setelah pengaduan selesai."""

    class Meta:
        model = Pengaduan
        fields = ['rating_kepuasan', 'ulasan_kepuasan']
        widgets = {
            'rating_kepuasan': forms.NumberInput(attrs={
                'type': 'range',
                'min': 1,
                'max': 5,
                'class': 'form-range',
            }),
            'ulasan_kepuasan': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Berikan ulasan Anda terkait pelayanan yang telah diberikan (opsional)...',
            }),
        }
        labels = {
            'rating_kepuasan': 'Skor Kepuasan (1-5)',
            'ulasan_kepuasan': 'Ulasan Pelayanan',
        }

    def clean_rating_kepuasan(self):
        rating = self.cleaned_data.get('rating_kepuasan')
        if rating is not None and (rating < 1 or rating > 5):
            raise forms.ValidationError('Rating harus berada di antara nilai 1 dan 5.')
        return rating


class KategoriPengaduanForm(forms.ModelForm):
    """Form kelola Kategori Pengaduan oleh Admin."""

    class Meta:
        model = KategoriPengaduan
        fields = ['nama', 'deskripsi', 'petugas_penanggung_jawab', 'sla_jam', 'is_active']
        widgets = {
            'nama': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama Kategori (misal: Fasilitas & Sarpras)',
            }),
            'deskripsi': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Deskripsi lingkup kategori pengaduan...',
            }),
            'petugas_penanggung_jawab': forms.Select(attrs={
                'class': 'form-select',
            }),
            'sla_jam': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': '24',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['petugas_penanggung_jawab'].queryset = User.objects.filter(
            role__in=['petugas_pengaduan', 'admin'],
            is_active=True,
        )
