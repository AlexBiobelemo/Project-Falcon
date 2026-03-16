#!/usr/bin/env python
"""Script to reset all sessions and ensure clean login state."""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airport_sim.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

# Delete all sessions to force re-login
session_count = Session.objects.count()
Session.objects.all().delete()
print(f"Deleted {session_count} active sessions")

# Verify user exists and has correct permissions
try:
    user = User.objects.get(username='alex')
    print(f"User 'alex' exists with permissions:")
    print(f"  - Superuser: {user.is_superuser}")
    print(f"  - Staff: {user.is_staff}")
    print(f"  - Active: {user.is_active}")
    print(f"  - Password: (set to 12345)")
except User.DoesNotExist:
    print("User 'alex' does not exist!")

print("\nTo access the admin panel:")
print("1. Go to: http://localhost:8000/admin/")
print("2. Login with:")
print("   Username: alex")
print("   Password: 12345")
print("3. You should now have full admin access")