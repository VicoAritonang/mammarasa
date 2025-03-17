from django import forms
from .models import Order

class OrderReviewForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['review']
        widgets = {
            'review': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tulis review Anda di sini...', 'rows': 3}),
        } 