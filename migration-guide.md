# Migration Guide from SQLite to PostgreSQL

This guide provides instructions for migrating your Django restaurant website from SQLite to PostgreSQL.

## 1. Install PostgreSQL

### For Windows:
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer and follow the setup wizard
3. Remember the password you set for the postgres user
4. Add PostgreSQL's bin directory to your PATH

### For Linux:
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

### For macOS:
```bash
brew install postgresql
brew services start postgresql
```

## 2. Create a PostgreSQL Database

1. Open a terminal/command prompt and connect to PostgreSQL:
   ```bash
   # For Windows PowerShell
   psql -U postgres
   
   # For Linux (might need sudo -u postgres)
   sudo -u postgres psql
   
   # For macOS
   psql postgres
   ```

2. Create a new database:
   ```sql
   CREATE DATABASE mammarasa_db;
   ```

3. Exit from the PostgreSQL prompt:
   ```sql
   \q
   ```

## 3. Migrate Your Data (Optional)

If you want to migrate existing data from SQLite to PostgreSQL, you can use the `dumpdata` and `loaddata` commands or a third-party tool.

### Using Django's dumpdata/loaddata:

1. Export data from SQLite:
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data.json
   ```

2. Configure the settings.py file to use PostgreSQL (already done)

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Load data into PostgreSQL:
   ```bash
   python manage.py loaddata data.json
   ```

## 4. If Starting Fresh

If you're starting with a fresh database:

1. Remove the old SQLite database file:
   ```bash
   # Windows
   del db.sqlite3
   
   # Unix/Linux/macOS
   rm db.sqlite3
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

## 5. Test Your Setup

1. Run the development server:
   ```bash
   python manage.py runserver
   ```

2. Access the admin interface and verify everything works correctly

## 6. Troubleshooting

1. **Connection issues**: Verify your PostgreSQL server is running and check the connection details in `settings.py`

2. **Migration errors**: If you encounter migration errors, you may need to clear the Django migrations:
   ```bash
   python manage.py showmigrations
   # For each app
   python manage.py migrate app_name zero
   # Then recreate and run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Permission issues**: Ensure the PostgreSQL user has proper permissions for the database
