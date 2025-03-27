from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.conf import settings
from django.db.models import Sum
import qrcode
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
import requests
import uuid
from main.utils import sanitize_html, caesar_encrypt, caesar_decrypt

from main.models import User
from .models import Restoran, Menu
from buyer.models import Buyer, Order, OrderItem
from .forms import RestoranForm, MenuForm

# Create your views here.

@login_required
def restoran_page(request):
    """View for restaurant dashboard"""
    # Check if user has restoran role
    if request.user.role != 'restoran':
        if request.user.role == 'buyer':
            return redirect('buyer_page')
        else:
            return redirect('role_selection')
    
    # Get or create restaurant profile
    restoran, created = Restoran.objects.get_or_create(
        user=request.user,
        defaults={
            'nama_restoran': request.user.name,
        }
    )
    
    # If restaurant was just created and user has profile image, copy it to restaurant
    if created and request.user.profile_image:
        restoran.gambar_restoran = request.user.profile_image
        restoran.save()
    
    # Get all menus for this restaurant
    menus = Menu.objects.filter(restoran=restoran).order_by('-created_at')
    
    # Get recent orders
    orders = Order.objects.filter(restoran=restoran, status=True).order_by('-order_date')[:5]
    
    context = {
        'user': request.user,
        'restoran': restoran,
        'menus': menus,
        'orders': orders,
    }
    
    return render(request, 'restoran/restoran_page.html', context)

@login_required
def edit_restoran_profile(request):
    """View for editing restaurant profile"""
    if request.user.role != 'restoran':
        return redirect('home')
    
    restoran = get_object_or_404(Restoran, user=request.user)
    
    if request.method == 'POST':
        form = RestoranForm(request.POST, request.FILES, instance=restoran)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil restoran berhasil diperbarui.')
            return redirect('restoran_page')
    else:
        form = RestoranForm(instance=restoran)
    
    context = {
        'form': form,
        'restoran': restoran,
    }
    
    return render(request, 'restoran/edit_profile.html', context)

@login_required
def add_menu(request):
    """View for adding a new menu"""
    if request.user.role != 'restoran':
        return redirect('home')
    
    restoran = get_object_or_404(Restoran, user=request.user)
    
    if request.method == 'POST':
        form = MenuForm(request.POST, request.FILES)
        if form.is_valid():
            menu = form.save(commit=False)
            menu.restoran = restoran
            menu.save()
            messages.success(request, 'Menu berhasil ditambahkan.')
            return redirect('restoran_page')
    else:
        form = MenuForm()
    
    context = {
        'form': form,
        'restoran': restoran,
        'action': 'add',
    }
    
    return render(request, 'restoran/menu_form.html', context)

@login_required
def edit_menu(request, menu_id):
    """View for editing a menu"""
    if request.user.role != 'restoran':
        return redirect('home')
    
    restoran = get_object_or_404(Restoran, user=request.user)
    menu = get_object_or_404(Menu, id=menu_id, restoran=restoran)
    
    if request.method == 'POST':
        form = MenuForm(request.POST, request.FILES, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu berhasil diperbarui.')
            return redirect('restoran_page')
    else:
        form = MenuForm(instance=menu)
    
    context = {
        'form': form,
        'restoran': restoran,
        'menu': menu,
        'action': 'edit',
    }
    
    return render(request, 'restoran/menu_form.html', context)

@login_required
def delete_menu(request, menu_id):
    """View for deleting a menu"""
    if request.user.role != 'restoran':
        return redirect('home')
    
    restoran = get_object_or_404(Restoran, user=request.user)
    menu = get_object_or_404(Menu, id=menu_id, restoran=restoran)
    
    if request.method == 'POST':
        menu.delete()
        messages.success(request, 'Menu berhasil dihapus.')
        return redirect('restoran_page')
    
    context = {
        'menu': menu,
        'restoran': restoran,
    }
    
    return render(request, 'restoran/delete_menu.html', context)

@login_required
def generate_qr(request):
    """View for generating QR code for restaurant menu page"""
    if request.user.role != 'restoran':
        return redirect('home')
    
    restoran = get_object_or_404(Restoran, user=request.user)
    
    # Encrypt restaurant ID using Caesar cipher
    encrypted_id = caesar_encrypt(restoran.id)
    
    # Generate menu URL with encrypted ID
    menu_url = request.build_absolute_uri(reverse('menu_view', args=[encrypted_id]))
    
    # Generate QR code using external API
    try:
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={menu_url}"
        
        # If restaurant doesn't have a QR code yet, save it
        if not restoran.qrcode:
            response = requests.get(qr_api_url)
            if response.status_code == 200:
                img_name = f"{restoran.id}_qrcode.png"
                restoran.qrcode.save(img_name, ContentFile(response.content), save=True)
        
        context = {
            'restoran': restoran,
            'menu_url': menu_url,
            'qr_api_url': qr_api_url,
        }
        
        return render(request, 'restoran/generate_qr.html', context)
    
    except Exception as e:
        messages.error(request, f'Error generating QR code: {str(e)}')
        return redirect('restoran_page')

def menu_view(request, restoran_id):
    """Public view for restaurant menu page (accessible via QR code)"""
    try:
        # Decrypt restaurant ID from the URL
        decrypted_id = caesar_decrypt(restoran_id)
        restoran = get_object_or_404(Restoran, id=decrypted_id)
        menus = Menu.objects.filter(restoran=restoran, is_visible=True)
        
        # If user is authenticated and is a buyer, add this restaurant to visited restaurants
        if request.user.is_authenticated and request.user.role == 'buyer':
            buyer, created = Buyer.objects.get_or_create(user=request.user)
            buyer.visited_restaurants.add(restoran)
        
        context = {
            'restoran': restoran,
            'menus': menus,
        }
        
        return render(request, 'restoran/main_view.html', context)
    except Exception as e:
        # In case of decryption failure or invalid URL
        messages.error(request, 'Invalid restaurant link')
        return redirect('home')

@login_required
def add_to_cart(request, menu_id):
    """View for adding a menu to cart"""
    if request.user.role != 'buyer':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Only buyers can add items to cart'}, status=403)
        else:
            messages.error(request, 'Only buyers can add items to cart')
            return redirect('home')
    
    menu = get_object_or_404(Menu, id=menu_id)
    
    # Get or create buyer
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    
    # Get or create an unpaid order for this buyer and restaurant
    order, created = Order.objects.get_or_create(
        buyer=buyer,
        restoran=menu.restoran,
        status=False,
        defaults={'review': ''}
    )
    
    # Check if this menu is already in the order
    try:
        order_item = OrderItem.objects.get(order=order, menu=menu)
        order_item.quantity += 1
        order_item.save()
    except OrderItem.DoesNotExist:
        order_item = OrderItem.objects.create(order=order, menu=menu, quantity=1)
    
    # Store order ID in session for checkout
    request.session['current_order_id'] = str(order.id)
    
    # Return response based on request type
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return updated cart data for AJAX requests
        cart_items = OrderItem.objects.filter(order=order)
        cart_data = {
            'items': [
                {
                    'id': str(item.id),
                    'menu_id': str(item.menu.id),
                    'name': item.menu.nama_menu,
                    'price': item.menu.harga_makanan,
                    'quantity': item.quantity,
                    'subtotal': item.subtotal
                } for item in cart_items
            ],
            'total': order.total_price,
            'order_id': str(order.id)
        }
        return JsonResponse(cart_data)
    else:
        # Redirect to view cart for non-AJAX requests
        messages.success(request, f'{menu.nama_menu} added to your cart.')
        return redirect('view_cart', restoran_id=menu.restoran.id)

@login_required
def view_orders(request):
    """View for restaurant to see all orders"""
    if request.user.role != 'restoran':
        return redirect('home')
    
    restoran = get_object_or_404(Restoran, user=request.user)
    orders = Order.objects.filter(restoran=restoran, status=True).order_by('-order_date')
    
    context = {
        'restoran': restoran,
        'orders': orders,
    }
    
    return render(request, 'restoran/view_orders.html', context)

@login_required
def toggle_menu_visibility(request, menu_id):
    """View for toggling menu visibility"""
    if request.user.role != 'restoran':
        return redirect('home')
    
    restoran = get_object_or_404(Restoran, user=request.user)
    menu = get_object_or_404(Menu, id=menu_id, restoran=restoran)
    
    # Toggle visibility
    menu.is_visible = not menu.is_visible
    menu.save()
    
    # Return JSON response if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_visible': menu.is_visible
        })
    
    # Otherwise redirect back to restaurant page
    messages.success(request, f'Menu "{menu.nama_menu}" is now {"visible" if menu.is_visible else "hidden"}.')
    return redirect('restoran_page')
