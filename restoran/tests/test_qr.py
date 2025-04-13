# tests/test_qr.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from restoran.models import Restoran


class GenerateQrTest(TestCase):

    def setUp(self):
        # Create a user and a restaurant
        self.user = User.objects.create_user(username='testuser', password='password', role='restoran')
        self.restoran = Restoran.objects.create(user=self.user, nama_restoran='Test Restaurant')

    @patch('requests.get')  # Mock the external API call for QR code generation
    def test_generate_qr(self, mock_get):
        # Mock the response from the QR code API
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"Fake QR code image content"
        
        # Login the user
        self.client.login(username='testuser', password='password')
        
        # URL to generate the QR code
        url = reverse('generate_qr')
        
        # Generate QR code
        response = self.client.get(url)

        # Check that the QR code image is saved in the restaurant
        self.restoran.refresh_from_db()
        self.assertTrue(self.restoran.qrcode.name.endswith('.png'))  # Ensure QR code image file exists

        # Ensure the generated QR code URL is present in the context
        self.assertContains(response, 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=')

        # Ensure the correct response type (HTML page)
        self.assertEqual(response.status_code, 200)
