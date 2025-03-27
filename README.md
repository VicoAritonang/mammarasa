# Mamma Rasa Restaurant Website

Aplikasi web Django untuk membantu restoran menampilkan menu secara online. Sistem memiliki dua peran utama: pengguna restoran dan pembeli.

## Fitur Keamanan

Website ini menerapkan beberapa lapisan keamanan:

1. **Sanitasi Input (Anti-XSS)**
   - Menggunakan Bleach untuk membersihkan input HTML dari tag berbahaya
   - Melindungi dari serangan Cross-Site Scripting (XSS)

2. **Database PostgreSQL**
   - Menggunakan PostgreSQL sebagai database relasional yang lebih aman dan skalabel

3. **Enkripsi Data**
   - Enkripsi password menggunakan algoritma hashing Django
   - Enkripsi OTP dengan Fernet (symmetric encryption)
   - ID restoran di QR code dienkripsi dengan Caesar cipher

4. **TLS/HTTPS**
   - Konfigurasi HTTPS untuk komunikasi terenkripsi
   - HSTS untuk mencegah downgrade attack
   - Cookies secure untuk melindungi sesi

## Instalasi

1. **Clone repositori**
   ```
   git clone <repo-url>
   cd mammarasa
   ```

2. **Buat lingkungan virtual Python**
   ```
   python -m venv env
   source env/bin/activate  # Linux/macOS
   env\Scripts\activate     # Windows
   ```

3. **Instal dependensi**
   ```
   pip install -r requirements.txt
   ```

4. **Siapkan database PostgreSQL**
   - Buat database PostgreSQL baru
   - Sesuaikan `DATABASES` di `settings.py` dengan kredensial PostgreSQL Anda

5. **Jalankan migrasi**
   ```
   python manage.py migrate
   ```

6. **Buat superuser**
   ```
   python manage.py createsuperuser
   ```

7. **Jalankan server dengan HTTPS (development)**
   ```
   python manage.py runserver_plus --cert-file=cert.crt
   ```

## Test XSS Protection

Untuk menguji proteksi XSS, coba masukkan skrip berbahaya di form berikut:

1. Form login: `<script>alert('XSS')</script>` di field email
2. Form registrasi: `<script>alert('XSS')</script>` di field nama
3. Form tambah menu: `<img src="x" onerror="alert('XSS')">` di field keterangan

## Lingkungan Produksi

Untuk deployment produksi:

1. Set `DEBUG = False` di settings.py
2. Gunakan sertifikat TLS/SSL yang valid
3. Pastikan semua pengaturan keamanan diaktifkan
4. Gunakan web server seperti Nginx atau Apache dengan Gunicorn 