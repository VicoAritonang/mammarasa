# Instructions for creating self-signed certificates for TLS

Follow these steps to generate self-signed certificates for enabling TLS on your Django website during development.

## For Windows:

1. Install OpenSSL (if not already installed):
   - Download and install OpenSSL for Windows from https://slproweb.com/products/Win32OpenSSL.html
   - Add the bin directory to your system PATH

2. Generate your self-signed certificate:
   ```powershell
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```
   When prompted, fill in the details. The Common Name (CN) should be `localhost` for local development.

3. Place the generated `cert.pem` and `key.pem` files in the root directory of your project

## For Linux/macOS:

1. If OpenSSL is not installed:
   - For Linux: `sudo apt-get install openssl` (Ubuntu/Debian) or `sudo yum install openssl` (CentOS/RHEL)
   - For macOS: `brew install openssl`

2. Generate your self-signed certificate:
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```
   When prompted, fill in the details. The Common Name (CN) should be `localhost` for local development.

3. Place the generated `cert.pem` and `key.pem` files in the root directory of your project

## Using with Django Development Server:

To run the Django development server with SSL/TLS:

```bash
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem
```

To use this command, you need to install django-extensions:

```bash
pip install django-extensions
```

And add 'django_extensions' to your INSTALLED_APPS in settings.py.

## For Production:

For production, use a real SSL certificate from a trusted certificate authority (like Let's Encrypt) and configure your web server (Nginx, Apache, etc.) to handle HTTPS/TLS.
