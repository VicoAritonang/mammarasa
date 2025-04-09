from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum
from django.urls import reverse

from main.models import User
from restoran.models import Restoran, Menu
from .models import Buyer, Order, OrderItem
from .forms import OrderReviewForm

# Create your views here.

@login_required
def buyer_page(request):
    """View for buyer dashboard"""
    # Check if user has buyer role
    if request.user.role != 'buyer':
        if request.user.role == 'restoran':
            return redirect('restoran_page')
        else:
            return redirect('role_selection')
    
    # Get or create buyer profile
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    
    # Get visited restaurants
    visited_restaurants = buyer.visited_restaurants.all()
    
    # Get recent orders
    orders = Order.objects.filter(buyer=buyer).order_by('-order_date')[:5]
    
    context = {
        'user': request.user,
        'buyer': buyer,
        'visited_restaurants': visited_restaurants,
        'orders': orders,
    }
    
    return render(request, 'buyer/buyer_page.html', context)

@login_required
def view_cart(request, restoran_id):
    """View for viewing the current cart"""
    if request.user.role != 'buyer':
        return redirect('home')
    
    restoran = get_object_or_404(Restoran, id=restoran_id)
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    
    # Get current unpaid order for this restaurant
    try:
        # First try to get the order from the database
        order = Order.objects.get(buyer=buyer, restoran=restoran, status=False)
    except Order.DoesNotExist:
        # If no order exists, check if there's an order ID in the session
        order_id = request.session.get('current_order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id, buyer=buyer, status=False)
            except Order.DoesNotExist:
                order = None
                order_items = []
                messages.info(request, "Your cart is empty.")
                return render(request, 'buyer/view_cart.html', {
                    'buyer': buyer,
                    'restoran': restoran,
                    'order': None,
                    'order_items': [],
                })
        else:
            order = None
            order_items = []
            messages.info(request, "Your cart is empty.")
            return render(request, 'buyer/view_cart.html', {
                'buyer': buyer,
                'restoran': restoran,
                'order': None,
                'order_items': [],
            })
    
    # Get order items
    order_items = OrderItem.objects.filter(order=order)
    
    # Store order ID in session
    request.session['current_order_id'] = str(order.id)
    
    context = {
        'buyer': buyer,
        'restoran': restoran,
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'buyer/view_cart.html', context)

@login_required
def update_cart_item(request, item_id):
    """AJAX view for updating cart item quantity"""
    if request.user.role != 'buyer':
        return JsonResponse({'error': 'Only buyers can update cart'}, status=403)
    
    item = get_object_or_404(OrderItem, id=item_id)
    order = item.order
    
    # Ensure the order belongs to the current user
    if order.buyer.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get the new quantity from the request
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        # Remove item if quantity is 0 or less
        item.delete()
    else:
        # Update quantity
        item.quantity = quantity
        item.save()
    
    # Return updated cart data
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
        'total': order.total_price
    }
    
    return JsonResponse(cart_data)

@login_required
def checkout(request, order_id):
    if request.user.role != 'buyer':
        return redirect('home')

    order = get_object_or_404(Order, id=order_id, buyer__user=request.user, status=False)
    order_items = order.items.all()

    if request.method == 'POST':
        form = OrderReviewForm(request.POST, instance=order)
        if form.is_valid():
            # Simpan informasi delivery di sini!
            form.save()  # Menyimpan data name, phone, address ke Order
            return redirect('payment', order_id=order.id)
        else:
            messages.error(request, "Mohon lengkapi data pengiriman dengan benar.")
    else:
        form = OrderReviewForm(instance=order)

    context = {
        'order': order,
        'order_items': order_items,
        'form': form,
    }

    return render(request, 'buyer/checkout.html', context)


@login_required
def payment(request, order_id):
    """View for payment page with QR code"""
    if request.user.role != 'buyer':
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id, buyer__user=request.user, status=False)
    order_items = order.items.all()
    
    # Generate payment URL
    payment_url = request.build_absolute_uri(reverse('payment_confirmation', args=[str(order.id)]))
    
    # Generate QR code using external API
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={payment_url}"
    
    context = {
        'order': order,
        'order_items': order_items,
        'qr_api_url': qr_api_url,
        'payment_url': payment_url,
    }
    
    return render(request, 'buyer/payment.html', context)

@login_required
def payment_confirmation(request, order_id):
    """View for payment confirmation page"""
    if request.user.role != 'buyer':
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id, buyer__user=request.user, status=False)
    
    context = {
        'order': order,
    }
    
    return render(request, 'buyer/payment_confirmation.html', context)

@login_required
def process_payment(request, order_id):
    """View for processing payment"""
    if request.user.role != 'buyer':
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id, buyer__user=request.user, status=False)
    
    if request.method == 'POST':
        # Mark order as paid
        order.status = True
        order.save()
        
        # Clear order ID from session
        if 'current_order_id' in request.session:
            del request.session['current_order_id']
        
        messages.success(request, 'Pembayaran berhasil! Pesanan Anda sedang diproses.')
        return redirect('buyer_page')
    
    # If not POST, redirect to payment confirmation
    return redirect('payment_confirmation', order_id=order.id)

@login_required
def order_history(request):
    """View for viewing order history"""
    if request.user.role != 'buyer':
        return redirect('home')
    
    buyer, created = Buyer.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(buyer=buyer).order_by('-order_date')
    
    context = {
        'buyer': buyer,
        'orders': orders,
    }
    
    return render(request, 'buyer/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """View for viewing order details"""
    if request.user.role != 'buyer':
        return redirect('home')
    
    order = get_object_or_404(Order, id=order_id, buyer__user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    
    return render(request, 'buyer/order_detail.html', context)
