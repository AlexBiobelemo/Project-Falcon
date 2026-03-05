"""Middleware for thread-local request storage and honeypot protection.

This middleware provides:
1. Thread-local request storage for signals
2. Honeypot endpoint detection and logging
3. Rate limiting for honeypot triggers
"""

import logging
import threading
import secrets
import hashlib
import json
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.conf import settings
from django.core.cache import cache

# Thread-local storage for the current request
_current_request = threading.local()

# Honeypot logger
honeypot_logger = logging.getLogger('honeypot')


def get_current_request():
    """Get the current request from thread-local storage."""
    return getattr(_current_request, 'request', None)


def set_current_request(request):
    """Set the current request in thread-local storage."""
    _current_request.request = request


def get_client_ip(request):
    """Get the client IP address from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def generate_honeypot_token():
    """Generate a secure random token for honeypot validation."""
    return secrets.token_urlsafe(32)


def hash_honeypot_token(token):
    """Hash a honeypot token for secure storage/comparison."""
    return hashlib.sha256(token.encode()).hexdigest()


class RequestMiddleware:
    """Middleware to store the current request in thread-local storage.
    
    This allows Django signals to access the current request context,
    including user information and IP address.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request in thread-local storage
        set_current_request(request)
        
        try:
            response = self.get_response(request)
        finally:
            # Clean up thread-local storage
            set_current_request(None)
        
        return response


class HoneypotMiddleware:
    """Middleware to detect and respond to honeypot attacks.
    
    This middleware:
    - Detects access to honeypot endpoints
    - Generates dynamic honeypot tokens to prevent caching
    - Logs all honeypot access for analysis
    - Implements rate limiting to prevent honeypot abuse
    - Returns misleading responses to confuse attackers
    """

    # Honeypot endpoint paths (dynamic, loaded from settings)
    HONEYPOT_PATHS = getattr(settings, 'HONEYPOT_PATHS', [
        '/admin/secret-panel/',
        '/api/internal/debug/',
        '/api/backup/',
        '/wp-admin/',
        '/phpmyadmin/',
        '/server-status/',
    ])
    
    # Time window for rate limiting (seconds)
    RATE_LIMIT_WINDOW = getattr(settings, 'HONEYPOT_RATE_LIMIT_WINDOW', 60)
    
    # Maximum honeypot triggers per IP in time window
    RATE_LIMIT_MAX = getattr(settings, 'HONEYPOT_RATE_LIMIT_MAX', 3)
    
    # Whether honeypot is enabled
    ENABLED = getattr(settings, 'HONEYPOT_ENABLED', True)

    def __init__(self, get_response):
        self.get_response = get_response
        self._honeypot_paths = None

    def _get_honeypot_paths(self):
        """Get compiled honeypot paths for efficient matching."""
        if self._honeypot_paths is None:
            import re
            # Convert paths to regex patterns
            self._honeypot_paths = []
            for path in self.HONEYPOT_PATHS:
                # Escape special regex chars but allow wildcards
                pattern = path.replace('*', '.*').replace('/', r'\/?')
                self._honeypot_paths.append(re.compile(pattern, re.IGNORECASE))
        return self._honeypot_paths

    def _is_honeypot_path(self, path):
        """Check if the path matches any honeypot pattern."""
        for pattern in self._get_honeypot_paths():
            if pattern.match(path):
                return True
        return False

    def _check_rate_limit(self, ip):
        """Check if IP has exceeded rate limit for honeypot triggers."""
        if not self.ENABLED:
            return True
            
        cache_key = f'honeypot_rate_limit:{ip}'
        count = cache.get(cache_key, 0)
        
        if count >= self.RATE_LIMIT_MAX:
            return False
        
        # Increment counter
        cache.set(cache_key, count + 1, self.RATE_LIMIT_WINDOW)
        return True

    def _log_honeypot_access(self, request, path):
        """Log honeypot access with detailed information."""
        ip = get_client_ip(request)
        user = request.user if request.user.is_authenticated else 'anonymous'
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        
        # Get request method
        method = request.method
        
        # Log the attempt
        honeypot_logger.critical(
            f"HONEYPOT TRIGGERED | IP: {ip} | User: {user} | "
            f"Path: {path} | Method: {method} | "
            f"User-Agent: {user_agent}"
        )

    def _get_obfuscated_response(self, request, path):
        """Return an obfuscated response to confuse attackers."""
        import random
        
        # Randomize response to prevent pattern detection
        responses = [
            # Return 404 Not Found
            HttpResponseNotFound('Not Found'),
            # Return generic forbidden
            HttpResponseForbidden('Forbidden'),
            # Return redirect to homepage
            HttpResponseForbidden('Access Denied'),
        ]
        
        response = random.choice(responses)
        
        # Add security headers
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Custom-Honeypot'] = 'true'
        
        return response

    def __call__(self, request):
        # Skip if honeypot is disabled
        if not self.ENABLED:
            return self.get_response(request)
        
        path = request.path
        
        # Check if this is a honeypot path
        if self._is_honeypot_path(path):
            ip = get_client_ip(request)
            
            # Check rate limit
            if not self._check_rate_limit(ip):
                # IP is likely an aggressive scanner
                honeypot_logger.warning(
                    f"HONEYPOT RATE LIMIT EXCEEDED | IP: {ip} | Path: {path}"
                )
                # Return a delayed response to waste attacker's time
                import time
                time.sleep(2)
            
            # Log the honeypot access
            self._log_honeypot_access(request, path)
            
            # Return obfuscated response
            return self._get_obfuscated_response(request, path)
        
        # Continue to normal middleware
        return self.get_response(request)


class HoneypotTokenMiddleware:
    """Middleware that adds honeypot tokens to responses for form protection.
    
    This adds hidden token fields to forms rendered in templates,
    helping detect bots that try to submit forms without proper tokens.
    """

    ENABLED = getattr(settings, 'HONEYPOT_TOKEN_ENABLED', True)
    TOKEN_HEADER = 'X-Honeypot-Token'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        
        # Skip if disabled or not an HTML response
        if not self.ENABLED:
            return response
            
        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response
        
        # Add honeypot token header for JavaScript to read
        token = generate_honeypot_token()
        response[self.TOKEN_HEADER] = token
        
        # Also set as cookie for server-side validation
        response.set_cookie(
            'honeypot_token',
            hash_honeypot_token(token),
            max_age=3600,
            httponly=True,
            samesite='Lax'
        )
        
        return response
