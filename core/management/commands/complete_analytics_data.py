"""Supplementary command to complete analytics data population.

This adds the remaining data that wasn't created if the main script timed out.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from core.models import (
    Airport, Gate, Flight, Passenger, Staff, StaffAssignment, EventLog,
    FiscalAssessment, Report, Document, Aircraft, CrewMember,
    MaintenanceLog, MaintenanceSchedule, IncidentReport,
    Shift, StaffShiftAssignment, Baggage, ReportSchedule,
    GateStatus, FlightStatus, StaffRole, PassengerStatus,
    AssessmentPeriod, AssessmentStatus, ReportType, ReportFormat,
    AircraftType, AircraftStatus, CrewMemberType, CrewMemberStatus,
    MaintenanceType, MaintenanceStatus, IncidentType, IncidentSeverity, IncidentStatus,
)


class Command(BaseCommand):
    """Command to complete analytics data population."""

    help = "Complete analytics data population (baggage, assessments, events, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--flights',
            type=int,
            default=200,
            help='Number of additional flights to create',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("COMPLETING ANALYTICS DATA"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write()

        # Get existing data
        airports = list(Airport.objects.all())
        gates = list(Gate.objects.all())
        flights = list(Flight.objects.all())
        staff_members = list(Staff.objects.all())

        if not airports:
            self.stdout.write(self.style.ERROR("No airports found. Run populate_analytics_data first."))
            return

        # 1. Create more flights if needed
        target_flights = options['flights']
        if len(flights) < 500:
            self.stdout.write("[1/6] Creating additional flights...")
            flights.extend(self._create_more_flights(airports, gates, target_flights))

        # 2. Create baggage records
        self.stdout.write("[2/6] Creating baggage records...")
        self._create_baggage(flights)

        # 3. Create fiscal assessments
        self.stdout.write("[3/6] Creating fiscal assessments...")
        assessments = self._create_fiscal_assessments(airports)

        # 4. Create reports and documents
        self.stdout.write("[4/6] Creating reports and documents...")
        reports = self._create_reports(airports)
        self._create_documents(airports, assessments, reports)

        # 5. Create maintenance records
        self.stdout.write("[5/6] Creating maintenance records...")
        self._create_maintenance_records(gates, staff_members, airports)

        # 6. Create incidents and events
        self.stdout.write("[6/6] Creating incidents and event logs...")
        self._create_incidents_and_events(flights, gates, staff_members)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("DATA POPULATION COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write()
        self.stdout.write(f"Final Counts:")
        self.stdout.write(f"  Flights: {Flight.objects.count()}")
        self.stdout.write(f"  Passengers: {Passenger.objects.count()}")
        self.stdout.write(f"  Baggage: {Baggage.objects.count()}")
        self.stdout.write(f"  Fiscal Assessments: {FiscalAssessment.objects.count()}")
        self.stdout.write(f"  Reports: {Report.objects.count()}")
        self.stdout.write(f"  Documents: {Document.objects.count()}")
        self.stdout.write(f"  Event Logs: {EventLog.objects.count()}")
        self.stdout.write(f"  Incidents: {IncidentReport.objects.count()}")

    def _create_more_flights(self, airports, gates, target_count):
        """Create additional flights to reach target."""
        airlines = [
            ('Delta Air Lines', 'DL'), ('United Airlines', 'UA'),
            ('British Airways', 'BA'), ('Emirates', 'EK'),
            ('Lufthansa', 'LH'), ('Air Peace', 'P4'),
            ('Singapore Airlines', 'SQ'), ('Qatar Airways', 'QR'),
        ]
        now = timezone.now()
        created = []

        for i in range(target_count):
            airline = random.choice(airlines)
            flight_number = f"{airline[1]}{random.randint(1000, 9999)}"
            origin = random.choice(airports)
            destination = random.choice([a for a in airports if a != origin])

            day_offset = random.randint(0, 180)
            flight_date = now - timedelta(days=day_offset)
            departure_hour = random.randint(6, 22)
            scheduled_departure = flight_date.replace(hour=departure_hour, minute=random.choice([0, 15, 30, 45]), second=0, microsecond=0)
            scheduled_arrival = scheduled_departure + timedelta(hours=random.randint(2, 14))

            origin_gates = [g for g in gates if g.gate_id.startswith(origin.code)]
            gate = random.choice(origin_gates) if origin_gates else None

            if day_offset > 2:
                status = FlightStatus.ARRIVED
            elif day_offset > 0:
                status = random.choice([FlightStatus.DEPARTED, FlightStatus.SCHEDULED])
            else:
                status = random.choice([FlightStatus.SCHEDULED, FlightStatus.DELAYED])

            delay = random.choice([0, 0, 0, 15, 30, 45]) if status == FlightStatus.DELAYED else 0

            try:
                flight = Flight.objects.create(
                    flight_number=flight_number,
                    airline=airline[0],
                    origin=origin.code,
                    destination=destination.code,
                    scheduled_departure=scheduled_departure,
                    scheduled_arrival=scheduled_arrival,
                    gate=gate,
                    status=status.value,
                    delay_minutes=delay,
                    aircraft_type=random.choice(['B737', 'A320', 'B777', 'A350']),
                )
                if status == FlightStatus.ARRIVED:
                    flight.actual_departure = scheduled_departure
                    flight.actual_arrival = scheduled_arrival
                    flight.save()
                created.append(flight)
            except Exception:
                pass

        self.stdout.write(f"    Created {len(created)} additional flights.")
        return created

    def _create_baggage(self, flights):
        """Create baggage records for existing passengers."""
        baggage_count = 0
        statuses = [Baggage.BaggageStatus.CHECKED_IN, Baggage.BaggageStatus.SCREENED,
                   Baggage.BaggageStatus.SORTED, Baggage.BaggageStatus.LOADED]

        for flight in flights[:500]:  # Process first 500 flights
            passengers = list(flight.passengers.all())[:20]  # First 20 passengers per flight
            for passenger in passengers:
                if passenger.checked_bags > 0:
                    for bag_num in range(passenger.checked_bags):
                        tag = f"{flight.flight_number.replace(' ', '')}{bag_num + 1:03d}{passenger.passenger_id.hex[:4].upper()}"
                        status = Baggage.BaggageStatus.CLAIMED if flight.status == FlightStatus.ARRIVED else random.choice(statuses)

                        Baggage.objects.get_or_create(
                            tag_number=tag[:20],
                            defaults={'passenger': passenger, 'flight': flight,
                                     'status': status.value, 'origin': flight.origin,
                                     'destination': flight.destination,
                                     'weight': Decimal(f"{random.randint(15, 32)}.{random.randint(0, 9)}"),
                                     'pieces': 1,
                                     'location': f"Terminal {random.choice(['1', '2', '3'])}"}
                        )
                        baggage_count += 1

        self.stdout.write(f"    Created {baggage_count} baggage records.")

    def _create_fiscal_assessments(self, airports):
        """Create 6 months of fiscal assessments."""
        assessments = []
        for airport in airports:
            for months_ago in range(6):
                start_date = (timezone.now() - timedelta(days=30 * (months_ago + 1))).date().replace(day=1)
                if start_date.month == 12:
                    end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)

                base_revenue = Decimal(f"{random.randint(1200000, 2800000)}")
                base_expenses = Decimal(f"{random.randint(700000, 1600000)}")
                status = random.choice([AssessmentStatus.APPROVED, AssessmentStatus.COMPLETED])

                assessment, _ = FiscalAssessment.objects.get_or_create(
                    airport=airport, period_type=AssessmentPeriod.MONTHLY.value,
                    start_date=start_date, end_date=end_date,
                    defaults={'status': status.value,
                             'fuel_revenue': base_revenue * Decimal('0.30'),
                             'parking_revenue': base_revenue * Decimal('0.12'),
                             'retail_revenue': base_revenue * Decimal('0.22'),
                             'landing_fees': base_revenue * Decimal('0.20'),
                             'cargo_revenue': base_revenue * Decimal('0.10'),
                             'other_revenue': base_revenue * Decimal('0.06'),
                             'security_costs': base_expenses * Decimal('0.25'),
                             'maintenance_costs': base_expenses * Decimal('0.20'),
                             'operational_costs': base_expenses * Decimal('0.22'),
                             'staff_costs': base_expenses * Decimal('0.23'),
                             'utility_costs': base_expenses * Decimal('0.07'),
                             'other_expenses': base_expenses * Decimal('0.03'),
                             'passenger_count': random.randint(80000, 250000),
                             'flight_count': random.randint(1500, 4000),
                             'assessed_by': 'alex',
                             'approved_by': 'approver'}
                )
                assessment.calculate_totals().save()
                assessments.append(assessment)

        self.stdout.write(f"    Created {len(assessments)} fiscal assessments.")
        return assessments

    def _create_reports(self, airports):
        """Create reports."""
        reports = []
        report_types = [
            (ReportType.FISCAL_SUMMARY, "Fiscal Summary"),
            (ReportType.OPERATIONAL, "Operational Performance"),
            (ReportType.PASSENGER, "Passenger Analytics"),
            (ReportType.FINANCIAL, "Financial Analysis"),
            (ReportType.PERFORMANCE, "KPI Performance"),
        ]

        for airport in airports:
            for report_type, suffix in report_types:
                report, _ = Report.objects.get_or_create(
                    airport=airport, report_type=report_type.value,
                    title=f"{airport.code} {suffix} - {timezone.now().strftime('%B %Y')}",
                    defaults={'description': f"{suffix} Report",
                             'period_start': (timezone.now() - timedelta(days=30)).date(),
                             'period_end': timezone.now().date(),
                             'format': ReportFormat.HTML.value,
                             'generated_by': 'alex', 'is_generated': True,
                             'content': {'summary': f"Report for {airport.name}",
                                        'metrics': {'efficiency': round(random.uniform(0.85, 0.98), 2)}}}
                )
                reports.append(report)

        self.stdout.write(f"    Created {len(reports)} reports.")
        return reports

    def _create_documents(self, airports, assessments, reports):
        """Create documents."""
        doc_count = 0
        for airport in airports:
            Document.objects.get_or_create(
                name=f"{airport.code} Facility Agreement 2024",
                airport=airport,
                defaults={'document_type': Document.DocumentType.AGREEMENT.value,
                         'content': {'version': '2024.1'}, 'created_by': 'alex'}
            )
            doc_count += 1

        for assessment in assessments[:10]:
            Document.objects.get_or_create(
                name=f"Invoice INV-{assessment.id:05d}",
                fiscal_assessment=assessment,
                defaults={'document_type': Document.DocumentType.INVOICE.value,
                         'airport': assessment.airport,
                         'content': {'total': str(assessment.total_revenue)},
                         'created_by': 'alex'}
            )
            doc_count += 1

        self.stdout.write(f"    Created {doc_count} documents.")

    def _create_maintenance_records(self, gates, staff_members, airports):
        """Create maintenance logs and schedules."""
        maint_staff = [s for s in staff_members if s.role == StaffRole.MAINTENANCE.value] or staff_members[:5]
        logs_created = 0

        for gate in gates[:30]:
            MaintenanceLog.objects.get_or_create(
                equipment_type=MaintenanceLog.EquipmentType.GATE.value,
                equipment_id=gate.gate_id,
                description=f"Maintenance for {gate.gate_id}",
                defaults={'maintenance_type': MaintenanceType.ROUTINE.value,
                         'status': MaintenanceStatus.COMPLETED.value,
                         'started_at': timezone.now() - timedelta(days=random.randint(1, 60)),
                         'performed_by': random.choice(maint_staff),
                         'cost': Decimal(random.randint(500, 8000))}
            )
            logs_created += 1

        schedules_created = 0
        for airport in airports:
            for equip_type in ['gate', 'ground_equipment', 'baggage_system', 'security_equipment']:
                MaintenanceSchedule.objects.get_or_create(
                    title=f"{equip_type.replace('_', ' ').title()} Maintenance",
                    equipment_type=equip_type,
                    equipment_id=f"{airport.code}-{equip_type[:3].upper()}001",
                    airport=airport,
                    defaults={'frequency': random.choice(['weekly', 'monthly']),
                             'next_due': timezone.now() + timedelta(days=random.randint(1, 30)),
                             'priority': random.choice(['low', 'medium', 'high']),
                             'status': MaintenanceSchedule.Status.SCHEDULED.value,
                             'assigned_to': random.choice(maint_staff)}
                )
                schedules_created += 1

        self.stdout.write(f"    Created {logs_created} logs and {schedules_created} schedules.")

    def _create_incidents_and_events(self, flights, gates, staff_members):
        """Create incidents and event logs."""
        incidents_created = 0
        for i in range(10):
            IncidentReport.objects.get_or_create(
                title=f"Incident INC-{i+1:03d}",
                defaults={'incident_type': random.choice([t.value for t in IncidentType]),
                         'severity': random.choice([s.value for s in IncidentSeverity]),
                         'status': IncidentStatus.RESOLVED.value,
                         'description': f"Demo incident {i+1}",
                         'reported_by': random.choice(staff_members),
                         'date_occurred': timezone.now() - timedelta(days=random.randint(1, 60))}
            )
            incidents_created += 1

        # Create event logs (15 per day for 60 days = 900 events)
        events_created = 0
        event_types = [
            ('FLIGHT_CREATE', 'create', 'info'), ('FLIGHT_UPDATE', 'update', 'info'),
            ('FLIGHT_DELAY', 'update', 'warning'), ('PASSENGER_CHECKIN', 'create', 'info'),
            ('GATE_ASSIGNMENT', 'update', 'info'), ('BAGGAGE_LOADED', 'update', 'info'),
            ('MAINTENANCE_COMPLETE', 'update', 'info'), ('REPORT_GENERATED', 'export', 'info'),
            ('USER_LOGIN', 'login', 'info'), ('SYSTEM_ERROR', 'other', 'error'),
        ]

        admin_user = User.objects.filter(is_superuser=True).first()
        # Use bulk_create for better performance
        events_to_create = []
        for day in range(60):
            event_date = timezone.now() - timedelta(days=day)
            for _ in range(random.randint(10, 20)):
                event_type, action, severity = random.choice(event_types)
                events_to_create.append(EventLog(
                    event_type=event_type,
                    description=f"{event_type.replace('_', ' ').title()} event",
                    user=admin_user if random.random() > 0.2 else None,
                    action=action,
                    severity=severity,
                    flight=random.choice(flights[:200]) if flights and random.random() > 0.4 else None,
                    timestamp=event_date + timedelta(hours=random.randint(0, 23)),
                    ip_address=f"192.168.1.{random.randint(1, 254)}"
                ))
                
                if len(events_to_create) >= 500:
                    EventLog.objects.bulk_create(events_to_create)
                    events_created += len(events_to_create)
                    events_to_create = []
        
        # Create remaining events
        if events_to_create:
            EventLog.objects.bulk_create(events_to_create)
            events_created += len(events_to_create)

        self.stdout.write(f"    Created {incidents_created} incidents and {events_created} event logs.")
