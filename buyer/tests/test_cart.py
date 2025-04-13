# Cara run test : python manage.py test buyer.tests.test_cart    

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from buyer.models import Buyer, Order, OrderItem
from restoran.models import Restoran, Menu

User = get_user_model()

class OWASPTop10CartTests(TestCase):
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


    # A01: Broken Access Control
    def test_cart_access_requires_login(self):
        self.client.logout()  # pastikan tidak login

        response = self.client.get(self.view_cart_url)

        # Harus redirect ke login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

   # A02: Cryptographic Failures
    def test_password_not_leaked_in_cart(self):
        # Login dengan email (karena USERNAME_FIELD = 'email')
        login_success = self.client.login(username='buyer@example.com', password='Password123!')
        self.assertTrue(login_success)

        # Akses view_cart
        response = self.client.get(self.view_cart_url)

        # Pastikan field password hash tidak muncul secara tidak sengaja di halaman
        self.assertNotContains(response, 'pbkdf2_sha256')
        self.assertNotContains(response, 'Password123!')
        self.assertNotContains(response, self.user.password)  # optional


    # A03: Injection
    def test_update_cart_rejects_invalid_quantity(self):
        login_success = self.client.login(username='buyer@example.com', password='Password123!')
        self.assertTrue(login_success)

        with self.assertRaises(ValueError):
            self.client.post(self.update_url, {
                'quantity': "1; DROP TABLE buyer_orderitem;"
            })


    # A04: Insecure Design
    def test_user_cannot_update_other_users_cart(self):
        # Buat user penyusup dengan email karena pakai USERNAME_FIELD = 'email'
        another_user = User.objects.create_user(
            email='intruder@example.com',
            name='Intruder',
            password='intruderpass',
            role='buyer'
        )

        # Login sebagai user penyusup
        login_success = self.client.login(username='intruder@example.com', password='intruderpass')
        self.assertTrue(login_success)

        # Coba akses update item milik user lain
        response = self.client.post(self.update_url, {'quantity': 2})

        # Harus ditolak
        self.assertEqual(response.status_code, 403)

    # A05: Security Misconfiguration
    def test_response_has_security_headers(self):
        login_success = self.client.login(username='buyer@example.com', password='Password123!')
        self.assertTrue(login_success)

        response = self.client.get(self.view_cart_url)

        # X-Frame-Options harus diset untuk mencegah clickjacking
        self.assertIn('X-Frame-Options', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')

    # A06: Vulnerable Components
    def test_tailwind_cdn_loaded_securely(self):
        login_success = self.client.login(username='buyer@example.com', password='Password123!')
        self.assertTrue(login_success)

        response = self.client.get(self.view_cart_url)

        # Tailwind CDN harus pakai HTTPS
        self.assertContains(response, 'https://cdn.tailwindcss.com')

    # A07: Identification and Authentication Failures
    def test_checkout_requires_authenticated_user(self):
        self.client.logout()  # pastikan tidak login

        response = self.client.get(self.checkout_url)

        # Harus redirect ke login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    # A08: Software/Data Integrity Failures
    def test_update_cart_blocks_code_execution(self):
        login_success = self.client.login(username='buyer@example.com', password='Password123!')
        self.assertTrue(login_success)

        with self.assertRaises(ValueError):
            self.client.post(self.update_url, {
                'quantity': "__import__('os').system('rm -rf /')"
            })
    # A09: Security Logging and Monitoring
    def test_unauthorized_cart_update_logs_or_denies(self):
        # Buat user penyusup
        other_user = User.objects.create_user(
            email='unauth@example.com',
            name='Unauthorized User',
            password='123',
            role='buyer'
        )

        # Login sebagai user tersebut
        login_success = self.client.login(username='unauth@example.com', password='123')
        self.assertTrue(login_success)

        # Coba update cart item milik user lain
        response = self.client.post(self.update_url, {'quantity': 2})

        # Sistem harus menolak (403 Forbidden)
        self.assertEqual(response.status_code, 403)

    # A10: Server-Side Request Forgery (SSRF)
    def test_payment_qr_code_generation_safe(self):
        login_success = self.client.login(username='buyer@example.com', password='Password123!')
        self.assertTrue(login_success)

        response = self.client.get(reverse('payment', args=[str(self.order.id)]))

        # Pastikan QR code berasal dari public API yang aman
        self.assertContains(response, "https://api.qrserver.com")