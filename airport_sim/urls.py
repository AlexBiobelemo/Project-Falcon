"""
URL configuration for airport_sim project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

import core.api_urls

# Use custom RestrictedAdminSite to enforce superuser-only access
from core.admin import admin_site

def root_dashboard_view(request):
    """Serve the main dashboard at the root URL."""
    from core.views import DashboardView
    return DashboardView.as_view()(request)

def public_baggage_tracking_view(request):
    """Serve the public baggage tracking portal (no auth required)."""
    from core.views import BaggageTrackingView
    return BaggageTrackingView.as_view()(request)

# HTTP fallback for WebSocket notifications (prevents 404 in logs)
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def ws_notifications_fallback(request):
    """HTTP fallback for WebSocket notifications endpoint.
    
    Returns JSON response to prevent 404 errors in logs when
    browser tries HTTP before establishing WebSocket connection.
    """
    return JsonResponse({
        'message': 'Notifications are available via WebSocket only',
        'websocket_url': '/ws/notifications/',
        'status': 'WebSocket connection required'
    })

urlpatterns = [
    # Avoid noisy 500s/404s from browsers requesting /favicon.ico.
    # If you add a real icon later, serve it from /static/favicon.ico.
    path('favicon.ico', lambda request: JsonResponse({}, status=204), name='favicon'),
    path('', root_dashboard_view, name='home'),
    path('baggage/public/', public_baggage_tracking_view, name='public-baggage-tracking'),
    path('admin/', admin_site.urls),
    path('core/', include('core.urls', namespace='core')),

    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),

    # API v1 endpoints with DRF
    path('api/v1/', include((core.api_urls, 'core'), namespace='api')),

    # WebSocket HTTP fallback endpoints
    path('ws/notifications/', ws_notifications_fallback, name='ws-notifications-fallback'),

    # API Documentation (Swagger/OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
]

# Add debug toolbar URLs in development
from django.conf import settings
if settings.DEBUG:
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
