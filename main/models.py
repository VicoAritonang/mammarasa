from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
from django.utils import timezone
from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from datetime import timedelta
from .utils import encrypt_data, decrypt_data

class UserManager(BaseUserManager):

    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        if password:
            # Password will be hashed by Django's set_password method
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('restoran', 'Restoran'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    def __str__(self):
        return self.email

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.otp}"
    
    def is_valid(self):
        # OTP valid for 10 minutes
        return (timezone.now() - self.created_at).total_seconds() < 600
        
    def save(self, *args, **kwargs):
        # Encrypt OTP before saving
        if not self.id:  # Only encrypt when first created
            self.otp = encrypt_data(self.otp)
        super().save(*args, **kwargs)

class LoginAttempt(models.Model):
    user_email = models.EmailField()
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user_email} - {self.timestamp}"
    
    @classmethod
    def get_timeout_remaining(cls, ip_address):
        recent_attempts = cls.objects.filter(
            ip_address=ip_address,
            timestamp__gte=timezone.now() - timedelta(minutes=5),
            successful=False
        ).order_by('-timestamp')[:3]
        
        # Check if there are exactly 3 recent failed attempts
        if len(recent_attempts) == 3:
            # Get the most recent failed attempt
            last_attempt = recent_attempts[0]
            
            if last_attempt:
                timeout_end = last_attempt.timestamp + timedelta(minutes=2)
                remaining = (timeout_end - timezone.now()).total_seconds()
                return max(0, int(remaining))
        return 0

# Register models with auditlog
auditlog.register(User)
auditlog.register(LoginAttempt)

