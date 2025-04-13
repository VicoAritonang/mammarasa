from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from restoran.models import Menu, Restoran
from main.models import User

class MenuTestCase(TestCase):
    def setUp(self):
        # Membuat user restoran dan login
        self.user = User.objects.create_user(username='restoran_user', password='password', role='restoran')
        self.restoran = Restoran.objects.create(user=self.user, nama_restoran='Restoran Test')
        
        # Menambahkan menu ke restoran
        self.menu = Menu.objects.create(
            restoran=self.restoran,
            nama_menu='Test Menu',
            harga_makanan=10000,
            keterangan_makanan='Test Description'
        )

    def test_edit_menu(self):
        self.client.login(username='restoran_user', password='password')

        # URL untuk mengedit menu
        url = reverse('edit_menu', args=[self.menu.id])

        # Data yang akan diubah
        data = {
            'nama_menu': 'Updated Menu',
            'harga_makanan': 15000,
            'keterangan_makanan': 'Updated Description',
        }

        # Simulasi post request untuk edit menu
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)

        # Memastikan menu sudah terupdate
        self.menu.refresh_from_db()
        self.assertEqual(self.menu.nama_menu, 'Updated Menu')
        self.assertEqual(self.menu.harga_makanan, 15000)
        self.assertEqual(self.menu.keterangan_makanan, 'Updated Description')

        # Cek XSS
        self.assertNotIn("<script>", response.content.decode())

    def test_delete_menu(self):
        self.client.login(username='restoran_user', password='password')

        # URL untuk menghapus menu
        url = reverse('delete_menu', args=[self.menu.id])

        # Simulasi post request untuk delete menu
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)

        # Memastikan menu sudah terhapus
        with self.assertRaises(Menu.DoesNotExist):
            self.menu.refresh_from_db()

        # Cek XSS
        self.assertNotIn("<script>", response.content.decode())

    def test_sql_injection_prevention(self):
        malicious_input = "' OR 1=1 --"
        url = reverse('edit_menu', args=[self.menu.id])
        data = {
            'nama_menu': malicious_input,
            'harga_makanan': 15000,
            'keterangan_makanan': 'Test SQL Injection',
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.menu.refresh_from_db()
        self.assertNotEqual(self.menu.nama_menu, malicious_input)

    def test_csrf_protection(self):
        url = reverse('edit_menu', args=[self.menu.id])
        data = {'nama_menu': 'Malicious Menu'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)

    def test_access_control(self):
        guest_user = get_user_model().objects.create_user(username='guest_user', password='password')
        self.client.login(username='guest_user', password='password')

        url = reverse('edit_menu', args=[self.menu.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        url = reverse('delete_menu', args=[self.menu.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
