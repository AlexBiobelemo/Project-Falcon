#!/usr/bin/env python
"""Script to check and fix admin user permissions."""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airport_sim.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if user exists
try:
    user = User.objects.get(username='alex')
    print(f"User found: {user.username}")
    print(f"Is superuser: {user.is_superuser}")
    print(f"Is staff: {user.is_staff}")
    print(f"Is active: {user.is_active}")
    
    # Fix permissions if needed
    if not user.is_superuser or not user.is_staff or not user.is_active:
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.set_password('12345')
        user.save()
        print("User permissions fixed!")
    else:
        print("User already has correct permissions!")
        
except User.DoesNotExist:
    print("User 'alex' does not exist, creating...")
    user = User.objects.create_superuser('alex', 'alex@airportsim.local', '12345')
    print("Superuser created!")

# List all superusers
print("\nAll superusers:")
for u in User.objects.filter(is_superuser=True):
    print(f"- {u.username} (active: {u.is_active})")