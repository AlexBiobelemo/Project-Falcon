"""Signal handlers for automatic activity logging.

This module provides Django signal handlers that automatically capture
user activities and log them to the EventLog model.

Rules compliance: PEP8, type hints, docstrings.
"""

import logging
from typing import Any, Optional

from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .models import (
    EventLog,
    FiscalAssessment,
    Flight,
    Gate,
    Document,
    Report,
    Staff,
    StaffAssignment,
    Aircraft,
    CrewMember,
    MaintenanceLog,
    IncidentReport,
    Airport,
)
from .middleware import get_current_request

logger = logging.getLogger('django')


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login events."""
    event_type = 'user_login'
    description = f"User logged in: {user.username}"
    
    try:
        EventLog.objects.create(
            event_type=event_type,
            description=description,
            user=user,
            action='login',
            ip_address=get_client_ip(request),
            severity='info',
        )
    except Exception as e:
        logger.error(f"Failed to log user login: {e}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout events."""
    event_type = 'user_logout'
    description = f"User logged out: {user.username}"
    
    try:
        EventLog.objects.create(
            event_type=event_type,
            description=description,
            user=user,
            action='logout',
            ip_address=get_client_ip(request),
            severity='info',
        )
    except Exception as e:
        logger.error(f"Failed to log user logout: {e}")


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request=None, **kwargs):
    """Log failed login attempts."""
    event_type = 'user_login_failed'
    
    # Get username from credentials dict
    username = credentials.get('username', 'unknown')
    description = f"Failed login attempt for username: {username}"
    
    ip_address = get_client_ip(request) if request else ''
    
    try:
        EventLog.objects.create(
            event_type=event_type,
            description=description,
            action='login',
            ip_address=ip_address,
            severity='warning',
        )
    except Exception as e:
        logger.error(f"Failed to log login failure: {e}")


def get_client_ip(request) -> str:
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def log_activity(
    request,
    event_type: str,
    description: str,
    action: str = 'other',
    severity: str = 'info',
    obj: Any = None,
    flight: Any = None,
) -> None:
    """Helper function to log user activity.
    
    Args:
        request: The HTTP request object.
        event_type: Type/category of the event.
        description: Human-readable description.
        action: The action performed.
        severity: Event severity level.
        obj: The object that was affected.
        flight: Associated flight (if applicable).
    """
    try:
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        ip_address = get_client_ip(request) if request else ''
        
        EventLog.objects.create(
            event_type=event_type,
            description=description,
            user=user,
            action=action,
            ip_address=ip_address,
            flight=flight,
            severity=severity,
        )
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")


@receiver(post_save, sender=FiscalAssessment)
def log_fiscal_assessment_save(
    sender: Any, instance: FiscalAssessment, created: bool, **kwargs
) -> None:
    """Log fiscal assessment create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'fiscal_assessment_{action}'
    description = f"Fiscal assessment {action}d: {instance} (Status: {instance.status})"
    severity = 'info'
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity=severity,
            obj=instance,
        )
    else:
        # Fallback: log without user context
        try:
            EventLog.objects.create(
                event_type=event_type,
                description=description,
                action=action,
                severity=severity,
            )
        except Exception as e:
            logger.error(f"Failed to log fiscal assessment activity: {e}")


@receiver(post_delete, sender=FiscalAssessment)
def log_fiscal_assessment_delete(
    sender: Any, instance: FiscalAssessment, **kwargs
) -> None:
    """Log fiscal assessment delete activities."""
    event_type = 'fiscal_assessment_delete'
    description = f"Fiscal assessment deleted: {instance}"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='warning',
            obj=instance,
        )


@receiver(pre_save, sender=Flight)
def detect_flight_status_change(
    sender: Any, instance: Flight, **kwargs
) -> None:
    """Detect flight status changes and trigger notifications."""
    if not instance.pk:
        return  # New flight, no previous status

    try:
        old_instance = sender.objects.get(pk=instance.pk)
        old_status = old_instance.status
        new_status = instance.status

        if old_status != new_status:
            # Import here to avoid circular imports
            from .consumers import (
                notify_flight_status_change,
                notify_gate_change,
            )

            # Schedule notification via channels
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()

            # Trigger appropriate notification based on status change
            if new_status == 'delayed':
                async_to_sync(channel_layer.group_send)(
                    'notifications',
                    {
                        'type': 'delay_notification',
                        'title': f'Flight Delayed - {instance.flight_number}',
                        'body': f'Flight {instance.flight_number} is delayed by {instance.delay_minutes} minutes',
                        'data': {
                            'flight_id': instance.id,
                            'flight_number': instance.flight_number,
                            'delay_minutes': instance.delay_minutes,
                            'old_status': old_status,
                            'new_status': new_status,
                        },
                    }
                )
            elif new_status == 'cancelled':
                async_to_sync(channel_layer.group_send)(
                    'notifications',
                    {
                        'type': 'cancellation_notification',
                        'title': f'Flight Cancelled - {instance.flight_number}',
                        'body': f'Flight {instance.flight_number} has been cancelled',
                        'data': {
                            'flight_id': instance.id,
                            'flight_number': instance.flight_number,
                            'old_status': old_status,
                            'new_status': new_status,
                        },
                    }
                )
            else:
                async_to_sync(channel_layer.group_send)(
                    'notifications',
                    {
                        'type': 'flight_notification',
                        'title': f'Flight Status Changed - {instance.flight_number}',
                        'body': f'Flight {instance.flight_number} status changed from {old_status} to {new_status}',
                        'data': {
                            'flight_id': instance.id,
                            'flight_number': instance.flight_number,
                            'old_status': old_status,
                            'new_status': new_status,
                        },
                    }
                )

            # Check for gate change
            old_gate = old_instance.gate.gate_id if old_instance.gate else None
            new_gate = instance.gate.gate_id if instance.gate else None

            if old_gate != new_gate:
                async_to_sync(channel_layer.group_send)(
                    'notifications',
                    {
                        'type': 'gate_change_notification',
                        'title': f'Gate Change - {instance.flight_number}',
                        'body': f'Flight {instance.flight_number} gate changed from {old_gate or "none"} to {new_gate or "none"}',
                        'data': {
                            'flight_id': instance.id,
                            'flight_number': instance.flight_number,
                            'old_gate': old_gate,
                            'new_gate': new_gate,
                        },
                    }
                )

    except Flight.DoesNotExist:
        pass  # Flight doesn't exist yet
    except Exception as e:
        logger.error(f"Failed to detect flight status change: {e}")


@receiver(post_save, sender=Flight)
def log_flight_save(
    sender: Any, instance: Flight, created: bool, **kwargs
) -> None:
    """Log flight create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'flight_{action}'
    description = f"Flight {action}d: {instance.flight_number} ({instance.origin} → {instance.destination}) - Status: {instance.status}"

    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
            flight=instance,
        )


@receiver(post_delete, sender=Flight)
def log_flight_delete(
    sender: Any, instance: Flight, **kwargs
) -> None:
    """Log flight delete activities."""
    event_type = 'flight_delete'
    description = f"Flight deleted: {instance.flight_number}"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='warning',
            flight=instance,
        )


@receiver(post_save, sender=Gate)
def log_gate_save(
    sender: Any, instance: Gate, created: bool, **kwargs
) -> None:
    """Log gate create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'gate_{action}'
    description = f"Gate {action}d: {instance.gate_id} - Status: {instance.status}"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
        )


@receiver(post_save, sender=Document)
def log_document_save(
    sender: Any, instance: Document, created: bool, **kwargs
) -> None:
    """Log document create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'document_{action}'
    description = f"Document {action}d: {instance.name}"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
        )


@receiver(post_delete, sender=Document)
def log_document_delete(
    sender: Any, instance: Document, **kwargs
) -> None:
    """Log document delete activities."""
    event_type = 'document_delete'
    description = f"Document deleted: {instance.name}"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='warning',
        )


@receiver(post_save, sender=Report)
def log_report_save(
    sender: Any, instance: Report, created: bool, **kwargs
) -> None:
    """Log report create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'report_{action}'
    description = f"Report {action}d: {instance.title} (Type: {instance.report_type})"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
        )


@receiver(post_save, sender=Staff)
def log_staff_save(
    sender: Any, instance: Staff, created: bool, **kwargs
) -> None:
    """Log staff create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'staff_{action}'
    description = f"Staff member {action}d: {instance.first_name} {instance.last_name} ({instance.role})"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
        )


@receiver(post_save, sender=StaffAssignment)
def log_staff_assignment_save(
    sender: Any, instance: StaffAssignment, created: bool, **kwargs
) -> None:
    """Log staff assignment activities."""
    action = 'create' if created else 'update'
    event_type = f'staff_assignment_{action}'
    description = f"Staff assignment {action}d: {instance.staff} assigned to {instance.flight}"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
            flight=instance.flight,
        )


@receiver(post_delete, sender=StaffAssignment)
def log_staff_assignment_delete(
    sender: Any, instance: StaffAssignment, **kwargs
) -> None:
    """Log staff assignment delete activities."""
    event_type = 'staff_assignment_delete'
    description = f"Staff assignment removed: {instance.staff} unassigned from {instance.flight}"
    
    # Get request from thread local storage
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='info',
            flight=instance.flight,
        )


@receiver(post_save, sender=Aircraft)
def log_aircraft_save(
    sender: Any, instance: Aircraft, created: bool, **kwargs
) -> None:
    """Log aircraft create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'aircraft_{action}'
    description = f"Aircraft {action}d: {instance.tail_number} (Type: {instance.aircraft_type})"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
        )


@receiver(post_delete, sender=Aircraft)
def log_aircraft_delete(
    sender: Any, instance: Aircraft, **kwargs
) -> None:
    """Log aircraft delete activities."""
    event_type = 'aircraft_delete'
    description = f"Aircraft deleted: {instance.tail_number}"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='warning',
            obj=instance,
        )


@receiver(post_save, sender=CrewMember)
def log_crew_member_save(
    sender: Any, instance: CrewMember, created: bool, **kwargs
) -> None:
    """Log crew member create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'crew_member_{action}'
    description = f"Crew member {action}d: {instance.first_name} {instance.last_name} (Role: {instance.crew_type})"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
        )


@receiver(post_delete, sender=CrewMember)
def log_crew_member_delete(
    sender: Any, instance: CrewMember, **kwargs
) -> None:
    """Log crew member delete activities."""
    event_type = 'crew_member_delete'
    description = f"Crew member deleted: {instance.first_name} {instance.last_name}"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='warning',
            obj=instance,
        )


@receiver(post_save, sender=MaintenanceLog)
def log_maintenance_log_save(
    sender: Any, instance: MaintenanceLog, created: bool, **kwargs
) -> None:
    """Log maintenance log create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'maintenance_log_{action}'
    description = f"Maintenance log {action}d: {instance.equipment_id} ({instance.equipment_type}) - Type: {instance.maintenance_type}"
    
    severity = 'info' if action == 'create' else 'info'
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity=severity,
            obj=instance,
        )


@receiver(post_delete, sender=MaintenanceLog)
def log_maintenance_log_delete(
    sender: Any, instance: MaintenanceLog, **kwargs
) -> None:
    """Log maintenance log delete activities."""
    event_type = 'maintenance_log_delete'
    description = f"Maintenance log deleted: {instance.equipment_id} ({instance.equipment_type})"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='warning',
            obj=instance,
        )


@receiver(post_save, sender=IncidentReport)
def log_incident_report_save(
    sender: Any, instance: IncidentReport, created: bool, **kwargs
) -> None:
    """Log incident report create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'incident_report_{action}'
    severity = 'error' if instance.severity == 'critical' else 'warning' if instance.severity == 'high' else 'info'
    description = f"Incident report {action}d: {instance.title} (Severity: {instance.severity})"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity=severity,
            obj=instance,
            flight=instance.related_flight,
        )


@receiver(post_delete, sender=IncidentReport)
def log_incident_report_delete(
    sender: Any, instance: IncidentReport, **kwargs
) -> None:
    """Log incident report delete activities."""
    event_type = 'incident_report_delete'
    description = f"Incident report deleted: {instance.title}"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='warning',
            obj=instance,
            flight=instance.related_flight,
        )


@receiver(post_save, sender=Airport)
def log_airport_save(
    sender: Any, instance: Airport, created: bool, **kwargs
) -> None:
    """Log airport create/update activities."""
    action = 'create' if created else 'update'
    event_type = f'airport_{action}'
    description = f"Airport {action}d: {instance.code} - {instance.name}"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action=action,
            severity='info',
            obj=instance,
        )


@receiver(post_delete, sender=Airport)
def log_airport_delete(
    sender: Any, instance: Airport, **kwargs
) -> None:
    """Log airport delete activities."""
    event_type = 'airport_delete'
    description = f"Airport deleted: {instance.code} - {instance.name}"
    
    request = get_current_request()
    if request:
        log_activity(
            request=request,
            event_type=event_type,
            description=description,
            action='delete',
            severity='warning',
            obj=instance,
        )
