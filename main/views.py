from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.conf import settings

from .forms import LoginForm, RegistrationForm, OTPVerificationForm, RoleSelectionForm
from .models import User, OTP
from .utils import create_and_send_otp, verify_otp

def login_view(request):
    """View for user login with email/password or Google OAuth"""
    if request.user.is_authenticated:
        # Redirect based on user role
        if request.user.role == 'buyer':
            return redirect('buyer_page')
        elif request.user.role == 'restoran':
            return redirect('restoran_page')
        else:
            return redirect('role_selection')
    
    # Store next parameter in session if it exists
    next_url = request.GET.get('next')
    if next_url:
        request.session['next_url'] = next_url
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Create and send OTP for verification
                otp, email_sent = create_and_send_otp(user)
                
                if not email_sent:
                    messages.error(request, 'Failed to send OTP email. Please try again or contact support.')
                    return render(request, 'main/login.html', {'form': form})
                
                # Store user ID in session for OTP verification
                request.session['user_id_for_otp'] = str(user.id)
                return redirect('verify_otp')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'main/login.html', {'form': form})

def register_view(request):
    """View for user registration"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User will be activated after OTP verification
            user.save()
            
            # Create and send OTP for verification
            otp, email_sent = create_and_send_otp(user)
            
            if not email_sent:
                messages.error(request, 'Failed to send OTP email. Please try again or contact support.')
                # Delete the user since we couldn't send the OTP
                user.delete()
                return render(request, 'main/register.html', {'form': form})
            
            # Store user ID in session for OTP verification
            request.session['user_id_for_otp'] = str(user.id)
            request.session['registration'] = True
            
            return redirect('verify_otp')
    else:
        form = RegistrationForm()
    
    return render(request, 'main/register.html', {'form': form})

def verify_otp_view(request):
    """View for OTP verification"""
    user_id = request.session.get('user_id_for_otp')
    is_registration = request.session.get('registration', False)
    
    if not user_id:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please try again.')
        return redirect('login')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data.get('otp')
            
            if verify_otp(user, otp_code):
                # OTP verified successfully
                if is_registration:
                    user.is_active = True
                    user.save()
                    # Clear registration flag
                    del request.session['registration']
                
                # Log in the user with the specific backend
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Clear OTP session
                del request.session['user_id_for_otp']
                
                # Check if there's a next URL to redirect to
                next_url = request.session.get('next_url')
                if next_url:
                    # Clear the next_url from session
                    del request.session['next_url']
                    return redirect(next_url)
                
                # Otherwise, redirect based on user role
                if user.role:
                    if user.role == 'buyer':
                        return redirect('buyer_page')
                    elif user.role == 'restoran':
                        return redirect('restoran_page')
                else:
                    return redirect('role_selection')
            else:
                messages.error(request, 'Invalid or expired OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, 'main/verify_otp.html', {'form': form})

def resend_otp_view(request):
    """View for resending OTP"""
    user_id = request.session.get('user_id_for_otp')
    
    if not user_id:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        otp, email_sent = create_and_send_otp(user)
        
        if email_sent:
            messages.success(request, 'OTP has been resent to your email.')
        else:
            messages.error(request, 'Failed to send OTP email. Please try again or contact support.')
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please try again.')
    
    return redirect('verify_otp')

@login_required
def role_selection_view(request):
    """View for selecting user role (for Google OAuth users)"""
    user = request.user
    
    # If user already has a role, redirect to appropriate page
    if user.role:
        if user.role == 'buyer':
            return redirect('buyer_page')
        elif user.role == 'restoran':
            return redirect('restoran_page')
    
    if request.method == 'POST':
        form = RoleSelectionForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            
            # Redirect based on selected role
            if user.role == 'buyer':
                return redirect('buyer_page')
            elif user.role == 'restoran':
                return redirect('restoran_page')
    else:
        form = RoleSelectionForm(instance=user)
    
    return render(request, 'main/role_selection.html', {'form': form})

@login_required
def logout_view(request):
    """View for user logout"""
    logout(request)
    return redirect('login')

def home_view(request):
    """Home view that redirects based on authentication and role"""
    if request.user.is_authenticated:
        if request.user.role == 'buyer':
            return redirect('buyer_page')
        elif request.user.role == 'restoran':
            return redirect('restoran_page')
        else:
            return redirect('role_selection')
    else:
        return redirect('login')
