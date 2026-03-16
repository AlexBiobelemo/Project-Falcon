#!/usr/bin/env python
"""Script to create a superuser for the airport_sim project."""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airport_sim.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='alex').exists():
    User.objects.create_superuser('alex', 'alex@airportsim.local', '12345')
    print('Superuser created successfully!')
    print('Username: alex')
    print('Password: 12345')
else:
    # Update existing user
    user = User.objects.get(username='alex')
    user.set_password('12345')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print('Superuser credentials updated successfully!')
    print('Username: alex')
    print('Password: 12345')
