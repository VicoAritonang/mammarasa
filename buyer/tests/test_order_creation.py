# buyer/tests/test_order_creation.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from restoran.models import Restoran, Menu
from buyer.models import Order, OrderItem

class OrderCreationTest(TestCase):

    def setUp(self):
        # Create a buyer user
        self.user = User.objects.create_user(username='testbuyer', password='password', role='buyer')
        self.restoran = Restoran.objects.create(user=self.user, nama_restoran='Test Restaurant')
        self.menu_item = Menu.objects.create(nama_menu="Test Menu Item", harga_makanan=100, restoran=self.restoran)

        # Create a buyer instance for the user
        self.buyer = Buyer.objects.create(user=self.user)

    def test_add_to_cart_and_create_order(self):
        # Login the buyer user
        self.client.login(username='testbuyer', password='password')

        # Add the menu item to the cart
        url = reverse('add_to_cart', args=[self.menu_item.id])
        response = self.client.post(url)

        # Check that the response is a redirect to the cart view
        self.assertRedirects(response, reverse('view_cart', restoran_id=self.restoran.id))

        # Ensure an order has been created
        order = Order.objects.filter(buyer=self.buyer, restoran=self.restoran, status=False).first()
        self.assertIsNotNone(order, "Order should be created for the buyer.")

        # Ensure the menu item has been added to the order
        order_item = OrderItem.objects.filter(order=order, menu=self.menu_item).first()
        self.assertIsNotNone(order_item, "Menu item should be added to the order.")
        self.assertEqual(order_item.quantity, 1, "The quantity of the item should be 1.")

    def test_add_multiple_items_to_cart(self):
        # Create another menu item
        menu_item_2 = Menu.objects.create(nama_menu="Another Menu Item", harga_makanan=200, restoran=self.restoran)

        # Login the buyer user
        self.client.login(username='testbuyer', password='password')

        # Add the first menu item to the cart
        url = reverse('add_to_cart', args=[self.menu_item.id])
        self.client.post(url)

        # Add the second menu item to the cart
        url = reverse('add_to_cart', args=[menu_item_2.id])
        self.client.post(url)

        # Ensure both items are in the cart (Order)
        order = Order.objects.filter(buyer=self.buyer, restoran=self.restoran, status=False).first()
        self.assertIsNotNone(order, "Order should be created for the buyer.")

        # Check if both items are in the order
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 2, "There should be two items in the order.")

    def test_add_item_to_cart_for_non_buyer(self):
        # Create a non-buyer user (restoran role)
        non_buyer_user = User.objects.create_user(username='testrestoran', password='password', role='restoran')
        self.client.login(username='testrestoran', password='password')

        # Try to add a menu item to the cart
        url = reverse('add_to_cart', args=[self.menu_item.id])
        response = self.client.post(url)

        # Ensure that only buyers can add items to the cart
        self.assertEqual(response.status_code, 403, "Non-buyers should not be able to add items to the cart.")

    def test_cart_contains_correct_item(self):
        # Login the buyer user
        self.client.login(username='testbuyer', password='password')

        # Add the menu item to the cart
        url = reverse('add_to_cart', args=[self.menu_item.id])
        self.client.post(url)

        # Get the cart (order)
        order = Order.objects.filter(buyer=self.buyer, restoran=self.restoran, status=False).first()
        self.assertIsNotNone(order)

        # Check if the cart contains the correct item
        order_item = OrderItem.objects.filter(order=order, menu=self.menu_item).first()
        self.assertEqual(order_item.menu, self.menu_item, "The cart should contain the correct menu item.")
        self.assertEqual(order_item.quantity, 1, "The quantity of the item should be 1.")

