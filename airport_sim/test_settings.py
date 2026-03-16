"""
Test settings for running tests without debug toolbar issues.
"""

from .settings import *

# Disable debug toolbar for tests
DEBUG = False

# Remove debug toolbar from installed apps
INSTALLED_APPS = [
    app for app in INSTALLED_APPS 
    if app != 'debug_toolbar'
]

# Remove debug toolbar middleware but keep honeypot middleware
MIDDLEWARE = [
    m for m in MIDDLEWARE 
    if not m.startswith('debug_toolbar.')
]

# Use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use simple password hasher for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Enable honeypot for tests (needed for middleware tests)
HONEYPOT_ENABLED = True
HONEYPOT_TOKEN_ENABLED = True

# Simplified caching for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable debug toolbar check
INTERNAL_IPS = []
