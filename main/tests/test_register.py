# Cara run : 
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')  # pastikan nama URL-nya sesuai

    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create your account')

    def test_register_with_valid_data(self):
        response = self.client.post(self.register_url, {
            'name': 'Test User',
            'email': 'test@example.com',
            'role': 'buyer',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })

        # Pastikan redirect ke halaman OTP (atau halaman yang sesuai)
        self.assertRedirects(response, reverse('verify_otp'))

        # Cek apakah user dengan email tersebut berhasil dibuat
        user_exists = User.objects.filter(email='test@example.com').exists()
        self.assertTrue(user_exists)

        # Cek apakah user tersebut belum aktif (karena OTP belum diverifikasi)
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.is_active)
        
    # A01: Broken Access Control - Authenticated user should be redirected
    def test_authenticated_user_redirected_from_register(self):
        # Buat dan login user
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='Test123!',
            role='buyer'
        )
        self.client.login(username='test@example.com', password='Test123!')

        # Akses halaman register (tanpa follow=True agar tidak error render)
        response = self.client.get(self.register_url)

        # Cek redirect (kode status)
        self.assertEqual(response.status_code, 302)

        # Cek URL tujuan redirect (biasanya ke 'home' atau sesuai dengan logika kamu)
        self.assertIn(reverse('home'), response.url)

    # A02: Cryptographic Failures - Ensure password is not stored as plain text
    def test_password_is_hashed_on_registration(self):
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'password1': 'StrongPass1!',
            'password2': 'StrongPass1!',
            'role': 'buyer'
        }
        response = self.client.post(self.register_url, data)
        user = User.objects.filter(email='john@example.com').first()
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password, 'StrongPass1!')
        self.assertTrue(user.password.startswith('pbkdf2'))

    # A03: Injection - Prevent HTML/script injection on name field
    def test_html_injection_in_name_field(self):
        malicious_name = "<script>alert('x')</script>"
        data = {
            'name': malicious_name,
            'email': 'inject@example.com',
            'password1': 'StrongPass1!',
            'password2': 'StrongPass1!',
            'role': 'buyer'
        }
        self.client.post(self.register_url, data)
        user = User.objects.filter(email='inject@example.com').first()
        self.assertNotIn('<script>', user.name)

    # A04: Insecure Design - Mismatched passwords should fail
    def test_registration_fails_on_mismatched_passwords(self):
        data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'password1': 'Password1!',
            'password2': 'Password2!',
            'role': 'buyer'
        }
        response = self.client.post(self.register_url, data)
        self.assertContains(response, 'Passwords do not match')
        self.assertEqual(User.objects.filter(email='jane@example.com').count(), 0)

    # A05: Security Misconfiguration - Captcha field presence
    def test_captcha_input_present_in_form(self):
        response = self.client.get(self.register_url)
        self.assertContains(response, 'id="captchaInputLogin"')

    # A06: Vulnerable Components - CDN uses HTTPS
    def test_cdn_links_use_https(self):
        response = self.client.get(self.register_url)
        self.assertContains(response, 'https://cdn.jsdelivr.net/npm/tailwindcss')
        self.assertContains(response, 'https://cdnjs.cloudflare.com')

    # A07: Identification and Authentication Failures - Weak password blocked
    def test_weak_password_is_rejected(self):
        data = {
            'name': 'Weak User',
            'email': 'weak@example.com',
            'password1': 'weak',
            'password2': 'weak',
            'role': 'buyer'
        }
        response = self.client.post(self.register_url, data)
        self.assertContains(response, 'Password must be at least 8 characters long.')

    # A08: Software/Data Integrity Failures - Ensure no unsafe script in form values
    def test_register_view_blocks_script_submission(self):
        data = {
            'name': "<img src=x onerror=alert(1)>",
            'email': 'safe@example.com',
            'password1': 'SecurePass1!',
            'password2': 'SecurePass1!',
            'role': 'buyer'
        }

        response = self.client.post(self.register_url, data)

        # User should not be created
        user = User.objects.filter(email='safe@example.com').first()
        self.assertIsNone(user)

        # Make sure validation error appears because sanitized name became empty
        self.assertContains(response, "This field cannot be blank.", status_code=200)

    # A09: Security Logging and Monitoring Failures - Simulate failed registration and check system logs (simplified here)
    def test_failed_registration_is_handled_gracefully(self):
        data = {
            'name': '',
            'email': 'error@example.com',
            'password1': 'Short1!',
            'password2': 'Short1!',
            'role': 'buyer'
        }
        response = self.client.post(self.register_url, data)
        self.assertContains(response, 'This field is required', html=False)

    # A10: SSRF - QR not relevant here, just ensure no SSRF-prone fields exist
    def test_no_external_api_call_on_register(self):
        response = self.client.get(self.register_url)
        self.assertNotIn('src="http://', response.content.decode())
        self.assertNotIn("href='http://", response.content.decode())
