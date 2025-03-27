import random
import string
from django.core.mail import send_mail
from django.conf import settings
import bleach
from bleach.sanitizer import ALLOWED_TAGS as BLEACH_ALLOWED_TAGS
from bleach.sanitizer import ALLOWED_ATTRIBUTES as BLEACH_ALLOWED_ATTRIBUTES
import base64
import hashlib
from cryptography.fernet import Fernet
import uuid

# Define custom allowed HTML tags and attributes for sanitization
ALLOWED_TAGS = list(BLEACH_ALLOWED_TAGS) + ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
ALLOWED_ATTRIBUTES = dict(BLEACH_ALLOWED_ATTRIBUTES)
ALLOWED_ATTRIBUTES.update({
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
})

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(user, otp):
    """Send OTP to user's email"""
    subject = 'Your OTP for Mamma Rasa'
    message = f'Your OTP for Mamma Rasa is: {otp}. This OTP is valid for 10 minutes.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]
    
    try:
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        print(f"OTP email sent to {user.email}")
        return True
    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return False

def create_and_send_otp(user):
    """Create OTP for user and send it via email"""
    # Import OTP model here to avoid circular import
    from .models import OTP
    
    # Delete any existing OTPs for this user
    OTP.objects.filter(user=user).delete()
    
    # Generate new OTP
    otp_code = generate_otp()
    
    # Save OTP to database
    otp = OTP.objects.create(user=user, otp=otp_code)
    
    # Send OTP via email
    email_sent = send_otp_email(user, otp_code)
    
    return otp, email_sent

def verify_otp(user, otp_code):
    """Verify if OTP is valid for the user"""
    # Import OTP model here to avoid circular import
    from .models import OTP
    
    try:
        stored_otp = OTP.objects.get(user=user)
        # Dekripsi OTP yang tersimpan
        decrypted_otp = decrypt_data(stored_otp.otp)
        
        if decrypted_otp == otp_code and stored_otp.is_valid():
            # Delete OTP after successful verification
            stored_otp.delete()
            return True
        else:
            # Delete expired OTP
            if not stored_otp.is_valid():
                stored_otp.delete()
            return False
    except OTP.DoesNotExist:
        return False
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        return False

def sanitize_html(text):
    """
    Sanitize HTML content to prevent XSS attacks
    """
    if text is None:
        return ''
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)

# Caesar cipher for encrypting restaurant IDs
def caesar_encrypt(text, shift=5):
    """
    Encrypt text using Caesar cipher
    """
    if not text:
        return text
    
    # Convert UUID to string if necessary
    if isinstance(text, uuid.UUID):
        text = str(text)
        
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = ord('a') if char.islower() else ord('A')
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
        elif char.isdigit():
            result += str((int(char) + shift) % 10)
        else:
            result += char
    return result

def caesar_decrypt(text, shift=5):
    """
    Decrypt text using Caesar cipher
    """
    if not text:
        return text
    
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = ord('a') if char.islower() else ord('A')
            result += chr((ord(char) - ascii_offset - shift) % 26 + ascii_offset)
        elif char.isdigit():
            result += str((int(char) - shift) % 10)
        else:
            result += char
    return result

# Encryption key management
def get_encryption_key():
    """
    Get or create encryption key for sensitive data
    """
    # In production, this should be stored securely and not in the code
    # For this implementation, we'll generate a key based on the Django secret key
    from django.conf import settings
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encrypt_data(data):
    """
    Encrypt sensitive data
    """
    if not data:
        return data
    
    if isinstance(data, uuid.UUID):
        data = str(data)
    
    key = get_encryption_key()
    f = Fernet(key)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    """
    Decrypt sensitive data
    """
    if not encrypted_data:
        return encrypted_data
    
    key = get_encryption_key()
    f = Fernet(key)
    return f.decrypt(encrypted_data.encode()).decode() 