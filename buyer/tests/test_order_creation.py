import logging
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from restoran.models import Restoran, Menu
from buyer.models import Buyer, Order, OrderItem
from django.contrib.auth import get_user_model

# Initialize the logger
logger = logging.getLogger(__name__)

class OrderCreationTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Create user (email = username karena USERNAME_FIELD = 'email')
        self.user = User.objects.create_user(
            email='buyer@example.com',
            name='Buyer Test',
            password='Password123!',
            role='buyer'
        )

        # Login with correct credentials (username = email karena USERNAME_FIELD = 'email')
        self.client.login(username='buyer@example.com', password='Password123!')

        # Setup restoran, menu, buyer, order, item
        self.restoran = Restoran.objects.create(
            nama_restoran='Mamma Rasa',
            user=self.user  # <--- ini kunci fix-nya
        )

        self.menu = Menu.objects.create(nama_menu='Nasi Goreng', harga_makanan=20000, restoran=self.restoran)

        self.buyer = Buyer.objects.create(user=self.user)
        self.order = Order.objects.create(buyer=self.buyer, restoran=self.restoran, status=False)
        self.item = OrderItem.objects.create(order=self.order, menu=self.menu, quantity=1)

        self.view_cart_url = reverse('view_cart', args=[str(self.restoran.id)])
        self.update_url = reverse('update_cart_item', args=[str(self.item.id)])
        self.checkout_url = reverse('checkout', args=[str(self.order.id)])

    def test_add_to_cart_and_create_order(self):
        """Test that adding an item to the cart creates an order."""
        self.client.login(username='testbuyer', password='password')

        # Log the action
        logger.info(f'Buyer {self.user.username} is adding {self.menu_item.nama_menu} to cart.')

        # Add the menu item to the cart
        url = reverse('add_to_cart', args=[self.menu_item.id])
        response = self.client.post(url)

        # Check that the response is a redirect to the cart view
        self.assertRedirects(response, reverse('view_cart', args=[self.restoran.id]))

        # Ensure an order has been created
        order = Order.objects.filter(buyer=self.buyer, restoran=self.restoran, status=False).first()
        self.assertIsNotNone(order, "Order should be created for the buyer.")

        # Ensure the menu item has been added to the order
        order_item = OrderItem.objects.filter(order=order, menu=self.menu_item).first()
        self.assertIsNotNone(order_item, "Menu item should be added to the order.")
        self.assertEqual(order_item.quantity, 1, "The quantity of the item should be 1.")

    def test_add_multiple_items_to_cart(self):
        """Test adding multiple items to the cart and creating an order."""
        menu_item_2 = Menu.objects.create(nama_menu="Another Menu Item", harga_makanan=200, restoran=self.restoran)

        self.client.login(username='testbuyer', password='password')

        # Add items to the cart
        url = reverse('add_to_cart', args=[self.menu_item.id])
        self.client.post(url)
        self.client.post(reverse('add_to_cart', args=[menu_item_2.id]))

        # Ensure both items are in the cart
        order = Order.objects.filter(buyer=self.buyer, restoran=self.restoran, status=False).first()
        self.assertIsNotNone(order, "Order should be created for the buyer.")

        # Check if both items are in the order
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 2, "There should be two items in the order.")

    def test_add_item_to_cart_for_non_buyer(self):
        """Test that non-buyers cannot add items to the cart."""
        non_buyer_user = User.objects.create_user(username='testrestoran', password='password', role='restoran')
        self.client.login(username='testrestoran', password='password')

        # Try to add a menu item to the cart
        url = reverse('add_to_cart', args=[self.menu_item.id])
        response = self.client.post(url)

        # Ensure that only buyers can add items to the cart
        self.assertEqual(response.status_code, 403, "Non-buyers should not be able to add items to the cart.")

    def test_unauthenticated_user_access_cart(self):
        """Test that unauthenticated users cannot access the cart."""
        response = self.client.get(reverse('view_cart', args=[self.restoran.id]))
        self.assertRedirects(response, '/login/')  # Should redirect to login page

    def test_cart_contains_correct_item(self):
        """Test that the cart contains the correct menu item."""
        self.client.login(username='testbuyer', password='password')

        url = reverse('add_to_cart', args=[self.menu_item.id])
        self.client.post(url)

        # Get the cart (order)
        order = Order.objects.filter(buyer=self.buyer, restoran=self.restoran, status=False).first()
        self.assertIsNotNone(order)

        # Check if the cart contains the correct item
        order_item = OrderItem.objects.filter(order=order, menu=self.menu_item).first()
        self.assertEqual(order_item.menu, self.menu_item, "The cart should contain the correct menu item.")
        self.assertEqual(order_item.quantity, 1, "The quantity of the item should be 1.")

    def test_non_buyer_access_checkout(self):
        """Test that non-buyers cannot access the checkout page."""
        non_buyer_user = User.objects.create_user(username='testrestoran', password='password', role='restoran')
        self.client.login(username='testrestoran', password='password')

        response = self.client.get(reverse('checkout', args=[1]))  # Assuming order ID is 1
        self.assertRedirects(response, reverse('home'))  # Should redirect to home

    def test_order_status_on_creation(self):
        """Test that the order status is False when created."""
        self.client.login(username='testbuyer', password='password')
        url = reverse('add_to_cart', args=[self.menu_item.id])
        self.client.post(url)

        # Get the order created
        order = Order.objects.filter(buyer=self.buyer, restoran=self.restoran, status=False).first()
        self.assertFalse(order.status, "The order status should be False when created.")

    def test_empty_cart_checkout(self):
        """Test that attempting to checkout with an empty cart results in a message."""
        self.client.login(username='testbuyer', password='password')
        response = self.client.get(reverse('checkout', args=[1]))  # Assuming order ID is 1
        self.assertContains(response, "Your cart is empty.")
