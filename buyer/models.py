from django.db import models
import uuid
from main.models import User
from restoran.models import Restoran, Menu

class Buyer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer')
    visited_restaurants = models.ManyToManyField(Restoran, related_name='visitors', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.name

class Order(models.Model):
    STATUS_CHOICES = (
        (False, 'Not Paid'),
        (True, 'Paid'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE, related_name='orders')
    restoran = models.ForeignKey(Restoran, on_delete=models.CASCADE, related_name='orders')
    status = models.BooleanField(choices=STATUS_CHOICES, default=False)
    review = models.TextField(blank=True, null=True)
    order_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=[
        ('cash', 'Cash'),
        ('transfer', 'Transfer'),
        ('ewallet', 'E-Wallet'),
    ], default='cash')

    
    def __str__(self):
        return f"Order {self.id} - {self.buyer.user.name} at {self.restoran.nama_restoran}"
    
    @property
    def subtotal(self):
        return sum(item.menu.harga_makanan * item.quantity for item in self.items.all())
    
    @property
    def service_fee(self):
        return int(self.subtotal * 0.1)  # 10% service fee
    
    @property
    def total_price(self):
        return self.subtotal + self.service_fee

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.menu.nama_menu}"
    
    @property
    def subtotal(self):
        return self.menu.harga_makanan * self.quantity
