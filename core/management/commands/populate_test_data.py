"""Management command to populate the database with realistic test data.

This command creates a comprehensive set of data for the Airport Operations
Management System, including users, airports, flights, staff, and more.

Usage:
    python manage.py populate_test_data
"""

import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from decimal import Decimal

from core.models import (
    Airport, Gate, Flight, Passenger, Staff, StaffAssignment, 
    EventLog, FiscalAssessment, Report, Document, Aircraft,
    CrewMember, MaintenanceLog, IncidentReport,
    GateStatus, FlightStatus, StaffRole, PassengerStatus,
    AssessmentPeriod, AssessmentStatus, ReportType, ReportFormat,
    AircraftType, AircraftStatus, CrewMemberType, CrewMemberStatus,
    MaintenanceType, MaintenanceStatus, IncidentType, IncidentSeverity
)

class Command(BaseCommand):
    """Command to populate the database with test data."""
    
    help = "Populate the database with realistic test data"

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write("Populating database with test data...")
        
        # 1. Setup permissions first
        self.stdout.write("Setting up permissions...")
        call_command('setup_permissions')
        
        # 2. Create Users
        self.stdout.write("Creating users...")
        self._create_users()
        
        # 3. Create Airports
        self.stdout.write("Creating airports...")
        airports = self._create_airports()
        
        # 4. Create Gates
        self.stdout.write("Creating gates...")
        gates = self._create_gates(airports)
        
        # 5. Create Staff
        self.stdout.write("Creating staff...")
        staff_members = self._create_staff()
        
        # 6. Create Aircraft
        self.stdout.write("Creating aircraft...")
        aircraft_list = self._create_aircraft()
        
        # 7. Create Crew Members
        self.stdout.write("Creating crew members...")
        crew_members = self._create_crew(airports)
        
        # 8. Create Flights
        self.stdout.write("Creating flights...")
        flights = self._create_flights(airports, gates)
        
        # 9. Create Passengers
        self.stdout.write("Creating passengers...")
        self._create_passengers(flights)
        
        # 10. Create Staff Assignments
        self.stdout.write("Creating staff assignments...")
        self._create_staff_assignments(flights, staff_members)
        
        # 11. Create Fiscal Assessments
        self.stdout.write("Creating fiscal assessments...")
        assessments = self._create_fiscal_assessments(airports)
        
        # 12. Create Reports
        self.stdout.write("Creating reports...")
        reports = self._create_reports(airports)
        
        # 13. Create Documents
        self.stdout.write("Creating documents...")
        self._create_documents(airports, assessments, reports)
        
        # 14. Create Maintenance Logs
        self.stdout.write("Creating maintenance logs...")
        self._create_maintenance_logs(gates, staff_members)
        
        # 15. Create Incident Reports
        self.stdout.write("Creating incident reports...")
        self._create_incident_reports(flights, gates, staff_members)
        
        # 16. Create Event Logs
        self.stdout.write("Creating event logs...")
        self._create_event_logs(flights)
        
        self.stdout.write(self.style.SUCCESS("Database populated successfully!"))

    def _create_users(self):
        """Create users with different roles."""
        # Admin (alex already exists, but ensure it's correct)
        admin_user, _ = User.objects.get_or_create(username='alex')
        admin_user.set_password('12345')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        
        # Editor
        editor_user, _ = User.objects.get_or_create(username='editor', email='editor@airportsim.local')
        editor_user.set_password('12345')
        editor_user.is_staff = True
        editor_user.save()
        editors_group = Group.objects.get(name='editors')
        editor_user.groups.add(editors_group)
        
        # Approver
        approver_user, _ = User.objects.get_or_create(username='approver', email='approver@airportsim.local')
        approver_user.set_password('12345')
        approver_user.is_staff = True
        approver_user.save()
        approvers_group = Group.objects.get(name='approvers')
        approver_user.groups.add(approvers_group)

    def _create_airports(self):
        """Create a set of airports."""
        airport_data = [
            {'code': 'LOS', 'name': 'Murtala Muhammed International Airport', 'city': 'Lagos', 'timezone': 'Africa/Lagos'},
            {'code': 'JFK', 'name': 'John F. Kennedy International Airport', 'city': 'New York', 'timezone': 'America/New_York'},
            {'code': 'LHR', 'name': 'London Heathrow Airport', 'city': 'London', 'timezone': 'Europe/London'},
            {'code': 'DXB', 'name': 'Dubai International Airport', 'city': 'Dubai', 'timezone': 'Asia/Dubai'},
            {'code': 'SIN', 'name': 'Singapore Changi Airport', 'city': 'Singapore', 'timezone': 'Asia/Singapore'},
        ]
        
        airports = []
        for data in airport_data:
            airport, _ = Airport.objects.get_or_create(code=data['code'], defaults=data)
            airports.append(airport)
        return airports

    def _create_gates(self, airports):
        """Create gates for airports."""
        terminals = ['T1', 'T2', 'T3']
        capacities = ['narrow-body', 'wide-body', 'regional']
        statuses = [GateStatus.AVAILABLE.value, GateStatus.OCCUPIED.value, GateStatus.MAINTENANCE.value]
        
        gates = []
        for airport in airports:
            for i in range(1, 6):
                gate_id = f"{airport.code}-G{i}"
                gate, _ = Gate.objects.get_or_create(
                    gate_id=gate_id,
                    defaults={
                        'terminal': random.choice(terminals),
                        'capacity': random.choice(capacities),
                        'status': random.choice(statuses)
                    }
                )
                gates.append(gate)
        return gates

    def _create_staff(self):
        """Create staff members."""
        first_names = ['James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        roles = [role.value for role in StaffRole]
        
        staff_members = []
        for i in range(1, 21):
            staff, _ = Staff.objects.get_or_create(
                employee_number=f"EMP{i:04d}",
                defaults={
                    'first_name': random.choice(first_names),
                    'last_name': random.choice(last_names),
                    'role': random.choice(roles),
                    'certification': "Safety-V1, Operations-A2",
                    'is_available': True,
                    'phone': f"+234-800-{i:04d}",
                    'email': f"staff{i}@airportsim.local"
                }
            )
            staff_members.append(staff)
        return staff_members

    def _create_aircraft(self):
        """Create aircraft."""
        manufacturers = ['Boeing', 'Airbus', 'Embraer', 'Bombardier']
        models = {
            'Boeing': ['737 MAX 8', '777-300ER', '787-9'],
            'Airbus': ['A320neo', 'A350-900', 'A380'],
            'Embraer': ['E195-E2', 'E175'],
            'Bombardier': ['CRJ900', 'Global 7500']
        }
        
        aircraft_list = []
        for i in range(1, 11):
            mfr = random.choice(manufacturers)
            model = random.choice(models[mfr])
            tail = f"N{i:03d}AF"
            
            aircraft, _ = Aircraft.objects.get_or_create(
                tail_number=tail,
                defaults={
                    'aircraft_type': random.choice([t.value for t in AircraftType]),
                    'model': model,
                    'manufacturer': mfr,
                    'capacity_passengers': random.randint(50, 400),
                    'capacity_cargo': Decimal(random.randint(5000, 50000)),
                    'status': AircraftStatus.ACTIVE.value,
                    'registration_country': 'USA',
                    'year_manufactured': random.randint(2010, 2023),
                    'total_flight_hours': Decimal(random.randint(100, 20000))
                }
            )
            aircraft_list.append(aircraft)
        return aircraft_list

    def _create_crew(self, airports):
        """Create crew members."""
        first_names = ['William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica']
        last_names = ['Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas']
        crew_types = [ctype.value for ctype in CrewMemberType]
        
        crew_list = []
        for i in range(1, 31):
            crew, _ = CrewMember.objects.get_or_create(
                employee_id=f"CREW{i:04d}",
                defaults={
                    'first_name': random.choice(first_names),
                    'last_name': random.choice(last_names),
                    'crew_type': random.choice(crew_types),
                    'license_number': f"LIC-{i:05d}",
                    'license_expiry': timezone.now().date() + timedelta(days=random.randint(30, 730)),
                    'status': CrewMemberStatus.AVAILABLE.value,
                    'total_flight_hours': Decimal(random.randint(500, 15000)),
                    'rank': random.choice(['Senior', 'Junior', 'Lead']),
                    'base_airport': random.choice(airports),
                    'hire_date': timezone.now().date() - timedelta(days=random.randint(365, 3650))
                }
            )
            crew_list.append(crew)
        return crew_list

    def _create_flights(self, airports, gates):
        """Create flights."""
        airlines = ['Delta', 'United', 'British Airways', 'Emirates', 'Air Peace', 'Lufthansa']
        statuses = [status.value for status in FlightStatus]
        
        flights = []
        now = timezone.now()
        
        # Use fixed flight numbers for idempotency
        prefixes = ['DL', 'UA', 'BA', 'EK', 'P4', 'LH']
        for i in range(1, 16):
            flight_number = f"{prefixes[i % len(prefixes)]}{100 + i}"
            origin = airports[i % len(airports)]
            destination = airports[(i + 1) % len(airports)]
            
            departure = now + timedelta(days=(i % 7) - 2, hours=i % 24)
            arrival = departure + timedelta(hours=(i % 12) + 2)
            
            gate = random.choice([g for g in gates if g.gate_id.startswith(origin.code)])
            
            flight, _ = Flight.objects.get_or_create(
                flight_number=flight_number,
                defaults={
                    'airline': random.choice(airlines),
                    'origin': origin.code,
                    'destination': destination.code,
                    'scheduled_departure': departure,
                    'scheduled_arrival': arrival,
                    'gate': gate,
                    'status': random.choice(statuses),
                    'delay_minutes': random.choice([0, 0, 0, 15, 30]),
                    'aircraft_type': random.choice(['B737', 'A320', 'B777'])
                }
            )
            flights.append(flight)
        return flights

    def _create_passengers(self, flights):
        """Create passengers for flights."""
        first_names = ['Thomas', 'Dorothy', 'Christopher', 'Karen', 'Daniel', 'Nancy', 'Matthew', 'Betty']
        last_names = ['Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White']
        
        for flight in flights:
            for i in range(1, 11):
                # Deterministic passport based on flight and index
                passport = f"P{flight.id:04d}{i:04d}"
                Passenger.objects.get_or_create(
                    passport_number=passport,
                    defaults={
                        'first_name': random.choice(first_names),
                        'last_name': random.choice(last_names),
                        'email': f"passenger{passport}@example.com",
                        'phone': f"+1-555-{i:04d}",
                        'flight': flight,
                        'seat_number': f"{i}{random.choice('ABCDEF')}",
                        'status': random.choice([s.value for s in PassengerStatus]),
                        'checked_bags': i % 3
                    }
                )

    def _create_staff_assignments(self, flights, staff_members):
        """Create staff assignments."""
        for flight in flights:
            # Assign deterministic staff
            for i in range(3):
                staff = staff_members[(flight.id + i) % len(staff_members)]
                try:
                    StaffAssignment.objects.get_or_create(
                        staff=staff,
                        flight=flight,
                        defaults={'assignment_type': staff.role}
                    )
                except Exception:
                    pass

    def _create_fiscal_assessments(self, airports):
        """Create comprehensive fiscal assessments with realistic data."""
        assessments = []
        statuses = [AssessmentStatus.DRAFT.value, AssessmentStatus.APPROVED.value, AssessmentStatus.COMPLETED.value]
        
        assessment_notes = [
            "Quarterly review shows a significant increase in retail revenue due to the new terminal shops.",
            "Operational costs are higher than expected due to emergency maintenance on Runway 2.",
            "Passenger counts have stabilized after the holiday peak.",
            "Fuel revenue is down by 5% compared to the previous period, reflecting lower global prices.",
            "Security costs increased due to the implementation of new biometric screening systems.",
            "Wait times at immigration have improved, contributing to higher passenger satisfaction scores.",
            "Cargo operations are seeing a steady 3% month-over-month growth.",
            "Parking revenue remains strong; considering expanding the long-term parking facility."
        ]

        for airport in airports:
            for i in range(1, 5):
                period_type = AssessmentPeriod.MONTHLY.value if i < 4 else AssessmentPeriod.QUARTERLY.value
                
                # Create dates for current and previous periods
                if period_type == AssessmentPeriod.MONTHLY.value:
                    start_date = (timezone.now() - timedelta(days=i*30)).date().replace(day=1)
                    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                else:
                    # Quarterly
                    start_date = (timezone.now() - timedelta(days=120)).date().replace(day=1)
                    end_date = (start_date + timedelta(days=92)).replace(day=1) - timedelta(days=1)
                
                # Variation based on airport and period
                multiplier = Decimal(1.0 + (random.random() * 0.4))
                base_rev = Decimal(1500000) * multiplier
                base_exp = Decimal(800000) * multiplier
                
                status = statuses[i % len(statuses)]
                approved_by = "approver" if status in [AssessmentStatus.APPROVED.value, AssessmentStatus.COMPLETED.value] else ""
                approved_at = timezone.now() - timedelta(days=random.randint(1, 5)) if approved_by else None

                assessment, created = FiscalAssessment.objects.get_or_create(
                    airport=airport,
                    period_type=period_type,
                    start_date=start_date,
                    end_date=end_date,
                    defaults={
                        'status': status,
                        'fuel_revenue': base_rev * Decimal('0.35'),
                        'parking_revenue': base_rev * Decimal('0.15'),
                        'retail_revenue': base_rev * Decimal('0.20'),
                        'landing_fees': base_rev * Decimal('0.18'),
                        'cargo_revenue': base_rev * Decimal('0.08'),
                        'other_revenue': base_rev * Decimal('0.04'),
                        'security_costs': base_exp * Decimal('0.28'),
                        'maintenance_costs': base_exp * Decimal('0.22'),
                        'operational_costs': base_exp * Decimal('0.20'),
                        'staff_costs': base_exp * Decimal('0.20'),
                        'utility_costs': base_exp * Decimal('0.07'),
                        'other_expenses': base_exp * Decimal('0.03'),
                        'passenger_count': random.randint(50000, 150000),
                        'flight_count': random.randint(800, 2500),
                        'assessed_by': "alex",
                        'approved_by': approved_by,
                        'approved_at': approved_at,
                        'assessment_notes': random.choice(assessment_notes)
                    }
                )
                
                if not created:
                    # Update existing with more detail
                    assessment.assessment_notes = random.choice(assessment_notes)
                    assessment.assessed_by = "alex"
                    assessment.status = status
                    assessment.save()
                    
                assessment.calculate_totals().save()
                assessments.append(assessment)
        return assessments

    def _create_reports(self, airports):
        """Create comprehensive reports with detailed JSON content."""
        reports = []
        report_types = [t.value for t in ReportType]
        
        descriptions = {
            ReportType.FISCAL_SUMMARY.value: "Comprehensive overview of airport financial performance, including revenue streams and cost centers.",
            ReportType.OPERATIONAL.value: "Analysis of flight operations, gate utilization, and overall system efficiency.",
            ReportType.PASSENGER.value: "Demographic and flow analysis of passengers through the terminal facilities.",
            ReportType.FINANCIAL.value: "Detailed breakdown of profit and loss, capital expenditures, and budget variances.",
            ReportType.PERFORMANCE.value: "Key Performance Indicators (KPIs) comparison against industry benchmarks.",
            ReportType.COMPLIANCE.value: "Audit of safety, security, and environmental regulation compliance."
        }
        
        for airport in airports:
            for r_type in report_types:
                title = f"{airport.code} {r_type.replace('_', ' ').title()} Report - 2024"
                
                # Create structured content for the report
                content = {
                    "summary": f"This {r_type.replace('_', ' ').title()} report for {airport.name} covers the recent operational period, highlighting key performance indicators and areas for improvement.",
                    "key_findings": [
                        "Overall efficiency increased by 4.2% compared to the baseline.",
                        "Resource utilization peaked during the mid-morning shift.",
                        "Identified potential for 12% reduction in utility costs through automation."
                    ],
                    "metrics": {
                        "efficiency_score": round(random.uniform(0.75, 0.98), 2),
                        "reliability_index": round(random.uniform(0.85, 0.99), 2),
                        "cost_per_passenger": round(random.uniform(12.50, 25.00), 2)
                    },
                    "recommendations": [
                        "Invest in secondary runway maintenance systems.",
                        "Implement automated check-in kiosks in Terminal B.",
                        "Review security staffing levels during peak weekend hours."
                    ]
                }

                report, created = Report.objects.get_or_create(
                    airport=airport,
                    title=title,
                    report_type=r_type,
                    defaults={
                        'description': descriptions.get(r_type, "Detailed operational analysis."),
                        'period_start': (timezone.now() - timedelta(days=90)).date(),
                        'period_end': timezone.now().date(),
                        'format': random.choice([ReportFormat.HTML.value, ReportFormat.PDF.value]),
                        'generated_by': "alex",
                        'is_generated': True,
                        'generated_at': timezone.now() - timedelta(hours=random.randint(1, 48)),
                        'content': content
                    }
                )
                
                if not created:
                    report.content = content
                    report.is_generated = True
                    report.save()
                    
                reports.append(report)
        return reports

    def _create_documents(self, airports, assessments, reports):
        """Create comprehensive documents tied to assessments and reports."""
        # 1. Facility Agreements
        for airport in airports:
            name = f"{airport.code} Facility Access Agreement - 2024 Rev A"
            Document.objects.get_or_create(
                name=name,
                airport=airport,
                defaults={
                    'document_type': Document.DocumentType.AGREEMENT.value,
                    'content': {
                        "version": "2024.1",
                        "sections": [
                            {"title": "1. Scope", "text": "This agreement covers all ground services and facility access."},
                            {"title": "2. Fees", "text": "Fees are calculated based on aircraft weight and duration of stay."},
                            {"title": "3. Liability", "text": "Standard liability clauses apply as per international regulations."}
                        ],
                        "signatories": ["Airport Authority", "Airline Representative"]
                    },
                    'created_by': "alex"
                }
            )
        
        # 2. Invoices for Assessments
        for assessment in assessments:
            if assessment.status != AssessmentStatus.DRAFT.value:
                name = f"Invoice INV-{assessment.id:05d} - {assessment.airport.code}"
                Document.objects.get_or_create(
                    name=name,
                    fiscal_assessment=assessment,
                    defaults={
                        'document_type': Document.DocumentType.INVOICE.value,
                        'airport': assessment.airport,
                        'content': {
                            "invoice_number": f"INV-{assessment.id:05d}",
                            "date": assessment.start_date.strftime("%Y-%m-%d"),
                            "total_amount": str(assessment.total_revenue),
                            "items": [
                                {"desc": "Fuel Services", "amount": str(assessment.fuel_revenue)},
                                {"desc": "Landing Fees", "amount": str(assessment.landing_fees)},
                                {"desc": "Retail Concessions", "amount": str(assessment.retail_revenue)}
                            ],
                            "status": "Paid" if assessment.status == AssessmentStatus.COMPLETED.value else "Outstanding"
                        },
                        'created_by': "alex"
                    }
                )

        # 3. Certificates for Airports
        for airport in airports:
            name = f"Safety Compliance Certificate - {airport.code}"
            Document.objects.get_or_create(
                name=name,
                airport=airport,
                defaults={
                    'document_type': Document.DocumentType.CERTIFICATE.value,
                    'content': {
                        "cert_number": f"CERT-{airport.code}-2024",
                        "issue_date": "2024-01-15",
                        "expiry_date": "2025-01-14",
                        "authority": "International Aviation Safety Board",
                        "rating": "A+"
                    },
                    'created_by': "alex"
                }
            )

    def _create_maintenance_logs(self, gates, staff_members):
        """Create maintenance logs."""
        maintenance_staff = [s for s in staff_members if s.role == StaffRole.MAINTENANCE.value]
        if not maintenance_staff:
            maintenance_staff = staff_members
            
        for i, gate in enumerate(gates[:5]):
            MaintenanceLog.objects.get_or_create(
                equipment_type=MaintenanceLog.EquipmentType.GATE.value,
                equipment_id=gate.gate_id,
                description=f"Maintenance for {gate.gate_id}",
                defaults={
                    'maintenance_type': MaintenanceType.ROUTINE.value,
                    'status': MaintenanceStatus.COMPLETED.value,
                    'started_at': timezone.now() - timedelta(days=i+1),
                    'performed_by': maintenance_staff[i % len(maintenance_staff)],
                    'cost': Decimal(1000 + (i * 100))
                }
            )

    def _create_incident_reports(self, flights, gates, staff_members):
        """Create incident reports."""
        for i in range(1, 6):
            title = f"Incident INC-{i:03d}"
            flight = flights[i % len(flights)]
            gate = gates[i % len(gates)]
            
            IncidentReport.objects.get_or_create(
                title=title,
                defaults={
                    'incident_type': IncidentType.OPERATIONAL.value,
                    'severity': IncidentSeverity.LOW.value,
                    'status': 'reported',
                    'description': "Automated test incident.",
                    'location': gate.gate_id,
                    'reported_by': staff_members[i % len(staff_members)],
                    'date_occurred': timezone.now() - timedelta(days=i),
                    'related_flight': flight,
                    'related_gate': gate
                }
            )

    def _create_event_logs(self, flights):
        """Create event logs."""
        admin_user = User.objects.get(username='alex')
        for i in range(1, 11):
            flight = flights[i % len(flights)]
            EventLog.objects.get_or_create(
                description=f"Test event {i} for {flight.flight_number}",
                defaults={
                    'event_type': "SYSTEM_TEST",
                    'user': admin_user,
                    'action': 'other',
                    'severity': 'info',
                    'flight': flight,
                    'timestamp': timezone.now() - timedelta(hours=i)
                }
            )
