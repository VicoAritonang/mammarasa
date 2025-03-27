import re
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import User
from .utils import sanitize_html


def validate_strong_password(password):
    """Validates password strength based on several rules and returns multiple error messages"""
    errors = []

    if len(password) < 8:
        errors.append('Password must be at least 8 characters long.')
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter.')
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one digit number.')
    if not re.search(r'[^\w\s]', password):  # Special character
        errors.append('Password must contain at least one special character (e.g., !, @, #, etc.).')

    if errors:
        raise ValidationError(errors)

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        label='Email'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label='Password'
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        return sanitize_html(username)

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter OTP'}),
        label='OTP',
        max_length=6
    )
    
    def clean_otp(self):
        otp = self.cleaned_data.get('otp')
        return sanitize_html(otp)

class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label='Password'
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ('name', 'email', 'profile_image', 'role')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        validate_strong_password(password1)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match')

        return password2
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        return sanitize_html(name)
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        return sanitize_html(email)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

        return user

class RoleSelectionForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('role',)
        widgets = {
            'role': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
        
    def clean_role(self):
        role = self.cleaned_data.get('role')
        return sanitize_html(role)
