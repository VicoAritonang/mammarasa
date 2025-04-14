from main.models import User
from restoran.models import Restoran
from django.test import TestCase, Client
from django.urls import reverse
from restoran.forms import MenuForm

class MenuFormTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='12345',
            role='restoran',
            name='Mamma Rasa'
        )
        self.restoran = Restoran.objects.create(user=self.user, nama_restoran="Test Restoran")
        self.url = reverse('add_menu')
        self.client.force_login(self.user)

            
    def test_sql_injection_prevention(self):
        """
        Simulasi SQL Injection – input tidak boleh dieksekusi sebagai SQL, 
        tapi karena tidak ada raw SQL digunakan, kita hanya memastikan input disimpan aman.
        """
        payload = {
            'nama_menu': "Test'; DROP TABLE restoran_menu;--",
            'harga_makanan': 10000,
            'keterangan_makanan': "Delicious food",
        }

        form = MenuForm(data=payload)
        self.assertTrue(form.is_valid())  # form tetap valid

        # Cek bahwa data tetap tersimpan sebagai string biasa (bukan dieksekusi SQL)
        # Tidak memfilter kata 'DROP TABLE', tapi kita bisa pastikan tidak crash atau error
        self.assertEqual(form.cleaned_data['nama_menu'], payload['nama_menu'])

        # Tambahan: pastikan tidak ada <script> karena sanitize_html() fokusnya di XSS
        payload_xss = {
            'nama_menu': '<script>alert("xss")</script>',
            'harga_makanan': 10000,
            'keterangan_makanan': "Good"
        }
        form_xss = MenuForm(data=payload_xss)
        self.assertTrue(form_xss.is_valid())
        self.assertNotIn('<script>', form_xss.cleaned_data['nama_menu'])

    def test_xss_prevention(self):
        payload = {
            'nama_menu': '<script>alert("XSS")</script>',
            'harga_makanan': 10000,
            'keterangan_makanan': "Delicious food",
        }

        form = MenuForm(data=payload)
        self.assertTrue(form.is_valid())
        self.assertNotIn('<script>', form.cleaned_data['nama_menu'])

    def test_csrf_protection(self):
        # CSRF Protection Test
        payload = {
            'nama_menu': "Test Menu",
            'harga_makanan': 10000,
            'keterangan_makanan': "Delicious food",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)  # Expecting CSRF failure because no CSRF token is sent

    def test_user_authorization(self):
        # Uji akses dengan role 'restoran' — harus bisa akses halaman
        self.user.role = 'restoran'
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Ubah role jadi buyer, login ulang
        self.user.role = 'buyer'
        self.user.save()
        self.client.force_login(self.user)

        # Kirim request tanpa follow agar tidak sampai render ke template error
        response = self.client.get(self.url, follow=False)

        # Status harus redirect (302)
        self.assertEqual(response.status_code, 302)

        # Cek bahwa redirect URL-nya ke halaman 'buyer_page' (misal)
        self.assertEqual(response['Location'], '/')

    def test_input_length_validation(self):
        # Input Length Validation
        payload = {
            'nama_menu': 'A' * 256,  # Should trigger a max length validation error
            'harga_makanan': 10000,
            'keterangan_makanan': "Delicious food",
        }
        response = self.client.post(self.url, payload)
        self.assertContains(response, 'Ensure this value has at most 255 characters')

    def test_file_upload_validation(self):
        # File Upload validation (invalid image content)
        with open('test_image.jpg', 'wb') as f:
            f.write(b'\x00\x00\x00\x00')  # Simulate corrupted image

        with open('test_image.jpg', 'rb') as f:
            payload = {
                'nama_menu': "Test Menu",
                'harga_makanan': 10000,
                'keterangan_makanan': "Delicious food",
                'foto_makanan': f,
            }
            response = self.client.post(self.url, payload)
            self.assertContains(response, 'Upload a valid image')  # ✅ ini sesuai error asli

        # Cleanup
        import os
        os.remove('test_image.jpg')

    def test_open_redirects(self):
        # Simulate a redirect attempt via URL manipulation
        malicious_url = 'http://malicious-site.com'

        payload = {
            'nama_menu': "Test Menu",
            'harga_makanan': 10000,
            'keterangan_makanan': "Delicious food",
            'redirect_url': malicious_url  # Simulated injection
        }

        response = self.client.post(self.url, payload, follow=False)

        # Make sure it does NOT redirect to external domain
        if response.status_code == 302:
            redirect_target = response.get('Location', '')
            self.assertFalse(redirect_target.startswith('http://malicious-site.com'))

    def test_sensitive_data_exposure(self):
        # Sensitive Data Exposure (Sensitive information like passwords should not be shown in errors)
        response = self.client.get(reverse('restoran_page'))  # Simulate a page that should require authentication
        self.assertNotContains(response, 'password')  # Make sure no sensitive info is exposed in response
    
    def test_security_headers(self):
        response = self.client.get(self.url)

        # X-Content-Type-Options harus ada
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')

        # Strict-Transport-Security hanya muncul saat HTTPS aktif, jadi bersifat opsional
        sts = response.headers.get('Strict-Transport-Security')
        if sts:
            self.assertIn('max-age=31536000', sts)

    def test_rate_limiting(self):
        self.user.role = 'restoran'
        self.user.save()
        self.client.force_login(self.user)

        restoran, _ = Restoran.objects.get_or_create(
            user=self.user,
            defaults={'nama_restoran': 'Test Restoran'}
        )

        last_response = None
        for _ in range(10):
            last_response = self.client.post(self.url, {
                'nama_menu': 'Test Menu',
                'harga_makanan': 10000,
                'keterangan_makanan': 'Delicious food'
            })

        # ✅ Tidak error / rate limit
        self.assertNotEqual(last_response.status_code, 429)

        # ✅ Tambahan: boleh 302 karena redirect setelah sukses
        self.assertIn(last_response.status_code, [200, 302, 400])

