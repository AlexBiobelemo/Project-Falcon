"""
ASGI config for airport_sim project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import asyncio
from pathlib import Path
from django.core.asgi import get_asgi_application
from django.conf import settings

# Import channels and routing for WebSocket support
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Import static files handler for ASGI
from asgiref.compatibility import guarantee_single_callable
from asgiref.staticfiles import StaticFilesWrapper

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'airport_sim.settings')

# Initialize Django ASGI application early to ensure settings are loaded
django_asgi_app = get_asgi_application()

# Wrap with static files handler for production
# This serves static files from STATIC_ROOT when DEBUG=False
django_asgi_app = StaticFilesWrapper(django_asgi_app)

# Import WebSocket routing after Django is set up
from airport_sim.websocket_routing import websocket_urlpatterns


class WebSocketRateLimiterMiddleware:
    """
    Custom rate limiting middleware for WebSocket connections.
    Limits the number of messages per second per connection.
    """
    
    def __init__(self, application, rate="100/s"):
        self.application = application
        self.rate = rate
        # Parse rate (e.g., "100/s" -> 100 messages per second)
        self.max_messages = int(rate.split('/')[0])
        self.time_window = 1.0  # 1 second window
        self.connection_counts = {}  # Track message counts per connection
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            # Get connection identifier
            connection_id = id(scope.get('client', (None, None)))
            
            # Check and update connection count
            if connection_id in self.connection_counts:
                last_time, count = self.connection_counts[connection_id]
                current_time = asyncio.get_event_loop().time()
                
                # Reset if time window expired
                if current_time - last_time > self.time_window:
                    self.connection_counts[connection_id] = (current_time, 1)
                else:
                    # Check rate limit
                    if count >= self.max_messages:
                        # Close connection due to rate limit
                        await self._send_rate_limit_error(send)
                        return
                    self.connection_counts[connection_id] = (last_time, count + 1)
            else:
                current_time = asyncio.get_event_loop().time()
                self.connection_counts[connection_id] = (current_time, 1)
        
        # Process the WebSocket connection
        return await self.application(scope, receive, send)
    
    async def _send_rate_limit_error(self, send):
        """Send rate limit error message and close connection."""
        await send({
            'type': 'websocket.close',
            'code': 1013,  # Try again later
        })


class ConnectionLimitMiddleware:
    """
    Middleware to limit concurrent WebSocket connections per user.
    """
    
    def __init__(self, application, max_connections=10):
        self.application = application
        self.max_connections = max_connections
        self.active_connections = {}
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            # Get user from scope (set by AuthMiddlewareStack)
            user = scope.get('user', None)
            user_id = str(user.id) if user and user.is_authenticated else 'anonymous'
            
            # Check connection limit
            if user_id in self.active_connections:
                if self.active_connections[user_id] >= self.max_connections:
                    await send({
                        'type': 'websocket.close',
                        'code': 1013,
                    })
                    return
                self.active_connections[user_id] += 1
            else:
                self.active_connections[user_id] = 1
        
        try:
            return await self.application(scope, receive, send)
        finally:
            # Clean up on disconnect
            if scope['type'] == 'websocket' and user_id in self.active_connections:
                self.active_connections[user_id] -= 1
                if self.active_connections[user_id] <= 0:
                    del self.active_connections[user_id]


def get_websocket_application():
    """Create WebSocket application with authentication, rate limiting, and connection limits."""
    
    # Get configuration from environment
    max_connections = int(os.environ.get('WEBSOCKET_MAX_CONNECTIONS_PER_USER', '10'))
    rate_limit = os.environ.get('WEBSOCKET_RATE_LIMIT', '100/s')

    # Create WebSocket URL router with authentication and host validation
    websocket_app = AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    )
    
    # Add connection limits
    websocket_app = ConnectionLimitMiddleware(
        websocket_app,
        max_connections=max_connections
    )
    
    # Add rate limiting
    websocket_app = WebSocketRateLimiterMiddleware(
        websocket_app,
        rate=rate_limit
    )
    
    return websocket_app


# Application with connection limits and rate limiting
application = ProtocolTypeRouter({
    # Handle HTTP requests
    "http": django_asgi_app,
    
    # Handle WebSocket connections with authentication and rate limiting
    "websocket": get_websocket_application(),
})
