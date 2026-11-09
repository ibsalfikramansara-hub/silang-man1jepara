from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import User


class CustomAuthenticationForm(AuthenticationForm):
    """Form login dengan atribut Bootstrap 5."""
    username = forms.CharField(
        label='Username / Email',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan username atau email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password',
        })
    )


class UserCreateForm(forms.ModelForm):
    """Form tambah pengguna baru oleh Admin."""
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password pengguna baru',
        }),
        min_length=6,
        help_text='Tentukan password awal untuk pengguna baru (minimal 6 karakter).',
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'role',
            'nip_nisn', 'telepon', 'instansi_unit', 'is_verified',
            'is_active', 'is_staff', 'password'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Depan'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Belakang'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@madrasah.sch.id'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'nip_nisn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NIS / NISN / NIP'}),
            'telepon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '08xxxxxxxxxx'}),
            'instansi_unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kelas / Jurusan / Bagian'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('Alamat email ini sudah terdaftar pada pengguna lain.')
        return email

    def clean_nip_nisn(self):
        nip = self.cleaned_data.get('nip_nisn')
        if nip:
            if User.objects.filter(nip_nisn=nip).exists():
                raise forms.ValidationError('NIS / NISN / NIP ini sudah digunakan oleh akun lain.')
        return nip


class UserUpdateForm(forms.ModelForm):
    """Form perbarui pengguna oleh Admin (tanpa field password langsung)."""

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'role',
            'nip_nisn', 'telepon', 'instansi_unit', 'is_verified',
            'is_active', 'is_staff'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'nip_nisn': forms.TextInput(attrs={'class': 'form-control'}),
            'telepon': forms.TextInput(attrs={'class': 'form-control'}),
            'instansi_unit': forms.TextInput(attrs={'class': 'form-control'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = User.objects.filter(email__iexact=email)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('Alamat email ini sudah terdaftar pada pengguna lain.')
        return email

    def clean_nip_nisn(self):
        nip = self.cleaned_data.get('nip_nisn')
        if nip:
            qs = User.objects.filter(nip_nisn=nip)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('NIS / NISN / NIP ini sudah digunakan oleh akun lain.')
        return nip


class AdminPasswordResetForm(forms.Form):
    """Form bagi Admin untuk mereset password pengguna."""
    new_password = forms.CharField(
        label='Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Masukkan password baru',
        }),
        min_length=6,
        help_text='Minimal 6 karakter.',
    )
    confirm_password = forms.CharField(
        label='Konfirmasi Password Baru',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ulangi password baru',
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Konfirmasi password tidak cocok dengan password baru.')
        return cleaned_data


class UserSelfPasswordChangeForm(PasswordChangeForm):
    """Form ganti password mandiri oleh pengguna yang sedang login."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
