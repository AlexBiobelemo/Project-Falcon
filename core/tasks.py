
import logging
from django.utils import timezone
from core.models import Report, ReportType, ReportFormat, Flight, Passenger, FiscalAssessment
from django.db.models import Avg, Sum, Count

logger = logging.getLogger(__name__)

def generate_report_task(report_id):
    """Background task to generate report content."""
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
