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

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@airportsim.local', 'admin123')
    print('Superuser created successfully!')
    print('Username: admin')
    print('Password: admin123')
else:
    print('Superuser already exists!')
