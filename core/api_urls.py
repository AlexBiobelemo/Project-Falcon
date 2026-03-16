"""API URL configuration with versioning support.

This module defines URL patterns for the versioned API endpoints
at /api/v1/ using Django REST Framework.

Honeypot Protection:
- Decoy endpoints trap automated scanners
- Fake error endpoints confuse attackers
- All honeypot access is logged
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from . import api

app_name = 'api'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'airports', api.AirportViewSet, basename='airport')
router.register(r'gates', api.GateViewSet, basename='gate')
router.register(r'flights', api.FlightViewSet, basename='flight')
router.register(r'passengers', api.PassengerViewSet, basename='passenger')
router.register(r'staff', api.StaffViewSet, basename='staff')
router.register(r'staff-assignments', api.StaffAssignmentViewSet, basename='staff-assignment')
router.register(r'events', api.EventLogViewSet, basename='event')
router.register(r'assessments', api.FiscalAssessmentViewSet, basename='fiscal-assessment')

# New endpoints for additional models
router.register(r'aircraft', api.AircraftViewSet, basename='aircraft')
router.register(r'crew', api.CrewMemberViewSet, basename='crew')
router.register(r'maintenance', api.MaintenanceLogViewSet, basename='maintenance')
router.register(r'incidents', api.IncidentReportViewSet, basename='incident')

# Reports and documents
router.register(r'reports', api.ReportViewSet, basename='report')
router.register(r'documents', api.DocumentViewSet, basename='document')

# URL patterns
urlpatterns = [
    # API v1 routes
    path('', include(router.urls)),

    # Dashboard summary endpoint
    path(
        'dashboard-summary/',
        api.DashboardSummaryView.as_view(),
        name='dashboard-summary'
    ),

    # Metrics endpoint
    path(
        'metrics/',
        api.MetricsView.as_view(),
        name='metrics'
    ),

    # Analytics dashboard endpoint
    path(
        'analytics/',
        api.AnalyticsDashboardView.as_view(),
        name='analytics-dashboard'
    ),

    # Trend data endpoint
    path(
        'trends/',
        api.TrendDataAPIView.as_view(),
        name='trend-data'
    ),

    # Map data endpoint for live flight tracking
    path(
        'map-data/',
        api.map_data_view,
        name='map-data'
    ),

    # Weather search endpoint
    path(
        'weather/search/',
        api.weather_search_view,
        name='weather-search'
    ),

    # Weather by location endpoint
    path(
        'weather/location/',
        api.weather_location_view,
        name='weather-location'
    ),

    # User preferences endpoint
    path(
        'user/preferences/',
        api.UserPreferencesView.as_view(),
        name='user-preferences'
    ),

    # API Schema for documentation
    path(
        'schema/',
        SpectacularAPIView.as_view(),
        name='schema'
    ),
    path(
        'schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='api:schema'),
        name='swagger-ui'
    ),
    path(
        'schema/redoc/',
        SpectacularRedocView.as_view(url_name='api:schema'),
        name='redoc'
    ),

    #HONEYPOT These are decoy endpoints that trap and log scanners

    # Fake backup endpoint - traps automated scanners looking for data
    path(
        'backup/',
        api.honeypot_backup_endpoint,
        name='honeypot-backup'
    ),

    # Fake debug endpoint - traps developers tools
    path(
        'debug/',
        api.honeypot_debug_endpoint,
        name='honeypot-debug'
    ),

    # Fake admin endpoint - traps privilege escalation attempts
    path(
        'admin/config/',
        api.honeypot_admin_endpoint,
        name='honeypot-admin'
    ),

    # Fake internal endpoint - traps internal reconnaissance
    path(
        'internal/users/',
        api.honeypot_internal_endpoint,
        name='honeypot-internal'
    ),

    # Fake database endpoint
    path(
        'database/',
        api.honeypot_database_endpoint,
        name='honeypot-database'
    ),

    # Honeypot status endpoint (for monitoring)
    path(
        '_honeypot_status/',
        api.honeypot_status_endpoint,
        name='honeypot-status'
    ),
]
