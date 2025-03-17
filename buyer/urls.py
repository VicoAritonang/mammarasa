from django.urls import path
from . import views

urlpatterns = [
    path('', views.buyer_page, name='buyer_page'),
    path('view-cart/<uuid:restoran_id>/', views.view_cart, name='view_cart'),
    path('update-cart-item/<uuid:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/<uuid:order_id>/', views.checkout, name='checkout'),
    path('payment/<uuid:order_id>/', views.payment, name='payment'),
    path('payment-confirmation/<uuid:order_id>/', views.payment_confirmation, name='payment_confirmation'),
    path('process-payment/<uuid:order_id>/', views.process_payment, name='process_payment'),
    path('order-history/', views.order_history, name='order_history'),
    path('order-detail/<uuid:order_id>/', views.order_detail, name='order_detail'),
] 