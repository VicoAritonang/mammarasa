from django.db import models
import uuid
from main.models import User

class Restoran(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restoran')
    nama_restoran = models.CharField(max_length=255)
    gambar_restoran = models.ImageField(upload_to='restoran_images/', null=True, blank=True)
    qrcode = models.ImageField(upload_to='qrcode_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nama_restoran
    
    def save(self, *args, **kwargs):
        # Set default nama_restoran to user's name if not provided
        if not self.nama_restoran:
            self.nama_restoran = self.user.name
        super().save(*args, **kwargs)

class Menu(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restoran = models.ForeignKey(Restoran, on_delete=models.CASCADE, related_name='menus')
    nama_menu = models.CharField(max_length=255)
    foto_makanan = models.ImageField(upload_to='menu_images/', null=True, blank=True)
    harga_makanan = models.IntegerField()
    keterangan_makanan = models.TextField()
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nama_menu} - {self.restoran.nama_restoran}"
