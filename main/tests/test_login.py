from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class LoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')

   # A01: Broken Access Control
    def test_authenticated_user_redirected_from_login(self):
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='StrongPass123!',
            role='buyer'
        )
        self.client.login(username='test@example.com', password='StrongPass123!')
        response = self.client.get(self.login_url, follow=False)  # follow=False untuk hindari error template
        self.assertEqual(response.status_code, 302)  # 302 artinya redirect
        self.assertEqual(response['Location'], reverse('buyer_page'))  # pastikan redirect ke buyer_page

    # A02: Cryptographic Failures - Password should be hashed
    def test_password_is_hashed(self):
        User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='StrongPass123!',
            role='buyer'
        )
        user = User.objects.get(email='test@example.com')
        self.assertTrue(user.password.startswith('pbkdf2'))

    # A03: Injection - prevent login with SQL injection-like input
    def test_sql_injection_attempt_fails(self):
        response = self.client.post(self.login_url, {
            'username': "' OR 1=1 --",
            'password': 'any'
        }, follow=True)  # follow redirect

        self.assertContains(response, 'Invalid', status_code=200)

    # A04: Insecure Design - no GET login processing
    def test_login_not_accepted_via_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    # A05: Security Misconfiguration - form includes CSRF token
    def test_login_page_contains_csrf_token(self):
        response = self.client.get(self.login_url)
        self.assertContains(response, 'csrfmiddlewaretoken')

    # A06: Vulnerable Components - CDN uses HTTPS
    def test_cdn_links_use_https(self):
        response = self.client.get(self.login_url)
        self.assertContains(response, 'https://cdn.jsdelivr.net')
        self.assertContains(response, 'https://cdnjs.cloudflare.com')

   # A07: Identification and Authentication Failures - invalid credentials rejected
    def test_invalid_login_rejected(self):
        response = self.client.post(self.login_url, {
            'username': 'wrong@example.com',
            'password': 'wrongpass'
        }, follow=True)  # follow redirect to get final response content

        self.assertContains(response, 'Invalid', status_code=200)

    # A08: Software/Data Integrity Failures - no unsafe HTML from user input
    def test_script_input_in_login_not_reflected(self):
        malicious_input = '<script>alert(1)</script>'
        response = self.client.post(self.login_url, {
            'username': malicious_input,
            'password': 'StrongPass123!'
        }, follow=True)

        # Pastikan input tidak dipantulkan ke dalam HTML
        self.assertNotContains(response, malicious_input)

    # A09: Logging and Monitoring - failed login doesn't crash
    def test_failed_login_is_handled_gracefully(self):
        response = self.client.post(self.login_url, {
            'username': 'nonexistent@example.com',
            'password': 'wrongpass'
        }, follow=True)  # Follow redirect
        self.assertEqual(response.status_code, 200)

   # A10: SSRF - ensure no dangerous sources like 'file://' or non-https external URLs
    def test_no_external_unsafe_sources(self):
        response = self.client.get(self.login_url)

        # A10: SSRF - should not use file:// at all
        self.assertNotContains(response, 'file://')

        # A10: SSRF - http:// should only come from safe domains
        unsafe_http_sources = ['http://localhost', 'http://127.0.0.1', 'http://example.com']

        for source in unsafe_http_sources:
            self.assertNotIn(source, response.content.decode())
