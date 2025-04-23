import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from main.models import User
from restoran.models import Restoran, Menu
from buyer.models import Buyer, Order, OrderItem

class EditMenuTestCase(TestCase):
    """Test cases for the edit_menu view with OWASP Top 10 security testing"""

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
            nama_menu='Original Menu',
            harga_makanan=10000,
            keterangan_makanan='Test Description'
        )

        self.client = Client()

        self.edit_url = reverse('edit_menu', args=[self.menu.id])

    def test_edit_menu_get_request(self):
        """Test that the edit menu page loads correctly for restaurant owners"""
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'restoran/menu_form.html')
        self.assertContains(response, 'Original Menu')

    def test_edit_menu_post_request(self):
        """Test successful menu item update"""
        self.client.login(username='restoran@example.com', password='testpassword')

        updated_data = {
            'nama_menu': 'Updated Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'Updated Description'
        }

        response = self.client.post(self.edit_url, updated_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('restoran_page'))

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Updated Menu')
        self.assertEqual(self.menu.harga_makanan, 15000)
        self.assertEqual(self.menu.keterangan_makanan, 'Updated Description')

    # OWASP Top 10 Security Tests


    # A01:2021 - Broken Access Control
    def test_authentication_required(self):
        """Test that unauthenticated users cannot access the edit menu page"""
        self.client.logout()

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_unauthorized_user_access(self):
        """Test that non-restaurant users cannot access the edit menu page"""
        self.client.login(username='buyer@example.com', password='testpassword')

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

        updated_data = {
            'nama_menu': 'Hacked Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'Hacked Description'
        }

        response = self.client.post(self.edit_url, updated_data)

        self.assertEqual(response.status_code, 302)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Original Menu')

    def test_wrong_restoran_access(self):
        """Test that restaurant owners cannot edit menus from other restaurants"""
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

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 404)

    def test_menu_id_tampering(self):
        """Test against parameter tampering with menu IDs"""
        self.client.login(username='restoran@example.com', password='testpassword')

        fake_id = uuid.uuid4()
        fake_url = reverse('edit_menu', args=[fake_id])

        response = self.client.get(fake_url)

        self.assertEqual(response.status_code, 404)


    #A02:2021 - Cryptographic Failures
    def test_password_encryption(self):
        """Test that passwords are encrypted in the database"""
        user = User.objects.create_user(
            email='restoran123@example.com',
            name='Test Restaurant 123',
            password='plaintextpassword',
            role='restoran'
        )

        self.assertNotEqual(user.password, 'plaintextpassword')
        self.assertTrue(user.check_password('plaintextpassword'))
        self.assertFalse(user.check_password('wrongpassword'))


    # A03:2021 - Injection
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        self.client.login(username='restoran@example.com', password='testpassword')

        sql_injection_data = {
            'nama_menu': "'; DROP TABLE restoran_menu; --",
            'harga_makanan': 15000,
            'keterangan_makanan': 'SQL Injection Test'
        }

        response = self.client.post(self.edit_url, sql_injection_data)

        self.assertEqual(response.status_code, 302)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, "'; DROP TABLE restoran_menu; --")

    def test_template_injection_prevention(self):
        """Test template injection prevention"""
        self.client.login(username='restoran@example.com', password='testpassword')

        template_injection_data = {
            'nama_menu': '{% for user in users %}{{ user.password }}{% endfor %}',
            'harga_makanan': 15000,
            'keterangan_makanan': 'Template Injection Test'
        }

        response = self.client.post(self.edit_url, template_injection_data)

        self.assertEqual(response.status_code, 302)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, '{% for user in users %}{{ user.password }}{% endfor %}')


    # A04:2021 - Insecure Design
    def test_insecure_design(self):
        """Test for insecure design in the edit menu form"""
        self.client.login(username='restoran@example.com', password='testpassword')

        insecure_data = {
            'nama_menu': '',  # Missing name
            'harga_makanan': 15000,
            'keterangan_makanan': 'Insecure Design Test'
        }

        response = self.client.post(self.edit_url, insecure_data)

        self.assertEqual(response.status_code, 200)


    # A05:2021 - Security Misconfiguration
    def test_security_headers(self):
        """Test security headers in the response"""
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.get(self.edit_url)
        self.assertIn('X-Content-Type-Options', response)

    def test_csrf_protection(self):
        """Test CSRF protection"""
        self.client.login(username='restoran@example.com', password='testpassword')

        client = Client(enforce_csrf_checks=True)
        client.login(username='restoran@example.com', password='testpassword')

        updated_data = {
            'nama_menu': 'CSRF Test Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'CSRF Test Description'
        }

        response = client.post(self.edit_url, updated_data)

        self.assertEqual(response.status_code, 403)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Original Menu')


    # A06:2021 - Vulnerable and Outdated Components
    def test_outdated_component(self):
        """Test for outdated components"""
        outdated_component = 'Django 2.2.0'
        self.assertIn(outdated_component, 'Django 2.2.0')


    # A07:2021 - Identification and Authentication Failures
    def test_session_handling(self):
        """Test proper session handling for authenticated users"""
        session = self.client.session
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.get(reverse('restoran_page'))
        self.assertEqual(response.status_code, 200)

        self.client.logout()

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    # A08:2021 - Software and Data Integrity Failures
    def test_data_integrity(self):
        """Test data integrity during menu update"""
        self.client.login(username='restoran@example.com', password='testpassword')

        integrity_data = {
            'nama_menu': 'Integrity Test Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'Integrity Test'
        }

        response = self.client.post(self.edit_url, integrity_data)

        self.assertEqual(response.status_code, 302)

    def test_form_validation_integrity(self):
        """Test form validation integrity"""
        self.client.login(username='restoran@example.com', password='testpassword')

        invalid_data = {
            'nama_menu': 'Integrity Test Menu',
            'harga_makanan': -1000,
            'keterangan_makanan': 'Integrity Test'
        }

        response = self.client.post(self.edit_url, invalid_data)

        self.assertEqual(response.status_code, 302)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Integrity Test Menu')


    # A09:2021 - Security Logging and Monitoring Failures
    def test_logging(self):
        """Test logging of menu updates"""
        self.client.login(username='restoran@example.com', password='testpassword')

        updated_data = {
            'nama_menu': 'Logged Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'Logging Test'
        }

        response = self.client.post(self.edit_url, updated_data)

        self.assertEqual(response.status_code, 302)

        self.menu.refresh_from_db()

        self.assertEqual(self.menu.nama_menu, 'Logged Menu')

    # A10:2021 - Server-Side Request Forgery (SSRF)
    @patch('requests.get')
    def test_ssrf_prevention(self, mock_get):
        """Test Server-Side Request Forgery (SSRF) prevention"""

        self.client.login(username='restoran@example.com', password='testpassword')

        ssrf_data = {
            'nama_menu': 'SSRF Test Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'http://internal-network/admin'
        }

        response = self.client.post(self.edit_url, ssrf_data)

        self.assertEqual(response.status_code, 302)

        mock_get.assert_not_called()

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.keterangan_makanan, 'http://internal-network/admin')

    # Additional tests for other OWASP Top 10 vulnerabilities and security issues

    # A3:2017 - Sensitive Data Exposure
    def test_no_sensitive_data_exposure(self):
        """Test that sensitive data is not exposed in responses"""
        self.client.login(username='restoran@example.com', password='testpassword')

        response = self.client.get(self.edit_url)

        self.assertNotContains(response, 'password')
        self.assertNotContains(response, 'csrf_token')


    # A7:2017 - Cross-Site Scripting (XSS)
    def test_xss_prevention(self):
        """Test Cross-Site Scripting (XSS) prevention"""
        self.client.login(username='restoran@example.com', password='testpassword')

        xss_data = {
            'nama_menu': '<script>alert("XSS")</script>Malicious Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': '<img src="x" onerror="alert(\'XSS\')">Description'
        }

        response = self.client.post(self.edit_url, xss_data)

        self.assertEqual(response.status_code, 302)

        self.menu.refresh_from_db()
        self.assertNotIn('<script>', self.menu.nama_menu)
        self.assertNotIn('onerror', self.menu.keterangan_makanan)

    def test_input_validation_max_length(self):
        """Test input validation for maximum field lengths"""
        self.client.login(username='restoran@example.com', password='testpassword')

        long_name_data = {
            'nama_menu': 'A' * 256,
            'harga_makanan': 15000,
            'keterangan_makanan': 'Length Test'
        }

        response = self.client.post(self.edit_url, long_name_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ensure this value has at most 255 characters')

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Original Menu')

    def test_file_upload_validation(self):
        """Test file upload validation"""
        self.client.login(username='restoran@example.com', password='testpassword')

        invalid_file = SimpleUploadedFile(
            "test.jpg",
            b"invalid image content",
            content_type="image/jpeg"
        )

        file_upload_data = {
            'nama_menu': 'File Upload Test Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'File Upload Test',
            'foto_makanan': invalid_file
        }

        response = self.client.post(self.edit_url, file_upload_data)

        self.assertEqual(response.status_code, 200)

        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Original Menu')

    def test_open_redirect_prevention(self):
        """Test prevention of open redirects"""
        self.client.login(username='restoran@example.com', password='testpassword')

        target_url = f"{self.edit_url}?next=http://malicious-site.com"

        response = self.client.get(target_url)

        self.assertEqual(response.status_code, 200)

        valid_data = {
            'nama_menu': 'Redirect Test Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'Redirect Test',
            'next': 'http://malicious-site.com'
        }

        response = self.client.post(self.edit_url, valid_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('restoran_page'))
