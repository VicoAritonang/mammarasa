from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from restoran.models import Restoran, Menu
from django.contrib.messages import get_messages
import logging

# Initialize the logger
logger = logging.getLogger(__name__)

class MenuVisibilityTest(TestCase):

    def setUp(self):
        # Create a user with 'restoran' role and a restaurant
        self.user = User.objects.create_user(username='testuser', password='password', role='restoran')
        self.restoran = Restoran.objects.create(user=self.user, nama_restoran='Test Restaurant')
        self.menu = Menu.objects.create(nama_menu="Test Menu", restoran=self.restoran, is_visible=True)

    def test_toggle_menu_visibility(self):
        """Test toggling the menu visibility (hide/show)."""
        
        # Ensure menu is initially visible
        self.assertTrue(self.menu.is_visible)

        # Login the user (restoran role)
        self.client.login(username='testuser', password='password')

        # Log the action
        logger.info(f'User {self.user.username} is toggling visibility for menu: {self.menu.nama_menu}')

        # URL to toggle menu visibility
        url = reverse('toggle_menu_visibility', args=[self.menu.id])

        # Toggle visibility
        response = self.client.post(url)

        # Refresh the menu object to check updated status
        self.menu.refresh_from_db()
        
        # Check if the menu visibility is now toggled
        self.assertFalse(self.menu.is_visible)

        # Ensure the user is redirected back to the restaurant page
        self.assertRedirects(response, reverse('restoran_page'))

        # Ensure a success message is displayed
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), f'Menu "{self.menu.nama_menu}" is now hidden.')

    def test_non_restoran_user_access(self):
        """Test that non-restoran users cannot toggle menu visibility."""
        
        # Create a non-restoran user (buyer role)
        non_restoran_user = User.objects.create_user(username='testbuyer', password='password', role='buyer')
        self.client.login(username='testbuyer', password='password')

        # Try to toggle the menu visibility
        url = reverse('toggle_menu_visibility', args=[self.menu.id])
        response = self.client.post(url)

        # Ensure that non-restoran users cannot toggle visibility
        self.assertEqual(response.status_code, 403, "Non-restoran users should not be able to toggle menu visibility.")

    def test_csrf_protection(self):
        """Test that CSRF protection is working for menu visibility toggle."""
        
        # Simulate a non-POST request to check if CSRF protection is applied
        url = reverse('toggle_menu_visibility', args=[self.menu.id])

        # Try to toggle menu visibility without CSRF token
        response = self.client.get(url)
        
        # Ensure that CSRF is being protected
        self.assertEqual(response.status_code, 403, "CSRF protection should prevent unauthorized POST requests.")
