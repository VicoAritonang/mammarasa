# tests/test_visibility.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from restoran.models import Restoran, Menu
from django.contrib.messages import get_messages

class MenuVisibilityTest(TestCase):

    def setUp(self):
        # Create a user and a restaurant
        self.user = User.objects.create_user(username='testuser', password='password', role='restoran')
        self.restoran = Restoran.objects.create(user=self.user, nama_restoran='Test Restaurant')
        self.menu = Menu.objects.create(nama_menu="Test Menu", restoran=self.restoran, is_visible=True)

    def test_toggle_menu_visibility(self):
        # Ensure menu is initially visible
        self.assertTrue(self.menu.is_visible)

        # Login the user
        self.client.login(username='testuser', password='password')

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
