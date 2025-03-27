from django import forms
from .models import Restoran, Menu
from main.utils import sanitize_html

class RestoranForm(forms.ModelForm):
    class Meta:
        model = Restoran
        fields = ['nama_restoran', 'gambar_restoran']
        widgets = {
            'nama_restoran': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Restoran'}),
            'gambar_restoran': forms.FileInput(attrs={'class': 'form-control'}),
        }
        
    def clean_nama_restoran(self):
        nama_restoran = self.cleaned_data.get('nama_restoran')
        return sanitize_html(nama_restoran)

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
        
    def clean_nama_menu(self):
        nama_menu = self.cleaned_data.get('nama_menu')
        return sanitize_html(nama_menu)
        
    def clean_keterangan_makanan(self):
        keterangan_makanan = self.cleaned_data.get('keterangan_makanan')
        return sanitize_html(keterangan_makanan) 