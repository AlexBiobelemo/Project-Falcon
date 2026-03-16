
"""Background tasks for the Airport Operations Management System.

This module provides background task functions for django-q2 including
report generation, scheduled reports, and email notifications.

Rules compliance: PEP8, type hints, docstrings.
"""

import logging
from typing import List, Optional
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from core.models import Report, ReportType, ReportFormat, Flight, Passenger, FiscalAssessment, ReportSchedule
from django.db.models import Avg, Sum, Count

logger = logging.getLogger(__name__)


def generate_report_task(report_id: int) -> bool:
    """Background task to generate report content.

    Args:
        report_id: ID of the report to generate

    Returns:
        True if successful, False otherwise
    """
    try:
        report = Report.objects.get(id=report_id)
        logger.info(f"Starting background generation for report: {report.title} ({report_id})")

        content = {
            "generated_at": timezone.now().isoformat(),
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat(),
            },
        }

        if report.report_type == ReportType.FISCAL_SUMMARY.value:
            # Get fiscal assessments for the period
            assessments = FiscalAssessment.objects.filter(
                airport=report.airport,
                start_date__gte=report.period_start,
                end_date__lte=report.period_end,
            )

            total_revenue = sum(a.total_revenue for a in assessments)
            total_expenses = sum(a.total_expenses for a in assessments)
            net_profit = sum(a.net_profit for a in assessments)
            total_passengers = sum(a.passenger_count for a in assessments)
            total_flights = sum(a.flight_count for a in assessments)

            content["summary"] = {
                "total_revenue": float(total_revenue),
                "total_expenses": float(total_expenses),
                "net_profit": float(net_profit),
                "total_passengers": total_passengers,
                "total_flights": total_flights,
                "assessment_count": assessments.count(),
            }
            content["assessments"] = [
                {
                    "period": f"{a.start_date} to {a.end_date}",
                    "type": a.period_type,
                    "revenue": float(a.total_revenue),
                    "expenses": float(a.total_expenses),
                    "profit": float(a.net_profit),
                }
                for a in assessments
            ]

        elif report.report_type == ReportType.OPERATIONAL.value:
            # Get flights for the period
            flights = Flight.objects.filter(
                gate__isnull=False,
                scheduled_departure__gte=report.period_start,
                scheduled_departure__lte=report.period_end,
            )

            total_flights = flights.count()
            delayed_flights = flights.filter(status="delayed").count()
            cancelled_flights = flights.filter(status="cancelled").count()
            avg_delay = flights.aggregate(Avg("delay_minutes"))["delay_minutes__avg"] or 0

            content["summary"] = {
                "total_flights": total_flights,
                "delayed_flights": delayed_flights,
                "cancelled_flights": cancelled_flights,
                "on_time_flights": total_flights - delayed_flights - cancelled_flights,
                "average_delay_minutes": round(avg_delay, 2),
            }

        elif report.report_type == ReportType.PASSENGER.value:
            # Get passengers for the period
            passengers = Passenger.objects.filter(
                flight__scheduled_departure__gte=report.period_start,
                flight__scheduled_departure__lte=report.period_end,
            )

            total_passengers = passengers.count()
            checked_in = passengers.filter(status="checked_in").count()
            boarded = passengers.filter(status="boarded").count()
            arrived = passengers.filter(status="arrived").count()
            no_show = passengers.filter(status="no_show").count()

            content["summary"] = {
                "total_passengers": total_passengers,
                "checked_in": checked_in,
                "boarded": boarded,
                "arrived": arrived,
                "no_show": no_show,
            }

        elif report.report_type == ReportType.FINANCIAL.value:
            assessments = FiscalAssessment.objects.filter(
                airport=report.airport,
                start_date__gte=report.period_start,
                end_date__lte=report.period_end,
            )

            revenue_breakdown = {
                "fuel_revenue": sum(float(a.fuel_revenue) for a in assessments),
                "parking_revenue": sum(float(a.parking_revenue) for a in assessments),
                "retail_revenue": sum(float(a.retail_revenue) for a in assessments),
                "landing_fees": sum(float(a.landing_fees) for a in assessments),
                "cargo_revenue": sum(float(a.cargo_revenue) for a in assessments),
                "other_revenue": sum(float(a.other_revenue) for a in assessments),
            }

            expense_breakdown = {
                "security_costs": sum(float(a.security_costs) for a in assessments),
                "maintenance_costs": sum(float(a.maintenance_costs) for a in assessments),
                "operational_costs": sum(float(a.operational_costs) for a in assessments),
                "staff_costs": sum(float(a.staff_costs) for a in assessments),
                "utility_costs": sum(float(a.utility_costs) for a in assessments),
                "other_expenses": sum(float(a.other_expenses) for a in assessments),
            }

            content["revenue_breakdown"] = revenue_breakdown
            content["expense_breakdown"] = expense_breakdown
            content["net_profit"] = sum(revenue_breakdown.values()) - sum(expense_breakdown.values())

        report.content = content
        report.is_generated = True
        report.generated_at = timezone.now()
        report.save()

        logger.info(f"Successfully generated report: {report_id}")
        return True

    except Report.DoesNotExist:
        logger.error(f"Report {report_id} not found for background generation")
    except Exception as e:
        logger.error(f"Error generating report {report_id}: {str(e)}")
        return False


def generate_scheduled_report(schedule_id: int) -> bool:
    """Generate and email a scheduled report.

    Args:
        schedule_id: ID of the ReportSchedule to process

    Returns:
        True if successful, False otherwise
    """
    try:
        schedule = ReportSchedule.objects.get(id=schedule_id)
        logger.info(f"Processing scheduled report: {schedule.name} ({schedule_id})")

        if not schedule.is_active:
            logger.info(f"Schedule {schedule_id} is inactive, skipping")
            return True

        # Calculate date range based on frequency
        now = timezone.now()
        if schedule.frequency == 'daily':
            period_end = now
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif schedule.frequency == 'weekly':
            from datetime import timedelta
            period_end = now
            period_start = now - timedelta(days=7)
        else:  # monthly
            period_end = now
            if now.month == 1:
                period_start = now.replace(year=now.year - 1, month=12, day=1)
            else:
                period_start = now.replace(month=now.month - 1, day=1)

        # Create report
        report = Report.objects.create(
            title=f"{schedule.name} - {now.strftime('%Y-%m-%d')}",
            report_type=schedule.report_type,
            airport=schedule.airport,
            period_start=period_start,
            period_end=period_end,
            format=schedule.format,
            description=f"Automatically generated report for {schedule.frequency} schedule",
        )

        # Generate report content
        success = generate_report_task(report.id)

        if success:
            # Send email
            email_sent = send_report_email(
                report=report,
                recipients=schedule.recipients.split(','),
                schedule_name=schedule.name
            )

            # Update schedule
            schedule.last_run = timezone.now()
            schedule.next_run = schedule.calculate_next_run()
            schedule.save()

            logger.info(f"Scheduled report {schedule_id} completed. Email sent: {email_sent}")
            return email_sent
        else:
            logger.error(f"Failed to generate content for scheduled report {schedule_id}")
            report.delete()
            return False

    except ReportSchedule.DoesNotExist:
        logger.error(f"ReportSchedule {schedule_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error processing scheduled report {schedule_id}: {str(e)}")
        return False


def send_report_email(report: Report, recipients: List[str], schedule_name: str) -> bool:
    """Send report via email to recipients.

    Args:
        report: The generated report
        recipients: List of email addresses
        schedule_name: Name of the schedule that triggered this

    Returns:
        True if email sent successfully
    """
    try:
        if not settings.EMAIL_HOST:
            logger.warning("Email not configured, skipping email delivery")
            return False

        # Prepare email content
        subject = f"Report: {report.title}"

        # Create HTML content
        html_content = render_to_string('core/emails/report_email.html', {
            'report': report,
            'schedule_name': schedule_name,
        })

        # Create plain text alternative
        text_content = f"""
Report: {report.title}
Schedule: {schedule_name}
Generated: {report.generated_at}

This report has been generated and is available in the system.
        """

        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        email.attach_alternative(html_content, "text/html")

        # Send to all recipients
        email.send()

        logger.info(f"Report email sent to {len(recipients)} recipients")
        return True

    except Exception as e:
        logger.error(f"Failed to send report email: {str(e)}")
        return False


def check_scheduled_reports() -> int:
    """Check and queue due scheduled reports.

    This should be run periodically (e.g., every hour) to process
    any scheduled reports that are due.

    Returns:
        Number of reports queued
    """
    from django_q.tasks import async_task

    now = timezone.now()
    due_schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_run__lte=now
    )

    queued_count = 0
    for schedule in due_schedules:
        try:
            async_task(
                'core.tasks.generate_scheduled_report',
                schedule.id,
                group='scheduled_reports',
            )
            queued_count += 1
            logger.info(f"Queued scheduled report: {schedule.name}")
        except Exception as e:
            logger.error(f"Failed to queue scheduled report {schedule.id}: {e}")

    return queued_count


def warm_cache() -> int:
    """Warm cache with frequently accessed data.
    
    This should be run periodically to ensure fast response times
    for commonly requested data.
    
    Returns:
        Number of cache entries warmed
    """
    from django.core.cache import cache
    from .models import Airport, Flight, Gate, FiscalAssessment, AssessmentStatus
    from django.db.models import Count, Sum, Avg
    
    warmed = 0
    
    try:
        # Cache dashboard summary
        dashboard_data = {
            'total_airports': Airport.objects.filter(is_active=True).count(),
            'total_gates': Gate.objects.count(),
            'total_flights': Flight.objects.count(),
            'available_gates': Gate.objects.filter(status='available').count(),
            'active_flights': Flight.objects.filter(
                status__in=['scheduled', 'boarding', 'departed']
            ).count(),
        }
        cache.set('dashboard_summary', dashboard_data, 300)
        warmed += 1
        
        # Cache flight status counts
        flight_status_counts = Flight.objects.values('status').annotate(
            count=Count('id')
        )
        cache.set('flight_status_counts', dict(flight_status_counts), 300)
        warmed += 1
        
        # Cache airport financial summary
        financial_summary = FiscalAssessment.objects.filter(
            status=AssessmentStatus.APPROVED.value
        ).aggregate(
            total_revenue=Sum('total_revenue'),
            total_expenses=Sum('total_expenses'),
            net_profit=Sum('net_profit'),
        )
        cache.set('financial_summary', financial_summary, 300)
        warmed += 1
        
        # Cache gate utilization
        gate_utilization = Gate.objects.values('status').annotate(
            count=Count('id')
        )
        cache.set('gate_utilization', dict(gate_utilization), 300)
        warmed += 1
        
        logger.info(f"Cache warmed: {warmed} entries")
        
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
    
    return warmed


def backup_database() -> dict:
    """Create a database backup.
    
    Creates a backup of the database and stores it in the backups directory.
    
    Returns:
        Dictionary with backup status information
    """
    import os
    import subprocess
    from django.conf import settings
    
    backup_dir = settings.BASE_DIR / 'backups'
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'db_backup_{timestamp}.sql'
    
    try:
        # Get database settings
        db_settings = settings.DATABASES['default']
        
        if db_settings['ENGINE'] == 'django.db.backends.postgresql':
            # PostgreSQL backup
            env = os.environ.copy()
            env['PGPASSWORD'] = db_settings.get('PASSWORD', '')
            
            cmd = [
                'pg_dump',
                '-h', db_settings.get('HOST', 'localhost'),
                '-U', db_settings.get('USER', ''),
                '-d', db_settings.get('NAME', ''),
                '-F', 'c',  # Custom format
                '-f', str(backup_file)
            ]
            
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            
        elif db_settings['ENGINE'] == 'django.db.backends.sqlite3':
            # SQLite backup (just copy the file)
            import shutil
            db_file = db_settings.get('NAME', '')
            if db_file and db_file != ':memory:':
                shutil.copy2(db_file, str(backup_file.with_suffix('.db')))
                backup_file = backup_file.with_suffix('.db')
        
        # Clean up old backups (keep last 7 days)
        cleanup_old_backups(backup_dir, days=7)
        
        logger.info(f"Database backup created: {backup_file}")
        
        return {
            'success': True,
            'file': str(backup_file),
            'size': backup_file.stat().st_size if backup_file.exists() else 0,
        }
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return {
            'success': False,
            'error': str(e),
        }


def cleanup_old_backups(backup_dir, days: int = 7):
    """Remove backups older than specified days."""
    import os
    from datetime import timedelta
    
    cutoff = timezone.now() - timedelta(days=days)
    
    for file in backup_dir.iterdir():
        if file.is_file() and timezone.datetime.fromtimestamp(
            file.stat().st_mtime, tz=timezone.get_current_timezone()
        ) < cutoff:
            try:
                file.unlink()
                logger.info(f"Deleted old backup: {file}")
            except Exception as e:
                logger.error(f"Failed to delete {file}: {e}")
