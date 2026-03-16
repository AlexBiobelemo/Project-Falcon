"""WebSocket consumers for real-time updates.

This module defines WebSocket consumers for real-time dashboard updates,
flight status, gate status, and event log updates using Django Channels.
"""

import json
import asyncio
from datetime import datetime
from typing import Optional

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class BaseAirportConsumer(AsyncWebsocketConsumer):
    """Base consumer for airport real-time updates.

    Provides common functionality for all airport consumers
    including connection management and group messaging.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        self.room_group_name = self.get_room_group_name()

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial data
        await self.send_initial_data()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    def get_room_group_name(self):
        """Get the room group name for this consumer."""
        raise NotImplementedError("Subclasses must implement get_room_group_name")

    async def send_initial_data(self):
        """Send initial data when client connects."""
        # Override in subclasses
        pass

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'ping':
                await self.send(json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
            elif action == 'subscribe':
                await self.handle_subscribe(data)
            elif action == 'unsubscribe':
                await self.handle_unsubscribe(data)
            elif action == 'request_notification_permission':
                await self.send(json.dumps({
                    'type': 'notification_permission',
                    'message': 'Please grant notification permission in your browser'
                }))
            else:
                await self.handle_action(data)
        except json.JSONDecodeError:
            await self.send(json.dumps({
                'error': 'Invalid JSON'
            }))

    async def handle_subscribe(self, data):
        """Handle subscription to specific data streams."""
        pass

    async def handle_unsubscribe(self, data):
        """Handle unsubscription from data streams."""
        pass

    async def handle_action(self, data):
        """Handle custom actions."""
        pass

    async def send_message(self, event):
        """Send message to WebSocket from group."""
        await self.send(text_data=json.dumps(event['message']))


class DashboardConsumer(BaseAirportConsumer):
    """WebSocket consumer for dashboard real-time updates.
    
    Broadcasts dashboard metrics, flight status, and gate utilization
    to all connected clients.
    """
    
    def get_room_group_name(self):
        """Get room group name for dashboard updates."""
        return 'dashboard_updates'
    
    async def send_initial_data(self):
        """Send initial dashboard data."""
        dashboard_data = await self.get_dashboard_data()
        
        await self.send(json.dumps({
            'type': 'dashboard_initial',
            'data': dashboard_data,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_dashboard_data(self):
        """Get current dashboard data from database."""
        from core.models import Flight, Gate, Passenger, EventLog
        
        # Get current metrics
        total_flights = Flight.objects.count()
        active_flights = Flight.objects.filter(
            status__in=['scheduled', 'boarding', 'departed', 'arrived']
        ).count()
        available_gates = Gate.objects.filter(status='available').count()
        total_gates = Gate.objects.count()
        total_passengers = Passenger.objects.count()
        
        # Get recent events
        recent_events = EventLog.objects.order_by('-timestamp')[:10]
        events_data = [
            {
                'id': str(e.event_id),
                'type': e.event_type,
                'description': e.description,
                'severity': e.severity,
                'timestamp': e.timestamp.isoformat()
            }
            for e in recent_events
        ]
        
        return {
            'flights': {
                'total': total_flights,
                'active': active_flights,
            },
            'gates': {
                'total': total_gates,
                'available': available_gates,
                'utilization': ((total_gates - available_gates) / total_gates * 100) if total_gates > 0 else 0
            },
            'passengers': {
                'total': total_passengers
            },
            'events': events_data
        }
    
    async def flight_update(self, event):
        """Handle flight update broadcast."""
        await self.send(json.dumps({
            'type': 'flight_update',
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def gate_update(self, event):
        """Handle gate update broadcast."""
        await self.send(json.dumps({
            'type': 'gate_update',
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def metrics_update(self, event):
        """Handle metrics update broadcast."""
        await self.send(json.dumps({
            'type': 'metrics_update',
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))


class FlightUpdatesConsumer(BaseAirportConsumer):
    """WebSocket consumer for flight status updates.
    
    Provides real-time flight status changes to connected clients.
    """
    
    def get_room_group_name(self):
        """Get room group name for flight updates."""
        return 'flight_updates'
    
    async def send_initial_data(self):
        """Send initial flight data."""
        flights_data = await self.get_all_flights()
        
        await self.send(json.dumps({
            'type': 'flights_initial',
            'data': flights_data,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_all_flights(self):
        """Get all flights from database."""
        from core.models import Flight
        
        flights = Flight.objects.select_related('gate').order_by('-scheduled_departure')[:50]
        
        return [
            {
                'id': f.id,
                'flight_number': f.flight_number,
                'airline': f.airline,
                'origin': f.origin,
                'destination': f.destination,
                'scheduled_departure': f.scheduled_departure.isoformat() if f.scheduled_departure else None,
                'actual_departure': f.actual_departure.isoformat() if f.actual_departure else None,
                'scheduled_arrival': f.scheduled_arrival.isoformat() if f.scheduled_arrival else None,
                'actual_arrival': f.actual_arrival.isoformat() if f.actual_arrival else None,
                'status': f.status,
                'delay_minutes': f.delay_minutes,
                'gate': {
                    'gate_id': f.gate.gate_id,
                    'terminal': f.gate.terminal
                } if f.gate else None,
            }
            for f in flights
        ]
    
    async def flight_status_changed(self, event):
        """Handle flight status change broadcast."""
        await self.send(json.dumps({
            'type': 'flight_status_changed',
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def flight_delay(self, event):
        """Handle flight delay broadcast."""
        await self.send(json.dumps({
            'type': 'flight_delay',
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))


class GateStatusConsumer(BaseAirportConsumer):
    """WebSocket consumer for gate status updates.
    
    Provides real-time gate availability and status changes.
    """
    
    def get_room_group_name(self):
        """Get room group name for gate updates."""
        return 'gate_updates'
    
    async def send_initial_data(self):
        """Send initial gate data."""
        gates_data = await self.get_all_gates()
        
        await self.send(json.dumps({
            'type': 'gates_initial',
            'data': gates_data,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_all_gates(self):
        """Get all gates from database."""
        from core.models import Gate
        
        gates = Gate.objects.all()
        
        return [
            {
                'id': g.id,
                'gate_id': g.gate_id,
                'terminal': g.terminal,
                'capacity': g.capacity,
                'status': g.status,
            }
            for g in gates
        ]
    
    async def gate_status_changed(self, event):
        """Handle gate status change broadcast."""
        await self.send(json.dumps({
            'type': 'gate_status_changed',
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def gate_assignment(self, event):
        """Handle gate assignment broadcast."""
        await self.send(json.dumps({
            'type': 'gate_assignment',
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))


class EventLogConsumer(BaseAirportConsumer):
    """WebSocket consumer for event log updates.
    
    Provides real-time event log updates for audit and monitoring.
    """
    
    def get_room_group_name(self):
        """Get room group name for event updates."""
        return 'event_updates'
    
    async def send_initial_data(self):
        """Send initial event log data."""
        events_data = await self.get_recent_events()
        
        await self.send(json.dumps({
            'type': 'events_initial',
            'data': events_data,
            'timestamp': timezone.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_recent_events(self, limit=50):
        """Get recent events from database."""
        from core.models import EventLog
        
        events = EventLog.objects.order_by('-timestamp')[:limit]
        
        return [
            {
                'id': str(e.event_id),
                'type': e.event_type,
                'description': e.description,
                'severity': e.severity,
                'flight': {
                    'flight_number': e.flight.flight_number
                } if e.flight else None,
                'timestamp': e.timestamp.isoformat()
            }
            for e in events
        ]
    
    async def new_event(self, event):
        """Handle new event broadcast."""
        await self.send(json.dumps({
            'type': 'new_event',
            'data': event['data'],
            'timestamp': timezone.now().isoformat()
        }))
    
    async def handle_action(self, data):
        """Handle custom actions for event log."""
        action = data.get('action')
        
        if action == 'filter':
            # Handle filter request
            await self.send(json.dumps({
                'type': 'filter_response',
                'data': {'message': 'Filter applied'},
                'timestamp': timezone.now().isoformat()
            }))
        elif action == 'get_older':
            # Handle pagination request for older events
            offset = data.get('offset', 50)
            older_events = await self.get_events_paginated(offset)
            await self.send(json.dumps({
                'type': 'older_events',
                'data': older_events,
                'timestamp': timezone.now().isoformat()
            }))
    
    @database_sync_to_async
    def get_events_paginated(self, offset=50, limit=50):
        """Get paginated events."""
        from core.models import EventLog
        
        events = EventLog.objects.order_by('-timestamp')[offset:offset + limit]
        
        return [
            {
                'id': str(e.event_id),
                'type': e.event_type,
                'description': e.description,
                'severity': e.severity,
                'flight': {
                    'flight_number': e.flight.flight_number
                } if e.flight else None,
                'timestamp': e.timestamp.isoformat()
            }
            for e in events
        ]


async def broadcast_to_group(group_name: str, message: dict):
    """Broadcast a message to all clients in a group.
    
    Args:
        group_name: The name of the channel group
        message: The message to broadcast
    """
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        group_name,
        {
            'type': 'send_message',
            'message': message
        }
    )


async def notify_flight_update(flight_id: int, update_data: dict):
    """Broadcast flight update to all dashboard consumers.
    
    Args:
        flight_id: ID of the updated flight
        update_data: Dictionary containing flight update data
    """
    await broadcast_to_group('dashboard_updates', {
        'type': 'flight_update',
        'data': update_data
    })
    await broadcast_to_group('flight_updates', {
        'type': 'flight_status_changed',
        'data': update_data
    })


async def notify_gate_update(gate_id: int, update_data: dict):
    """Broadcast gate update to all dashboard consumers.
    
    Args:
        gate_id: ID of the updated gate
        update_data: Dictionary containing gate update data
    """
    await broadcast_to_group('dashboard_updates', {
        'type': 'gate_update',
        'data': update_data
    })
    await broadcast_to_group('gate_updates', {
        'type': 'gate_status_changed',
        'data': update_data
    })


async def notify_new_event(event_data: dict):
    """Broadcast new event to all event consumers.

    Args:
        event_data: Dictionary containing event data
    """
    await broadcast_to_group('dashboard_updates', {
        'type': 'new_event',
        'data': event_data
    })
    await broadcast_to_group('event_updates', {
        'type': 'new_event',
        'data': event_data
    })


class NotificationConsumer(BaseAirportConsumer):
    """WebSocket consumer for real-time notifications.

    Provides browser push notifications for flight status changes,
    delays, cancellations, and other important operational updates.
    """

    def get_room_group_name(self):
        """Get room group name for notifications."""
        return 'notifications'

    async def send_initial_data(self):
        """Send initial notification preferences."""
        await self.send(json.dumps({
            'type': 'notification_config',
            'data': {
                'enabled': True,
                'types': ['flight_status', 'flight_delay', 'flight_cancellation', 'gate_change']
            },
            'timestamp': timezone.now().isoformat()
        }))

    async def flight_notification(self, event):
        """Handle flight notification broadcast."""
        await self.send(json.dumps({
            'type': 'flight_notification',
            'data': event['data'],
            'notification': {
                'title': event.get('title', 'Flight Update'),
                'body': event.get('body', ''),
                'icon': event.get('icon', '/static/icons/flight.png'),
                'badge': event.get('badge', '/static/icons/badge.png'),
                'tag': event.get('tag', f'flight-{event["data"].get("flight_id")}'),
                'requireInteraction': event.get('require_interaction', False),
            },
            'timestamp': timezone.now().isoformat()
        }))

    async def delay_notification(self, event):
        """Handle flight delay notification broadcast."""
        await self.send(json.dumps({
            'type': 'delay_notification',
            'data': event['data'],
            'notification': {
                'title': f"Flight Delayed - {event['data'].get('flight_number', 'Unknown')}",
                'body': event.get('body', f"Flight is delayed by {event['data'].get('delay_minutes', 0)} minutes"),
                'icon': '/static/icons/warning.png',
                'tag': f'delay-{event["data"].get("flight_id")}',
                'requireInteraction': True,
            },
            'timestamp': timezone.now().isoformat()
        }))

    async def cancellation_notification(self, event):
        """Handle flight cancellation notification broadcast."""
        await self.send(json.dumps({
            'type': 'cancellation_notification',
            'data': event['data'],
            'notification': {
                'title': f"Flight Cancelled - {event['data'].get('flight_number', 'Unknown')}",
                'body': event.get('body', 'Flight has been cancelled'),
                'icon': '/static/icons/error.png',
                'tag': f'cancel-{event["data"].get("flight_id")}',
                'requireInteraction': True,
            },
            'timestamp': timezone.now().isoformat()
        }))

    async def gate_change_notification(self, event):
        """Handle gate change notification broadcast."""
        await self.send(json.dumps({
            'type': 'gate_change_notification',
            'data': event['data'],
            'notification': {
                'title': f"Gate Change - {event['data'].get('flight_number', 'Unknown')}",
                'body': event.get('body', f"Gate changed to {event['data'].get('new_gate', 'Unknown')}"),
                'icon': '/static/icons/gate.png',
                'tag': f'gate-{event["data"].get("flight_id")}',
                'requireInteraction': False,
            },
            'timestamp': timezone.now().isoformat()
        }))


async def notify_flight_status_change(
    flight_id: int,
    flight_number: str,
    old_status: str,
    new_status: str,
    additional_data: Optional[dict] = None
):
    """Broadcast flight status change notification.

    Args:
        flight_id: ID of the flight
        flight_number: Flight number (e.g., "AA123")
        old_status: Previous flight status
        new_status: New flight status
        additional_data: Additional data to include
    """
    data = {
        'flight_id': flight_id,
        'flight_number': flight_number,
        'old_status': old_status,
        'new_status': new_status,
        **(additional_data or {})
    }

    # Determine notification type and message
    if new_status == 'delayed':
        await notify_flight_delay(flight_id, flight_number, additional_data.get('delay_minutes', 0))
    elif new_status == 'cancelled':
        await notify_flight_cancellation(flight_id, flight_number)
    else:
        await broadcast_to_group('notifications', {
            'type': 'flight_notification',
            'title': f'Flight Status Changed - {flight_number}',
            'body': f'Flight status changed from {old_status} to {new_status}',
            'data': data,
        })

    # Also broadcast to flight updates group
    await broadcast_to_group('flight_updates', {
        'type': 'flight_status_changed',
        'data': data
    })


async def notify_flight_delay(flight_id: int, flight_number: str, delay_minutes: int):
    """Broadcast flight delay notification.

    Args:
        flight_id: ID of the flight
        flight_number: Flight number
        delay_minutes: Number of minutes delayed
    """
    data = {
        'flight_id': flight_id,
        'flight_number': flight_number,
        'delay_minutes': delay_minutes,
        'status': 'delayed'
    }

    await broadcast_to_group('notifications', {
        'type': 'delay_notification',
        'title': f'Flight Delayed - {flight_number}',
        'body': f'Flight is delayed by {delay_minutes} minutes',
        'data': data,
    })

    await broadcast_to_group('flight_updates', {
        'type': 'flight_delay',
        'data': data
    })


async def notify_flight_cancellation(flight_id: int, flight_number: str):
    """Broadcast flight cancellation notification.

    Args:
        flight_id: ID of the flight
        flight_number: Flight number
    """
    data = {
        'flight_id': flight_id,
        'flight_number': flight_number,
        'status': 'cancelled'
    }

    await broadcast_to_group('notifications', {
        'type': 'cancellation_notification',
        'title': f'Flight Cancelled - {flight_number}',
        'body': 'Flight has been cancelled',
        'data': data,
    })

    await broadcast_to_group('flight_updates', {
        'type': 'flight_status_changed',
        'data': data
    })


async def notify_gate_change(
    flight_id: int,
    flight_number: str,
    old_gate: Optional[str],
    new_gate: Optional[str]
):
    """Broadcast gate change notification.

    Args:
        flight_id: ID of the flight
        flight_number: Flight number
        old_gate: Previous gate (if any)
        new_gate: New gate assignment
    """
    data = {
        'flight_id': flight_id,
        'flight_number': flight_number,
        'old_gate': old_gate,
        'new_gate': new_gate,
        'new_gate_id': new_gate
    }

    await broadcast_to_group('notifications', {
        'type': 'gate_change_notification',
        'title': f'Gate Change - {flight_number}',
        'body': f'Gate changed to {new_gate}' if new_gate else 'Gate assignment removed',
        'data': data,
    })

    await broadcast_to_group('gate_updates', {
        'type': 'gate_assignment',
        'data': data
    })
