"""WebSocket routing configuration for real-time updates.

This module defines WebSocket URL patterns for the airport simulation
and dashboard real-time updates using Django Channels.
"""

from django.urls import re_path

from core.consumers import (
    DashboardConsumer,
    FlightUpdatesConsumer,
    GateStatusConsumer,
    EventLogConsumer,
)

websocket_urlpatterns = [
    # Dashboard real-time updates
    re_path(r'ws/dashboard/$', DashboardConsumer.as_asgi()),
    
    # Flight status real-time updates
    re_path(r'ws/flights/$', FlightUpdatesConsumer.as_asgi()),
    
    # Gate status real-time updates
    re_path(r'ws/gates/$', GateStatusConsumer.as_asgi()),
    
    # Event log real-time updates
    re_path(r'ws/events/$', EventLogConsumer.as_asgi()),
]
