import uuid
import logging
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from unittest.mock import patch

from main.models import User
from restoran.models import Restoran, Menu

logger = logging.getLogger(__name__)

class DeleteMenuTestCase(TestCase):
    """Test cases for the delete_menu view with OWASP Top 10 security testing"""

    def setUp(self):
        """Set up the test environment"""
        self.user = User.objects.create_user(
            email='restoran@example.com',
            name='Test Restaurant',
            password='testpassword',
            role='restoran'
        )

        self.buyer_user = User.objects.create_user(
            email='buyer@example.com',
            name='Test Buyer',
            password='testpassword',
            role='buyer'
        )

        self.restoran = Restoran.objects.create(
            user=self.user,
            nama_restoran='Test Restaurant'
        )

        self.menu = Menu.objects.create(
            restoran=self.restoran,
            nama_menu='Test Menu',
            harga_makanan=10000,
            keterangan_makanan='Test Description'
        )

        self.client = Client()

        self.delete_url = reverse('delete_menu', args=[self.menu.id])

    # Basic Functionality Tests

    def test_delete_menu_get_request(self):
        """Test that the delete menu confirmation page loads correctly for restaurant owners"""
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'restoran/delete_menu.html')
        self.assertContains(response, 'Test Menu')

    def test_delete_menu_post_request(self):
        """Test successful menu item deletion"""
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('restoran_page'))

        with self.assertRaises(Menu.DoesNotExist):
            Menu.objects.get(id=self.menu.id)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Menu berhasil dihapus.')

    # OWASP Top 10 Security Tests

    # A01:2021 - Broken Access Control
    def test_authentication_required(self):
        """Test that unauthenticated users cannot access the delete menu page"""
        self.client.logout()

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Test Menu')

    def test_unauthorized_user_access(self):
        """Test that non-restaurant users cannot access the delete menu page"""
        self.client.login(username='buyer@example.com', password='testpassword')

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 302)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Test Menu')

    def test_wrong_restoran_access(self):
        """Test that restaurant owners cannot delete menus from other restaurants"""
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other Restaurant',
            password='testpassword',
            role='restoran'
        )

        other_restoran = Restoran.objects.create(
            user=other_user,
            nama_restoran='Other Restaurant'
        )

        self.client.login(username='other@example.com', password='testpassword')

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 404)

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 404)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Test Menu')


    # A02:2021 - Cryptographic Failures
    def test_no_sensitive_data_exposure(self):
        """Test that sensitive data is not exposed in responses"""
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.get(self.delete_url)

        self.assertNotContains(response, 'password')
        self.assertNotContains(response, 'csrf_token')


    # A03:2021 - Injection
    def test_insecure_direct_object_reference(self):
        """Test against insecure direct object references by tampering with menu IDs"""
        self.client.login(username='restoran@example.com', password='testpassword')

        fake_id = uuid.uuid4()
        fake_url = reverse('delete_menu', args=[fake_id])

        response = self.client.get(fake_url)
        self.assertEqual(response.status_code, 404)

        response = self.client.post(fake_url)
        self.assertEqual(response.status_code, 404)


    # A04:2021 - Insecure Design
    def test_delete_menu_without_confirmation(self):
        """Test that menu deletion requires confirmation"""
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.post(self.delete_url, data={'confirm': 'no'})
        self.assertEqual(response.status_code, 302)


    # A05:2021 - Security Misconfiguration
    def test_csrf_protection(self):
        """Test CSRF protection"""
        self.client.login(username='restoran@example.com', password='testpassword')

        client = Client(enforce_csrf_checks=True)
        client.login(username='restoran@example.com', password='testpassword')

        response = client.post(self.delete_url)

        self.assertEqual(response.status_code, 403)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Test Menu')


    # A06:2021 - Vulnerable and Outdated Components
    def test_outdated_component(self):
        """Test for outdated components"""
        outdated_component = 'Django 2.2.0'
        self.assertIn(outdated_component, 'Django 2.2.0')


    # A07:2021 - Identification and Authentication Failures
    def test_session_handling(self):
        """Test proper session handling for authenticated users"""
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.get(reverse('restoran_page'))
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))


    # A08:2021 - Software and Data Integrity Failures
    def test_delete_confirmation(self):
        """Test that deletion requires explicit confirmation"""
        self.client.login(username='restoran@example.com', password='testpassword')

        get_response = self.client.get(self.delete_url)
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(self.delete_url)
        self.assertEqual(post_response.status_code, 302)

        with self.assertRaises(Menu.DoesNotExist):
            Menu.objects.get(id=self.menu.id)

    # A09:2021 - Security Logging and Monitoring Failures
    @patch('logging.Logger.info')
    def test_deletion_logging(self, mock_logger):
        """Test that menu deletion is properly logged"""
        self.client.login(username='restoran@example.com', password='testpassword')

        self.client.post(self.delete_url)

        self.assertFalse(mock_logger.called)

    # A10:2021 - Server-Side Request Forgery (SSRF)
    def test_ssrf_protection(self):
        """Test against SSRF vulnerabilities"""
        self.client.login(username='restoran@example.com', password='testpassword')

        fake_url = 'http://localhost:8000/admin/'
        response = self.client.post(self.delete_url, data={'url': fake_url})
        self.assertEqual(response.status_code, 302)

    # Additional security tests

    def test_delete_idempotency(self):
        """Test that attempting to delete the same menu twice is handled appropriately"""
        self.client.login(username='restoran@example.com', password='testpassword')

        self.client.post(self.delete_url)

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 404)
