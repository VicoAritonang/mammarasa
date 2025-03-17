from django import forms
from .models import Restoran, Menu

class RestoranForm(forms.ModelForm):
    class Meta:
        model = Restoran
        fields = ['nama_restoran', 'gambar_restoran']
        widgets = {
            'nama_restoran': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Restoran'}),
            'gambar_restoran': forms.FileInput(attrs={'class': 'form-control'}),
        }

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['nama_menu', 'foto_makanan', 'harga_makanan', 'keterangan_makanan']
        widgets = {
            'nama_menu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Menu'}),
            'foto_makanan': forms.FileInput(attrs={'class': 'form-control'}),
            'harga_makanan': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Harga Makanan'}),
            'keterangan_makanan': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Keterangan Makanan', 'rows': 3}),
        } 