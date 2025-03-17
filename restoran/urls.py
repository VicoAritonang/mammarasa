from django.urls import path
from . import views

urlpatterns = [
    path('', views.restoran_page, name='restoran_page'),
    path('edit-profile/', views.edit_restoran_profile, name='edit_restoran_profile'),
    path('add-menu/', views.add_menu, name='add_menu'),
    path('edit-menu/<uuid:menu_id>/', views.edit_menu, name='edit_menu'),
    path('delete-menu/<uuid:menu_id>/', views.delete_menu, name='delete_menu'),
    path('toggle-menu-visibility/<uuid:menu_id>/', views.toggle_menu_visibility, name='toggle_menu_visibility'),
    path('generate-qr/', views.generate_qr, name='generate_qr'),
    path('view-orders/', views.view_orders, name='view_orders'),
    path('menu/<uuid:restoran_id>/', views.menu_view, name='menu_view'),
    path('add-to-cart/<uuid:menu_id>/', views.add_to_cart, name='add_to_cart'),
] 