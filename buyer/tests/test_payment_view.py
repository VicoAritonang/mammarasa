# Cara run test : python manage.py test buyer.tests.test_payment_view

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from buyer.models import Buyer, Order, OrderItem
from restoran.models import Restoran, Menu

User = get_user_model()

class PaymentViewAccessControlTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='buyer@example.com',
            password='password123',
            name='Buyer Test',
            role='buyer'
        )
        self.client.login(username='buyer@example.com', password='password123')

        self.restoran = Restoran.objects.create(nama_restoran='Test Resto', user=self.user)
        self.menu = Menu.objects.create(restoran=self.restoran, nama_menu='Test Menu', harga_makanan=20000)

        self.buyer = Buyer.objects.create(user=self.user)
        self.order = Order.objects.create(buyer=self.buyer, restoran=self.restoran, status=False)
        OrderItem.objects.create(order=self.order, menu=self.menu, quantity=1)

        self.payment_url = reverse('payment', args=[str(self.order.id)])

    # A01: Broken Access Control
    def test_payment_requires_login(self):
        self.client.logout()
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)

    # A02: Cryptographic Failures
    def test_password_not_visible_in_payment(self):
        response = self.client.get(self.payment_url)
        self.assertNotContains(response, self.user.password)
        self.assertNotContains(response, "pbkdf2_sha256")
        self.assertNotContains(response, "password")

    # A03: Injection
    def test_no_injection_possible_in_payment_url(self):
        response = self.client.get(self.payment_url + "?order_id=1;DROP TABLE user")
        self.assertEqual(response.status_code, 200) 
        self.assertNotContains(response, "error")

    # A04: Insecure Design
    def test_user_cannot_access_other_users_order(self):
        # Buat user lain yang bukan pemilik order
        other_user = User.objects.create_user(
            email="other@example.com",
            password="123",
            name="Other User",      
            role="buyer"
        )
        self.client.login(username="other@example.com", password="123")

        response = self.client.get(self.payment_url)

        self.assertEqual(response.status_code, 404)  


    # A05: Security Misconfiguration
    def test_payment_response_has_security_headers(self):
        response = self.client.get(self.payment_url)
        self.assertIn('X-Frame-Options', response.headers)
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')

    # A06: Vulnerable Components
    def test_tailwind_or_assets_use_https(self):
        response = self.client.get(self.payment_url)
        self.assertContains(response, "https://cdn.jsdelivr.net/npm/tailwindcss")

   # A07: Identification and Authentication Failures
    def test_payment_requires_authenticated_user(self):
        self.client.logout()  # Simulasi user belum login
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, 302)  
        self.assertIn('/login', response.url)   

    # A08: Software and Data Integrity Failures
    def test_payment_page_does_not_allow_script_injection(self):
        response = self.client.get(self.payment_url)

        # Pastikan tidak ada <script> berasal dari input pengguna
        self.assertNotIn("<script>alert(", response.content.decode())
        self.assertNotIn("onerror=", response.content.decode())
        self.assertNotIn("javascript:", response.content.decode())

    # A09: Security Logging and Monitoring Failures
    def test_unauthorized_access_logs_or_denies(self):
        # Buat user pemilik order
        owner_user = User.objects.create_user(
            email="owner@example.com",
            password="abc123",
            name="Owner",
            role="buyer"
        )
        buyer = Buyer.objects.create(user=owner_user)

        # Cek field-field yang valid di model Restoran, misalnya nama_restoran dan user
        restoran_owner = User.objects.create_user(
            email="resto@example.com",
            password="resto123",
            name="Resto Owner",
            role="restoran"
        )

        restoran = Restoran.objects.create(
            nama_restoran="Resto Aman",
            user=restoran_owner  # pastikan ini sesuai model kamu
        )

        # Buat order oleh buyer asli
        order = Order.objects.create(buyer=buyer, restoran=restoran)

        # Buat user penyusup
        intruder = User.objects.create_user(
            email="intruder@example.com",
            password="abc",
            name="Intruder",
            role="buyer"
        )
        self.client.login(username="intruder@example.com", password="abc")

        # Akses URL pembayaran untuk order milik orang lain
        payment_url = reverse('payment', args=[str(order.id)])
        response = self.client.get(payment_url)

        # Seharusnya tidak boleh akses (403 Forbidden)
        self.assertEqual(response.status_code, 404)


    # A10: Server Side Request Forgery (SSRF)
    def test_payment_qr_code_uses_safe_public_api(self):
        response = self.client.get(self.payment_url)
        self.assertContains(response, "https://api.qrserver.com")  # contoh API QR code aman

    # Bonus Test: Normal rendering
    def test_payment_page_renders_correctly(self):
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pembayaran")
        self.assertContains(response, self.menu.nama_menu)
        self.assertContains(response, "Unduh QR Code")
