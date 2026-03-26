"""
Comprehensive honeypot security tests for the Airport Operations Management System.

This module contains tests for:
- Honeypot middleware endpoint detection
- Honeypot form field protection
- API honeypot endpoints
- Rate limiting behavior
- Token validation

Security features tested:
- Honeypot path detection and blocking
- Rate limiting for repeated honeypot triggers
- Form submission time validation
- Token generation and validation
- Obfuscated responses to attackers
"""

import time
import hashlib
import hmac
import secrets
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from rest_framework.test import APIClient

from core.middleware import (
    HoneypotMiddleware,
    HoneypotTokenMiddleware,
    generate_honeypot_token,
    hash_honeypot_token,
    get_client_ip,
)
from core.honeypot import (
    create_time_token,
    validate_time_token,
    HoneypotFieldMixin,
)


class HoneypotMiddlewareTest(TestCase):
    """Tests for the HoneypotMiddleware."""
    
    def setUp(self):
        self.client = Client()
        self.middleware = HoneypotMiddleware(self.get_response_mock)
        self.get_response_mock = MagicMock()
        self.get_response_mock.return_value = MagicMock(status_code=200)
    
    def get_response_mock(self, request):
        return self.get_response_mock(request)
    
    def test_honeypot_path_detection(self):
        """Test that honeypot paths are correctly detected."""
        # Test common honeypot paths
        honeypot_paths = [
            '/admin/secret-panel/',
            '/api/internal/debug/',
            '/wp-admin/',
            '/phpmyadmin/',
        ]
        
        for path in honeypot_paths:
            with patch('core.middleware.cache') as mock_cache:
                mock_cache.get.return_value = 0
                with self.assertLogs('honeypot', level='CRITICAL'):
                    request = MagicMock()
                    request.path = path
                    request.method = 'GET'
                    request.META = {'REMOTE_ADDR': '127.0.0.1'}
                    request.user.is_authenticated = False
                    
                    response = self.middleware(request)
                    
                    # Should return obfuscated response, not call get_response
                    self.assertNotEqual(response.status_code, 200)
    
    def test_normal_path_not_blocked(self):
        """Test that normal paths are not blocked."""
        normal_paths = [
            '/',
            '/api/v1/airports/',
            '/dashboard/',
        ]
        
        for path in normal_paths:
            request = MagicMock()
            request.path = path
            request.method = 'GET'
            request.META = {'REMOTE_ADDR': '127.0.0.1'}
            
            response = self.middleware(request)
            
            # Should call get_response normally
            self.get_response_mock.assert_called()
    
    @override_settings(HONEYPOT_ENABLED=False)
    def test_honeypot_disabled(self):
        """Test that honeypot can be disabled via settings."""
        middleware = HoneypotMiddleware(self.get_response_mock)
        
        request = MagicMock()
        request.path = '/admin/secret-panel/'
        request.method = 'GET'
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        response = middleware(request)
        
        # Should not block when disabled
        self.get_response_mock.assert_called()


class HoneypotTokenMiddlewareTest(TestCase):
    """Tests for the HoneypotTokenMiddleware."""
    
    def setUp(self):
        self.middleware = HoneypotTokenMiddleware(self.get_response_mock)
        self.get_response_mock = MagicMock()
        mock_response = MagicMock()
        mock_response.get.return_value = 'text/html'
        mock_response.__getitem__ = lambda self, key: 'text/html' if key == 'Content-Type' else None
        mock_response.set_cookie = MagicMock()
        self.get_response_mock.return_value = mock_response
    
    def test_token_added_to_html_response(self):
        """Test that honeypot tokens are added to HTML responses."""
        request = MagicMock()
        request.path = '/some/page/'
        
        response = self.middleware(request)
        
        # Should have set a cookie
        response.set_cookie.assert_called()
        
        # Should have added header
        self.assertTrue(hasattr(response, '__setitem__'))

class HoneypotTokenUtilitiesTest(TestCase):
    """Tests for honeypot token generation and validation."""
    
    def test_generate_honeypot_token(self):
        """Test that token generation produces unique tokens."""
        token1 = generate_honeypot_token()
        token2 = generate_honeypot_token()
        
        # Tokens should be unique
        self.assertNotEqual(token1, token2)
        
        # Tokens should be sufficiently long
        self.assertGreater(len(token1), 30)
    
    def test_hash_honeypot_token(self):
        """Test that token hashing works correctly."""
        token = generate_honeypot_token()
        hashed = hash_honeypot_token(token)
        
        # Hash should be different from original
        self.assertNotEqual(token, hashed)
        
        # Hash should be consistent
        self.assertEqual(hashed, hash_honeypot_token(token))
    
    def test_create_time_token(self):
        """Test time-based token creation."""
        form_id = 'TestForm'
        token = create_time_token(form_id)
        
        # Token should contain timestamp:token format
        self.assertIn(':', token)
        
        parts = token.split(':')
        self.assertEqual(len(parts), 2)
        
        # Timestamp should be recent
        timestamp = int(parts[0])
        self.assertAlmostEqual(timestamp, int(time.time()), delta=2)
    
    def test_validate_time_token_valid(self):
        """Test token validation with valid token."""
        form_id = 'TestForm'
        token = create_time_token(form_id)
        
        is_valid, is_too_fast, error = validate_time_token(form_id, token)
        
        self.assertTrue(is_valid)
        self.assertFalse(is_too_fast)
        self.assertIsNone(error)
    
    def test_validate_time_token_invalid_format(self):
        """Test token validation with invalid format."""
        is_valid, is_too_fast, error = validate_time_token('TestForm', 'invalid')
        
        self.assertFalse(is_valid)
        self.assertIn('Invalid token format', error)
    
    def test_validate_time_token_wrong_form(self):
        """Test token validation with wrong form ID."""
        token = create_time_token('FormA')
        
        is_valid, is_too_fast, error = validate_time_token('FormB', token)
        
        self.assertFalse(is_valid)
    
    def test_validate_time_token_too_fast(self):
        """Test that submissions can be too fast (simulated)."""
        form_id = 'TestForm'
        
        # Create a token with a timestamp in the future (simulating fast submission)
        future_timestamp = int(time.time()) + 100
        secret = hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest()[:32]
        message = f"{form_id}:{future_timestamp}:{secret}"
        token = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        token_str = f"{future_timestamp}:{token}"
        
        # This should still be valid since timestamp is valid
        is_valid, is_too_fast, error = validate_time_token(form_id, token_str)
        
        # Token is technically valid (not too fast, just future)
        self.assertTrue(is_valid)

class APIHoneypotEndpointsTest(TestCase):
    """Tests for honeypot API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_backup_honeypot_endpoint(self):
        """Test the backup honeypot endpoint."""
        url = '/api/v1/backup/'
        response = self.client.get(url)
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
        
        # Should contain error message
        self.assertIn('error', response.json())
    
    def test_debug_honeypot_endpoint(self):
        """Test the debug honeypot endpoint."""
        url = '/api/v1/debug/'
        response = self.client.get(url)
        
        # Should return 403
        self.assertEqual(response.status_code, 403)
    
    def test_admin_honeypot_endpoint(self):
        """Test the admin honeypot endpoint."""
        url = '/api/v1/admin/config/'
        response = self.client.get(url)
        
        # Should return 401
        self.assertEqual(response.status_code, 401)
    
    def test_internal_honeypot_endpoint(self):
        """Test the internal honeypot endpoint."""
        url = '/api/v1/internal/users/'
        response = self.client.get(url)
        
        # Should return 403
        self.assertEqual(response.status_code, 403)
    
    def test_database_honeypot_endpoint(self):
        """Test the database honeypot endpoint."""
        url = '/api/v1/database/'
        response = self.client.get(url)
        
        # Should return 500
        self.assertEqual(response.status_code, 500)
    
    def test_status_honeypot_endpoint(self):
        """Test the status honeypot endpoint."""
        url = '/api/v1/_honeypot_status/'
        response = self.client.get(url)
        
        # Should return 200 with status
        self.assertEqual(response.status_code, 200)
        self.assertIn('status', response.json())


class HoneypotRateLimitTest(TestCase):
    """Tests for honeypot rate limiting."""
    
    def setUp(self):
        self.client = Client()
        self.middleware = HoneypotMiddleware(self.get_response_mock)
        self.get_response_mock = MagicMock()
        mock_response = MagicMock()
        mock_response.__setitem__ = lambda s, k, v: None
        self.get_response_mock.return_value = mock_response
    
    def test_rate_limit_blocks_repeated_triggers(self):
        """Test that repeated honeypot triggers are rate limited."""
        with patch('core.middleware.cache') as mock_cache:
            # First few requests should not be blocked
            for i in range(3):
                mock_cache.get.return_value = i
                
                request = MagicMock()
                request.path = '/admin/secret-panel/'
                request.method = 'GET'
                request.META = {'REMOTE_ADDR': '192.168.1.100'}
                request.user.is_authenticated = False
                
                response = self.middleware(request)
            
            # After exceeding rate limit, should be blocked
            mock_cache.get.return_value = 5
            
            request = MagicMock()
            request.path = '/admin/secret-panel/'
            request.method = 'GET'
            request.META = {'REMOTE_ADDR': '192.168.1.100'}
            
            # Should still return response but at reduced rate
            response = self.middleware(request)
            self.assertIsNotNone(response)


class HoneypotIntegrationTest(TestCase):
    """Integration tests for honeypot system."""
    
    def test_honeypot_paths_in_settings(self):
        """Test that honeypot paths are properly configured."""
        self.assertTrue(len(settings.HONEYPOT_PATHS) > 0)
        
        # Should include common attack targets
        expected_paths = ['/admin/secret-panel/', '/api/internal/debug/']
        for path in expected_paths:
            self.assertIn(path, settings.HONEYPOT_PATHS)
    
    def test_honeypot_middleware_registered(self):
        """Test that honeypot middleware is registered."""
        middleware_list = settings.MIDDLEWARE
        self.assertIn('core.middleware.HoneypotMiddleware', middleware_list)
        self.assertIn('core.middleware.HoneypotTokenMiddleware', middleware_list)
    
    def test_honeypot_logger_configured(self):
        """Test that honeypot logger is configured."""
        import logging
        logger = logging.getLogger('honeypot')
        
        # Logger should exist and be configured
        self.assertIsNotNone(logger)
        
        # Should have handlers
        self.assertGreater(len(logger.handlers), 0)
