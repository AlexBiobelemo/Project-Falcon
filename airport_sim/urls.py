"""
URL configuration for airport_sim project.
"""
from django.contrib import admin
from django.urls import path, include

import core.api_urls

# Use custom RestrictedAdminSite to enforce superuser-only access
from core.admin import RestrictedAdminSite
admin.site = RestrictedAdminSite()

def root_dashboard_view(request):
    """Serve the main dashboard at the root URL."""
    from core.views import DashboardView
    return DashboardView.as_view()(request)

urlpatterns = [
    path('', root_dashboard_view, name='home'),
    path('admin/', admin.site.urls),
    path('core/', include('core.urls', namespace='core')),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # API v1 endpoints with DRF
    path('api/v1/', include((core.api_urls, 'core'), namespace='api')),
]
