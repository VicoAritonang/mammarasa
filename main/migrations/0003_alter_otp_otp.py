# Generated by Django 5.1.7 on 2025-03-27 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_loginattempt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='otp',
            field=models.CharField(max_length=255),
        ),
    ]
