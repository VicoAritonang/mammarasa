from django.shortcuts import redirect
from django.urls import reverse
from .models import User

def create_user(backend, user=None, response=None, *args, **kwargs):
    """
    Custom pipeline function to create a user from social auth data.
    If the user already exists, it will be returned.
    If the user doesn't exist, it will be created with data from the social auth provider.
    """
    if user:
        return {'is_new': False}
    
    if not kwargs.get('email') and response.get('email'):
        kwargs['email'] = response.get('email')
    
    if not kwargs.get('email'):
        return redirect('login')
    
    # Check if user exists
    try:
        user = User.objects.get(email=kwargs['email'])
        return {'is_new': False, 'user': user}
    except User.DoesNotExist:
        # Create new user
        name = response.get('name', '')
        if not name and response.get('given_name') and response.get('family_name'):
            name = f"{response.get('given_name')} {response.get('family_name')}"
        
        user = User.objects.create_user(
            email=kwargs['email'],
            name=name,
        )
        
        # Set profile image if available
        if response.get('picture'):
            from urllib.request import urlopen
            from django.core.files.base import ContentFile
            
            try:
                image_url = response.get('picture')
                image_content = urlopen(image_url).read()
                user.profile_image.save(f"{user.id}.jpg", ContentFile(image_content))
            except Exception as e:
                print(f"Error saving profile image: {e}")
        
        # Redirect to role selection page for new users
        kwargs['user'] = user
        kwargs['is_new'] = True
        
        # We'll handle the redirect to role selection in the social auth complete view
        return {'is_new': True, 'user': user} 