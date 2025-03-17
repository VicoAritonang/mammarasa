from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('role-selection/', views.role_selection_view, name='role_selection'),
    path('logout/', views.logout_view, name='logout'),
    path('social-auth/', include('social_django.urls', namespace='social')),
] 