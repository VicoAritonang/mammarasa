import random
import string
from django.core.mail import send_mail
from django.conf import settings
from .models import OTP

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
    try:
        otp = OTP.objects.get(user=user, otp=otp_code)
        if otp.is_valid():
            # Delete OTP after successful verification
            otp.delete()
            return True
        else:
            # Delete expired OTP
            otp.delete()
            return False
    except OTP.DoesNotExist:
        return False 