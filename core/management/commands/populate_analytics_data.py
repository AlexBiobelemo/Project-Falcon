"""Management command to populate extensive demo data for professional analytics demonstration.

This command creates a LARGE, comprehensive dataset for the Airport Operations
Management System, optimized for showcasing analytics, dashboards, and reporting.

Generates:
- 6 months of historical flight data
- Extensive passenger bookings
- Comprehensive fiscal assessments (6 months)
- Rich event logs for audit trails
- Multiple reports and documents
- Maintenance records
- Incident reports
- Staff schedules

Usage:
    python manage.py populate_analytics_data
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.core.management import call_command

from core.models import (
    # Core models
    Airport, Gate, Flight, Passenger, Staff, StaffAssignment, EventLog,
    # Financial models
    FiscalAssessment, Report, Document,
    # Aircraft & Crew models
    Aircraft, CrewMember,
    # Maintenance models
    MaintenanceLog, MaintenanceSchedule,
    # Incident & Safety models
    IncidentReport,
    # Scheduling models
    Shift, StaffShiftAssignment,
    # Baggage models
    Baggage,
    # Report scheduling
    ReportSchedule,
    # Enums
    GateStatus, FlightStatus, StaffRole, PassengerStatus,
    AssessmentPeriod, AssessmentStatus, ReportType, ReportFormat,
    AircraftType, AircraftStatus, CrewMemberType, CrewMemberStatus,
    MaintenanceType, MaintenanceStatus, IncidentType, IncidentSeverity, IncidentStatus,
)


class Command(BaseCommand):
    """Command to populate extensive analytics-ready demo data."""

    help = "Populate extensive demo data optimized for analytics and dashboard demonstration"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before populating',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Skip confirmation prompts',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("AIRPORT OPERATIONS MANAGEMENT SYSTEM"))
        self.stdout.write(self.style.SUCCESS("EXTENSIVE ANALYTICS DATA POPULATION"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")

        # Confirm large data population
        self.stdout.write(self.style.WARNING("This will create a LARGE dataset optimized for analytics."))
        self.stdout.write(self.style.WARNING("Expected: 500+ flights, 5000+ passengers, 6 months of data"))
        self.stdout.write("")
        
        if not options['no_input']:
            confirm = input("Proceed with extensive data population? (y/n): ").lower().strip()
            if confirm != 'y':
                self.stdout.write("Operation cancelled.")
                return

        clear_data = options['clear']
        if not clear_data and not options['no_input']:
            clear_data = input("Clear existing demo data first? (y/n): ").lower().strip() == 'y'
            
        if clear_data:
            self.stdout.write("Clearing existing demo data...")
            self._clear_existing_data()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))
            self.stdout.write("")

        # 1. Setup permissions
        self.stdout.write("[1/12] Setting up permissions and groups...")
        self._setup_permissions()

        # 2. Create Users
        self.stdout.write("[2/12] Creating users with roles...")
        users = self._create_users()

        # 3. Create Airports
        self.stdout.write("[3/12] Creating airports...")
        airports = self._create_airports()

        # 4. Create Gates
        self.stdout.write("[4/12] Creating gates...")
        gates = self._create_gates(airports)

        # 5. Create Staff
        self.stdout.write("[5/12] Creating staff members...")
        staff_members = self._create_staff()

        # 6. Create Aircraft
        self.stdout.write("[6/12] Creating aircraft fleet...")
        aircraft_list = self._create_aircraft()

        # 7. Create Crew Members
        self.stdout.write("[7/12] Creating crew members...")
        crew_members = self._create_crew(airports)

        # 8. Create EXTENSIVE Flights (6 months history)
        self.stdout.write("[8/12] Creating extensive flight schedule (6 months)...")
        flights = self._create_extensive_flights(airports, gates, aircraft_list)

        # 9. Create EXTENSIVE Passengers
        self.stdout.write("[9/12] Creating extensive passenger bookings...")
        self._create_extensive_passengers(flights)

        # 10. Create Baggage records
        self.stdout.write("[10/12] Creating baggage records...")
        self._create_baggage(flights)

        # 11. Create Staff Assignments
        self.stdout.write("[11/12] Creating staff assignments and shifts...")
        self._create_staff_assignments(flights, staff_members)
        self._create_shifts(staff_members)

        # 12. Create Fiscal Assessments (6 months)
        self.stdout.write("[12/12] Creating fiscal assessments (6 months)...")
        assessments = self._create_extensive_fiscal_assessments(airports)

        # Create Reports and Documents
        self.stdout.write("[BONUS] Creating reports and documents...")
        reports = self._create_reports(airports)
        self._create_documents(airports, assessments, reports)

        # Create Maintenance Records
        self.stdout.write("[BONUS] Creating maintenance records...")
        self._create_maintenance_records(gates, staff_members, airports)

        # Create Incidents and Events
        self.stdout.write("[BONUS] Creating incident reports and event logs...")
        self._create_incidents_and_events(flights, gates, staff_members, users)

        # Create Report Schedules
        self.stdout.write("[BONUS] Creating report schedules...")
        self._create_report_schedules(airports, users)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("EXTENSIVE DEMO DATA POPULATION COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo Credentials:"))
        self.stdout.write("  Admin:     alex / 12345")
        self.stdout.write("  Editor:    editor / 12345")
        self.stdout.write("  Approver:  approver / 12345")
        self.stdout.write("  Viewer:    viewer / 12345")
        self.stdout.write("  Operations: operations / 12345")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Analytics-Ready Data Summary:"))
        self.stdout.write(f"  - {len(airports)} International Airports")
        self.stdout.write(f"  - {len(gates)} Gates")
        self.stdout.write(f"  - {len(flights)} Flights (6 months history)")
        self.stdout.write(f"  - {Passenger.objects.count()} Passenger Bookings")
        self.stdout.write(f"  - {Baggage.objects.count()} Baggage Records")
        self.stdout.write(f"  - {len(staff_members)} Staff Members")
        self.stdout.write(f"  - {len(crew_members)} Crew Members")
        self.stdout.write(f"  - {len(aircraft_list)} Aircraft")
        self.stdout.write(f"  - {len(assessments)} Fiscal Assessments")
        self.stdout.write(f"  - {Report.objects.count()} Reports")
        self.stdout.write(f"  - {Document.objects.count()} Documents")
        self.stdout.write(f"  - {EventLog.objects.count()} Event Log Entries")
        self.stdout.write(f"  - {IncidentReport.objects.count()} Incident Reports")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Dashboard Features Ready:"))
        self.stdout.write("  ✓ Flight trends (6 months)")
        self.stdout.write("  ✓ Passenger analytics")
        self.stdout.write("  ✓ Revenue tracking")
        self.stdout.write("  ✓ Gate utilization")
        self.stdout.write("  ✓ Staff scheduling")
        self.stdout.write("  ✓ On-time performance")
        self.stdout.write("  ✓ Baggage tracking")
        self.stdout.write("  ✓ Incident reporting")
        self.stdout.write("")

    def _clear_existing_data(self):
        """Clear existing demo data."""
        Baggage.objects.all().delete()
        StaffShiftAssignment.objects.all().delete()
        Shift.objects.all().delete()
        StaffAssignment.objects.all().delete()
        Document.objects.all().delete()
        Report.objects.all().delete()
        ReportSchedule.objects.all().delete()
        FiscalAssessment.objects.all().delete()
        MaintenanceLog.objects.all().delete()
        MaintenanceSchedule.objects.all().delete()
        IncidentReport.objects.all().delete()
        EventLog.objects.all().delete()
        Passenger.objects.all().delete()
        Flight.objects.all().delete()
        CrewMember.objects.all().delete()
        Aircraft.objects.all().delete()
        Gate.objects.all().delete()
        self.stdout.write("  All demo data cleared.")

    def _setup_permissions(self):
        """Setup permission groups."""
        call_command('setup_permissions', verbosity=0)

    def _create_users(self):
        """Create users with different roles."""
        users = {}

        # Admin
        admin_user, _ = User.objects.get_or_create(
            username='alex',
            defaults={'email': 'alex@airportsim.local', 'is_staff': True, 'is_superuser': True,
                     'first_name': 'Alexander', 'last_name': 'Admin'}
        )
        admin_user.set_password('12345')
        admin_user.save()
        users['admin'] = admin_user

        # Editor
        editor_user, _ = User.objects.get_or_create(
            username='editor',
            defaults={'email': 'editor@airportsim.local', 'is_staff': True,
                     'first_name': 'Emma', 'last_name': 'Editor'}
        )
        editor_user.set_password('12345')
        editor_user.save()
        Group.objects.get_or_create(name='editors')
        editor_user.groups.add(Group.objects.get(name='editors'))
        users['editor'] = editor_user

        # Approver
        approver_user, _ = User.objects.get_or_create(
            username='approver',
            defaults={'email': 'approver@airportsim.local', 'is_staff': True,
                     'first_name': 'Andrew', 'last_name': 'Approver'}
        )
        approver_user.set_password('12345')
        approver_user.save()
        Group.objects.get_or_create(name='approvers')
        approver_user.groups.add(Group.objects.get(name='approvers'))
        users['approver'] = approver_user

        # Viewer
        viewer_user, _ = User.objects.get_or_create(
            username='viewer',
            defaults={'email': 'viewer@airportsim.local', 'is_staff': False,
                     'first_name': 'Victoria', 'last_name': 'Viewer'}
        )
        viewer_user.set_password('12345')
        viewer_user.save()
        Group.objects.get_or_create(name='viewers')
        viewer_user.groups.add(Group.objects.get(name='viewers'))
        users['viewer'] = viewer_user

        # Operations
        ops_user, _ = User.objects.get_or_create(
            username='operations',
            defaults={'email': 'operations@airportsim.local', 'is_staff': True,
                     'first_name': 'Oliver', 'last_name': 'Operations'}
        )
        ops_user.set_password('12345')
        ops_user.save()
        ops_user.groups.add(Group.objects.get(name='editors'))
        users['operations'] = ops_user

        return users

    def _create_airports(self):
        """Create international airports."""
        airport_data = [
            {'code': 'LOS', 'name': "Murtala Muhammed International Airport", 'city': 'Lagos', 'country': 'Nigeria', 'timezone': 'Africa/Lagos', 'lat': Decimal('6.5774'), 'lon': Decimal('3.3212')},
            {'code': 'JFK', 'name': "John F. Kennedy International Airport", 'city': 'New York', 'country': 'USA', 'timezone': 'America/New_York', 'lat': Decimal('40.6413'), 'lon': Decimal('-73.7781')},
            {'code': 'LHR', 'name': "London Heathrow Airport", 'city': 'London', 'country': 'UK', 'timezone': 'Europe/London', 'lat': Decimal('51.4700'), 'lon': Decimal('-0.4543')},
            {'code': 'DXB', 'name': "Dubai International Airport", 'city': 'Dubai', 'country': 'UAE', 'timezone': 'Asia/Dubai', 'lat': Decimal('25.2532'), 'lon': Decimal('55.3657')},
            {'code': 'SIN', 'name': "Singapore Changi Airport", 'city': 'Singapore', 'country': 'Singapore', 'timezone': 'Asia/Singapore', 'lat': Decimal('1.3644'), 'lon': Decimal('103.9915')},
            {'code': 'FRA', 'name': "Frankfurt Airport", 'city': 'Frankfurt', 'country': 'Germany', 'timezone': 'Europe/Berlin', 'lat': Decimal('50.0379'), 'lon': Decimal('8.5622')},
            {'code': 'NRT', 'name': "Narita International Airport", 'city': 'Tokyo', 'country': 'Japan', 'timezone': 'Asia/Tokyo', 'lat': Decimal('35.7720'), 'lon': Decimal('140.3929')},
            {'code': 'SYD', 'name': "Sydney Kingsford Smith Airport", 'city': 'Sydney', 'country': 'Australia', 'timezone': 'Australia/Sydney', 'lat': Decimal('-33.9399'), 'lon': Decimal('151.1753')},
            {'code': 'CDG', 'name': "Charles de Gaulle Airport", 'city': 'Paris', 'country': 'France', 'timezone': 'Europe/Paris', 'lat': Decimal('49.0097'), 'lon': Decimal('2.5479')},
            {'code': 'AMS', 'name': "Amsterdam Airport Schiphol", 'city': 'Amsterdam', 'country': 'Netherlands', 'timezone': 'Europe/Amsterdam', 'lat': Decimal('52.3105'), 'lon': Decimal('4.7683')},
        ]

        airports = []
        for data in airport_data:
            airport, _ = Airport.objects.get_or_create(
                code=data['code'],
                defaults={'name': data['name'], 'city': data['city'], 'timezone': data['timezone'],
                         'latitude': data.get('lat'), 'longitude': data.get('lon'), 'is_active': True}
            )
            airports.append(airport)
        return airports

    def _create_gates(self, airports):
        """Create gates for all airports."""
        gates = []
        terminal_config = {
            'T1': {'capacity': 'regional', 'count': 6},
            'T2': {'capacity': 'narrow-body', 'count': 8},
            'T3': {'capacity': 'wide-body', 'count': 6},
        }

        for airport in airports:
            for terminal, config in terminal_config.items():
                for i in range(1, config['count'] + 1):
                    gate_id = f"{airport.code}-{terminal}{i:02d}"
                    gate, created = Gate.objects.get_or_create(
                        gate_id=gate_id,
                        defaults={'terminal': terminal, 'capacity': config['capacity'],
                                 'status': random.choice([GateStatus.AVAILABLE.value] * 5 + 
                                                        [GateStatus.OCCUPIED.value, GateStatus.MAINTENANCE.value])}
                    )
                    if created:
                        gates.append(gate)
        return gates

    def _create_staff(self):
        """Create extensive staff roster."""
        staff_data = []
        roles_config = [
            (StaffRole.GROUND_CREW.value, 15, 'Ground Ops'),
            (StaffRole.SECURITY.value, 10, 'Security'),
            (StaffRole.MAINTENANCE.value, 8, 'Maintenance'),
            (StaffRole.CLEANING.value, 10, 'Cleaning'),
            (StaffRole.PILOT.value, 12, 'ATP'),
            (StaffRole.CO_PILOT.value, 10, 'Commercial'),
            (StaffRole.CABIN_CREW.value, 20, 'FA'),
        ]

        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
                      'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
                      'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
                      'Matthew', 'Betty', 'Mark', 'Sandra', 'Steven', 'Ashley', 'Paul', 'Kimberly',
                      'Andrew', 'Emily', 'Joshua', 'Donna', 'Kenneth', 'Michelle', 'Kevin', 'Dorothy']

        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                     'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
                     'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
                     'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker']

        emp_num = 1
        for role, count, cert_prefix in roles_config:
            for i in range(count):
                staff_data.append({
                    'first_name': random.choice(first_names),
                    'last_name': random.choice(last_names),
                    'role': role,
                    'cert': f"{cert_prefix}-{random.randint(1000, 9999)}",
                    'emp_num': f"EMP{emp_num:04d}"
                })
                emp_num += 1

        staff_members = []
        for data in staff_data:
            staff, _ = Staff.objects.get_or_create(
                employee_number=data['emp_num'],
                defaults={'first_name': data['first_name'], 'last_name': data['last_name'],
                         'role': data['role'], 'certification': data['cert'], 'is_available': True,
                         'email': f"staff{data['emp_num']}@airportsim.local", 'phone': f"+234-800-{data['emp_num']}"}
            )
            staff_members.append(staff)
        return staff_members

    def _create_aircraft(self):
        """Create diverse aircraft fleet."""
        aircraft_data = [
            ('N101AF', AircraftType.NARROW_BODY, 'Boeing', '737-800', 162, 4400),
            ('N102AF', AircraftType.NARROW_BODY, 'Boeing', '737 MAX 8', 172, 4500),
            ('N103AF', AircraftType.NARROW_BODY, 'Airbus', 'A320neo', 165, 4200),
            ('N104AF', AircraftType.NARROW_BODY, 'Airbus', 'A321neo', 194, 4800),
            ('N105AF', AircraftType.NARROW_BODY, 'Airbus', 'A319', 145, 3900),
            ('N201AF', AircraftType.WIDE_BODY, 'Boeing', '777-300ER', 350, 20000),
            ('N202AF', AircraftType.WIDE_BODY, 'Boeing', '787-9', 290, 17000),
            ('N203AF', AircraftType.WIDE_BODY, 'Airbus', 'A350-900', 315, 18000),
            ('N204AF', AircraftType.WIDE_BODY, 'Airbus', 'A330-300', 277, 15000),
            ('N205AF', AircraftType.WIDE_BODY, 'Boeing', '747-8', 410, 25000),
            ('N301AF', AircraftType.REGIONAL, 'Embraer', 'E195-E2', 146, 3500),
            ('N302AF', AircraftType.REGIONAL, 'Embraer', 'E175', 88, 2500),
            ('N303AF', AircraftType.REGIONAL, 'Bombardier', 'CRJ900', 90, 2800),
            ('N304AF', AircraftType.REGIONAL, 'Bombardier', 'CRJ700', 78, 2400),
            ('N401AF', AircraftType.CARGO, 'Boeing', '747-8F', 0, 140000),
            ('N402AF', AircraftType.CARGO, 'Boeing', '767-300F', 0, 52000),
            ('N403AF', AircraftType.CARGO, 'Airbus', 'A330-200F', 0, 70000),
        ]

        aircraft_list = []
        for tail, atype, mfr, model, pax, cargo in aircraft_data:
            aircraft, _ = Aircraft.objects.get_or_create(
                tail_number=tail,
                defaults={'aircraft_type': atype.value, 'model': model, 'manufacturer': mfr,
                         'capacity_passengers': pax, 'capacity_cargo': Decimal(cargo),
                         'status': AircraftStatus.ACTIVE.value, 'registration_country': 'USA',
                         'year_manufactured': random.randint(2015, 2024),
                         'total_flight_hours': Decimal(random.randint(500, 15000))}
            )
            aircraft_list.append(aircraft)
        return aircraft_list

    def _create_crew(self, airports):
        """Create crew members."""
        crew_data = [
            (CrewMemberType.PILOT, 'Captain', 12000, 15000),
            (CrewMemberType.PILOT, 'Captain', 10000, 14000),
            (CrewMemberType.PILOT, 'Senior Captain', 15000, 18000),
            (CrewMemberType.FIRST_OFFICER, 'First Officer', 3000, 6000),
            (CrewMemberType.FIRST_OFFICER, 'First Officer', 4000, 7000),
            (CrewMemberType.FIRST_OFFICER, 'Senior FO', 6000, 9000),
            (CrewMemberType.FLIGHT_ATTENDANT, 'Flight Attendant', 2000, 5000),
            (CrewMemberType.FLIGHT_ATTENDANT, 'Flight Attendant', 3000, 6000),
            (CrewMemberType.FLIGHT_ATTENDANT, 'Flight Attendant', 2500, 5500),
            (CrewMemberType.LEAD_FATTENDANT, 'Lead FA', 7000, 10000),
            (CrewMemberType.LEAD_FATTENDANT, 'Purser', 8000, 12000),
        ]

        first_names = ['Captain John', 'Captain Maria', 'Captain Ahmed', 'Captain Yuki',
                      'FO Michael', 'FO Sophie', 'FO David', 'FA Emily', 'FA Carlos',
                      'FA Aisha', 'LFA Rachel', 'LFA Thomas']

        crew_members = []
        for i, ((ctype, rank, min_h, max_h)) in enumerate(crew_data, start=1):
            crew, _ = CrewMember.objects.get_or_create(
                employee_id=f"CREW{i:04d}",
                defaults={'first_name': first_names[i-1] if i <= len(first_names) else f'Crew{i}',
                         'last_name': f'CrewMember{i}', 'crew_type': ctype.value,
                         'license_number': f"LIC-{i:05d}-FAA",
                         'license_expiry': timezone.now().date() + timedelta(days=random.randint(180, 730)),
                         'status': CrewMemberStatus.AVAILABLE.value,
                         'total_flight_hours': Decimal(random.randint(min_h, max_h)),
                         'rank': rank, 'base_airport': random.choice(airports),
                         'hire_date': timezone.now().date() - timedelta(days=random.randint(365, 2500))}
            )
            crew_members.append(crew)
        return crew_members

    def _create_extensive_flights(self, airports, gates, aircraft_list):
        """Create 6 months of flight history for analytics."""
        airlines = [
            ('Delta Air Lines', 'DL'), ('United Airlines', 'UA'), ('British Airways', 'BA'),
            ('Emirates', 'EK'), ('Lufthansa', 'LH'), ('Air Peace', 'P4'),
            ('Singapore Airlines', 'SQ'), ('Qatar Airways', 'QR'), ('Air France', 'AF'),
            ('KLM', 'KL'), ('American Airlines', 'AA'), ('Turkish Airlines', 'TK'),
        ]

        aircraft_types = ['B737', 'B777', 'A320', 'A350', 'E195', 'B747', 'A330']
        now = timezone.now()
        flights = []

        # Generate flights for each day in the past 180 days
        for day_offset in range(180, -1, -1):
            flight_date = now - timedelta(days=day_offset)
            
            # 3-8 flights per day depending on weekday
            num_flights = random.randint(3, 8) if flight_date.weekday() < 5 else random.randint(2, 5)
            
            for flight_num in range(num_flights):
                airline = random.choice(airlines)
                flight_number = f"{airline[1]}{random.randint(100, 9999)}"
                origin = random.choice(airports)
                destination = random.choice([a for a in airports if a != origin])

                # Random departure time throughout the day
                departure_hour = random.randint(6, 22)
                departure_minute = random.choice([0, 15, 30, 45])
                scheduled_departure = flight_date.replace(
                    hour=departure_hour, minute=departure_minute, second=0, microsecond=0
                )

                # Flight duration 2-14 hours
                flight_duration = timedelta(hours=random.randint(2, 14))
                scheduled_arrival = scheduled_departure + flight_duration

                # Select gate
                origin_gates = [g for g in gates if g.gate_id.startswith(origin.code)]
                gate = random.choice(origin_gates) if origin_gates else None

                # Determine status based on date
                if day_offset > 2:
                    status = random.choice([FlightStatus.DEPARTED, FlightStatus.ARRIVED, FlightStatus.ARRIVED])
                elif day_offset > 0:
                    status = random.choice([FlightStatus.DEPARTED, FlightStatus.BOARDING, FlightStatus.SCHEDULED])
                else:
                    status = random.choice([FlightStatus.SCHEDULED] * 3 + [FlightStatus.DELAYED])

                delay = 0
                if status == FlightStatus.DELAYED:
                    delay = random.choice([15, 30, 45, 60, 90, 120])
                elif random.random() < 0.15:  # 15% chance of minor delay
                    delay = random.randint(5, 25)

                try:
                    flight, _ = Flight.objects.get_or_create(
                        flight_number=flight_number,
                        scheduled_departure=scheduled_departure,
                        defaults={'airline': airline[0], 'origin': origin.code,
                                 'destination': destination.code, 'scheduled_arrival': scheduled_arrival,
                                 'gate': gate, 'status': status.value, 'delay_minutes': delay,
                                 'aircraft_type': random.choice(aircraft_types)}
                    )

                    # Set actual times for completed flights
                    if status == FlightStatus.DEPARTED:
                        flight.actual_departure = scheduled_departure + timedelta(minutes=delay)
                        flight.save()
                    elif status == FlightStatus.ARRIVED:
                        flight.actual_departure = scheduled_departure + timedelta(minutes=delay)
                        flight.actual_arrival = scheduled_arrival + timedelta(minutes=random.randint(0, 30))
                        flight.save()

                    flights.append(flight)
                except Exception:
                    pass  # Skip duplicates

        self.stdout.write(f"    Created {len(flights)} flights spanning 6 months.")
        return flights

    def _create_extensive_passengers(self, flights):
        """Create extensive passenger bookings."""
        first_names = [
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
            'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
            'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
            'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
            'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
            'Kevin', 'Carol', 'Brian', 'Amanda', 'George', 'Melissa', 'Edward', 'Deborah',
            'Ronald', 'Stephanie', 'Timothy', 'Rebecca', 'Jason', 'Sharon', 'Jeffrey', 'Cynthia',
            'Ryan', 'Kathleen', 'Jacob', 'Amy', 'Gary', 'Angela', 'Nicholas', 'Shirley',
        ]

        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
            'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
            'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell',
        ]

        passenger_count = 0
        statuses = [PassengerStatus.CHECKED_IN, PassengerStatus.CHECKED_IN, PassengerStatus.BOARDED, PassengerStatus.ARRIVED]

        for flight in flights:
            # 15-35 passengers per flight
            num_passengers = random.randint(15, 35)
            for i in range(num_passengers):
                passport = f"P{flight.id:05d}{i:04d}"
                
                # Status depends on flight status
                if flight.status == FlightStatus.ARRIVED:
                    status = PassengerStatus.ARRIVED
                elif flight.status == FlightStatus.DEPARTED:
                    status = random.choice([PassengerStatus.BOARDED, PassengerStatus.ARRIVED])
                elif flight.status == FlightStatus.BOARDING:
                    status = random.choice([PassengerStatus.CHECKED_IN, PassengerStatus.BOARDED])
                else:
                    status = PassengerStatus.CHECKED_IN

                Passenger.objects.get_or_create(
                    passport_number=passport,
                    defaults={'first_name': random.choice(first_names),
                             'last_name': random.choice(last_names),
                             'email': f"pass{passport}@example.com",
                             'phone': f"+1-555-{random.randint(1000, 9999)}",
                             'flight': flight,
                             'seat_number': f"{random.randint(1, 35)}{random.choice('ABCDEF')}",
                             'status': status.value,
                             'checked_bags': random.randint(0, 3)}
                )
                passenger_count += 1

        self.stdout.write(f"    Created {passenger_count} passenger bookings.")

    def _create_baggage(self, flights):
        """Create baggage records."""
        baggage_count = 0
        statuses = [Baggage.BaggageStatus.CHECKED_IN, Baggage.BaggageStatus.SCREENED,
                   Baggage.BaggageStatus.SORTED, Baggage.BaggageStatus.LOADED]

        for flight in flights:
            passengers = flight.passengers.all()
            for passenger in passengers:
                if passenger.checked_bags > 0:
                    for bag_num in range(passenger.checked_bags):
                        tag = f"{flight.flight_number.replace(' ', '')}{bag_num + 1:03d}{passenger.passenger_id.hex[:4].upper()}"
                        
                        if flight.status == FlightStatus.ARRIVED:
                            status = Baggage.BaggageStatus.CLAIMED
                        else:
                            status = random.choice(statuses)

                        Baggage.objects.get_or_create(
                            tag_number=tag[:20],
                            defaults={'passenger': passenger, 'flight': flight,
                                     'status': status.value, 'origin': flight.origin,
                                     'destination': flight.destination,
                                     'weight': Decimal(f"{random.randint(15, 32)}.{random.randint(0, 9)}"),
                                     'pieces': 1,
                                     'location': f"Terminal {random.choice(['1', '2', '3'])}, Belt {random.randint(1, 12)}"}
                        )
                        baggage_count += 1

        self.stdout.write(f"    Created {baggage_count} baggage records.")

    def _create_staff_assignments(self, flights, staff_members):
        """Assign staff to flights."""
        assignments = 0
        roles_for_assignment = [StaffRole.GROUND_CREW.value, StaffRole.SECURITY.value, StaffRole.CLEANING.value]
        eligible_staff = [s for s in staff_members if s.role in roles_for_assignment]

        for flight in flights:
            num_assignments = random.randint(2, 5)
            assigned = random.sample(eligible_staff, min(num_assignments, len(eligible_staff)))

            for staff in assigned:
                try:
                    StaffAssignment.objects.get_or_create(
                        staff=staff, flight=flight, defaults={'assignment_type': staff.role}
                    )
                    assignments += 1
                except Exception:
                    pass

        self.stdout.write(f"    Created {assignments} staff assignments.")

    def _create_shifts(self, staff_members):
        """Create shift schedules for 30 days."""
        shift_configs = [
            {'name': 'Morning Shift', 'start': '06:00', 'end': '14:00', 'min': 5, 'max': 20},
            {'name': 'Afternoon Shift', 'start': '14:00', 'end': '22:00', 'min': 5, 'max': 20},
            {'name': 'Night Shift', 'start': '22:00', 'end': '06:00', 'min': 3, 'max': 12},
        ]

        shifts = []
        for config in shift_configs:
            shift, _ = Shift.objects.get_or_create(
                name=config['name'],
                defaults={'start_time': datetime.strptime(config['start'], '%H:%M').time(),
                         'end_time': datetime.strptime(config['end'], '%H:%M').time(),
                         'min_staff': config['min'], 'max_staff': config['max'], 'is_active': True}
            )
            shifts.append(shift)

        # Create assignments for 30 days
        assignments = 0
        for day_offset in range(30):
            shift_date = (timezone.now() + timedelta(days=day_offset)).date()
            for shift in shifts:
                num_staff = random.randint(5, 12)
                assigned_staff = random.sample(staff_members, min(num_staff, len(staff_members)))

                for staff in assigned_staff:
                    StaffShiftAssignment.objects.get_or_create(
                        staff=staff, shift=shift, date=shift_date,
                        defaults={'status': StaffShiftAssignment.AssignmentStatus.SCHEDULED}
                    )
                    assignments += 1

        self.stdout.write(f"    Created {len(shifts)} shifts with {assignments} assignments.")

    def _create_extensive_fiscal_assessments(self, airports):
        """Create 6 months of fiscal assessments."""
        assessments = []
        assessment_notes = [
            "Strong performance in retail revenue due to new terminal concessions.",
            "Operational efficiency improved with new automated systems.",
            "Passenger throughput increased by 12% compared to previous period.",
            "Fuel revenue impacted by global price fluctuations.",
            "Security costs optimized through technology integration.",
            "Cargo operations showing consistent growth trajectory.",
            "Parking utilization at 85% capacity during peak hours.",
            "Ground handling services expanded to meet demand.",
        ]

        for airport in airports:
            # Monthly assessments for 6 months
            for months_ago in range(6):
                start_date = (timezone.now() - timedelta(days=30 * (months_ago + 1))).date().replace(day=1)
                if start_date.month == 12:
                    end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)

                base_revenue = Decimal(f"{random.randint(1200000, 2800000)}")
                base_expenses = Decimal(f"{random.randint(700000, 1600000)}")

                status = random.choice([AssessmentStatus.APPROVED, AssessmentStatus.COMPLETED, AssessmentStatus.COMPLETED])

                assessment, created = FiscalAssessment.objects.get_or_create(
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
                             'approved_by': 'approver' if status != AssessmentStatus.COMPLETED else 'alex',
                             'assessment_notes': random.choice(assessment_notes)}
                )

                if created or assessment.status != status.value:
                    assessment.status = status.value
                    assessment.assessed_by = 'alex'
                    assessment.approved_by = 'approver' if status != AssessmentStatus.COMPLETED else 'alex'
                    assessment.assessment_notes = random.choice(assessment_notes)
                    assessment.calculate_totals().save()

                assessments.append(assessment)

        self.stdout.write(f"    Created {len(assessments)} fiscal assessments (6 months).")
        return assessments

    def _create_reports(self, airports):
        """Create operational and financial reports."""
        reports = []
        report_types = [
            (ReportType.FISCAL_SUMMARY, "Fiscal Summary Report", "Comprehensive financial performance analysis"),
            (ReportType.OPERATIONAL, "Operational Performance Report", "Flight operations and efficiency metrics"),
            (ReportType.PASSENGER, "Passenger Analytics Report", "Passenger flow and demographic analysis"),
            (ReportType.FINANCIAL, "Financial Analysis Report", "Detailed P&L and budget variance"),
            (ReportType.PERFORMANCE, "KPI Performance Report", "Key performance indicators dashboard"),
        ]

        for airport in airports:
            for report_type, title_suffix, desc in report_types:
                title = f"{airport.code} {title_suffix} - {timezone.now().strftime('%B %Y')}"

                report, _ = Report.objects.get_or_create(
                    airport=airport, report_type=report_type.value, title=title,
                    defaults={'description': desc,
                             'period_start': (timezone.now() - timedelta(days=30)).date(),
                             'period_end': timezone.now().date(),
                             'format': ReportFormat.HTML.value, 'generated_by': 'alex',
                             'is_generated': True,
                             'generated_at': timezone.now() - timedelta(hours=random.randint(1, 24)),
                             'content': {'summary': f"This report provides comprehensive analysis for {airport.name}.",
                                        'highlights': ['Performance exceeded targets by 8%',
                                                      'Operational efficiency improved',
                                                      'Customer satisfaction at 94%'],
                                        'metrics': {'efficiency': round(random.uniform(0.85, 0.98), 2),
                                                   'on_time_performance': round(random.uniform(0.80, 0.95), 2),
                                                   'customer_satisfaction': round(random.uniform(0.88, 0.98), 2)}}}
                )
                reports.append(report)

        self.stdout.write(f"    Created {len(reports)} operational reports.")
        return reports

    def _create_documents(self, airports, assessments, reports):
        """Create documents and templates."""
        doc_count = 0

        for airport in airports:
            Document.objects.get_or_create(
                name=f"{airport.code} Facility Access Agreement 2024",
                airport=airport,
                defaults={'document_type': Document.DocumentType.AGREEMENT.value,
                         'content': {'version': '2024.1', 'effective_date': '2024-01-01',
                                    'parties': [airport.name, 'Airline Consortium']},
                         'created_by': 'alex'}
            )
            doc_count += 1

            Document.objects.get_or_create(
                name=f"{airport.code} Safety Compliance Certificate",
                airport=airport,
                defaults={'document_type': Document.DocumentType.CERTIFICATE.value,
                         'content': {'cert_number': f"CERT-{airport.code}-2024",
                                    'issue_date': '2024-01-15', 'expiry_date': '2025-01-14',
                                    'authority': 'International Aviation Safety Board', 'rating': 'A+'},
                         'created_by': 'approver'}
            )
            doc_count += 1

        for assessment in assessments[:15]:
            if assessment.status != AssessmentStatus.DRAFT.value:
                Document.objects.get_or_create(
                    name=f"Invoice INV-{assessment.id:05d}",
                    fiscal_assessment=assessment,
                    defaults={'document_type': Document.DocumentType.INVOICE.value,
                             'airport': assessment.airport,
                             'content': {'invoice_number': f"INV-{assessment.id:05d}",
                                        'date': assessment.start_date.strftime('%Y-%m-%d'),
                                        'total_amount': str(assessment.total_revenue),
                                        'status': 'Paid' if assessment.status == AssessmentStatus.APPROVED else 'Pending'},
                             'created_by': 'alex'}
                )
                doc_count += 1

        self.stdout.write(f"    Created {doc_count} documents.")

    def _create_maintenance_records(self, gates, staff_members, airports):
        """Create maintenance logs and schedules."""
        maintenance_staff = [s for s in staff_members if s.role == StaffRole.MAINTENANCE.value]
        if not maintenance_staff:
            maintenance_staff = staff_members[:5]

        logs_created = 0
        for gate in gates[:20]:
            MaintenanceLog.objects.get_or_create(
                equipment_type=MaintenanceLog.EquipmentType.GATE.value,
                equipment_id=gate.gate_id,
                description=f"Routine maintenance for {gate.gate_id}",
                defaults={'maintenance_type': MaintenanceType.ROUTINE.value,
                         'status': MaintenanceStatus.COMPLETED.value,
                         'started_at': timezone.now() - timedelta(days=random.randint(1, 60)),
                         'completed_at': timezone.now() - timedelta(days=random.randint(0, 58)),
                         'performed_by': random.choice(maintenance_staff),
                         'cost': Decimal(f"{random.randint(500, 8000)}"),
                         'notes': 'All systems checked and operational'}
            )
            logs_created += 1

        schedule_types = [
            ('Gate Systems Inspection', MaintenanceLog.EquipmentType.GATE.value, 'weekly', 'high'),
            ('Ground Equipment Service', MaintenanceLog.EquipmentType.GROUND_EQUIPMENT.value, 'weekly', 'medium'),
            ('Baggage System Check', MaintenanceLog.EquipmentType.BAGGAGE_SYSTEM.value, 'monthly', 'high'),
            ('Security Equipment Test', MaintenanceLog.EquipmentType.SECURITY_EQUIPMENT.value, 'monthly', 'medium'),
        ]

        schedules_created = 0
        for airport in airports:
            for title, equip_type, freq, priority in schedule_types:
                MaintenanceSchedule.objects.get_or_create(
                    title=title, equipment_type=equip_type,
                    equipment_id=f"{airport.code}-{equip_type.upper()[:3]}001",
                    airport=airport,
                    defaults={'maintenance_type': title,
                             'description': f"Preventive maintenance for {equip_type}",
                             'frequency': freq,
                             'last_performed': timezone.now() - timedelta(days=random.randint(1, 14)),
                             'next_due': timezone.now() + timedelta(days=random.randint(1, 30)),
                             'priority': priority,
                             'status': MaintenanceSchedule.Status.SCHEDULED.value,
                             'assigned_to': random.choice(maintenance_staff)}
                )
                schedules_created += 1

        self.stdout.write(f"    Created {logs_created} maintenance logs and {schedules_created} schedules.")

    def _create_incidents_and_events(self, flights, gates, staff_members, users):
        """Create incident reports and extensive event logs."""
        incidents_created = 0
        incident_types = [
            (IncidentType.OPERATIONAL, IncidentSeverity.LOW, "Minor operational delay"),
            (IncidentType.SAFETY, IncidentSeverity.MEDIUM, "Safety protocol observation"),
            (IncidentType.EQUIPMENT, IncidentSeverity.LOW, "Equipment malfunction reported"),
            (IncidentType.OPERATIONAL, IncidentSeverity.LOW, "Ground handling incident"),
            (IncidentType.SECURITY, IncidentSeverity.MEDIUM, "Security screening alert"),
            (IncidentType.SAFETY, IncidentSeverity.HIGH, "Runway incursion - minor"),
            (IncidentType.OPERATIONAL, IncidentSeverity.MEDIUM, "Flight delay cascade"),
        ]

        for inc_type, severity, desc in incident_types:
            IncidentReport.objects.get_or_create(
                title=f"Incident INC-{incidents_created + 1:03d}",
                defaults={'incident_type': inc_type.value, 'severity': severity.value,
                         'status': random.choice([IncidentStatus.RESOLVED.value, IncidentStatus.INVESTIGATING.value]),
                         'description': f"{desc} - Demo data for analytics",
                         'location': f"Gate {random.choice([g.gate_id for g in gates[:10]])}",
                         'reported_by': random.choice(staff_members),
                         'date_occurred': timezone.now() - timedelta(days=random.randint(1, 60)),
                         'related_flight': random.choice(flights[:50]) if flights else None,
                         'root_cause': random.choice(['Under investigation', 'Procedural error', 'Equipment failure', 'Weather']),
                         'corrective_action': random.choice(['Additional training', 'Process updated', 'Equipment replaced', 'Policy revised'])}
            )
            incidents_created += 1

        # Extensive event logs
        events_created = 0
        event_types = [
            ('FLIGHT_CREATE', 'create', 'Flight created', 'info'),
            ('FLIGHT_UPDATE', 'update', 'Flight status updated', 'info'),
            ('FLIGHT_DELAY', 'update', 'Flight delayed', 'warning'),
            ('PASSENGER_CHECKIN', 'create', 'Passenger check-in', 'info'),
            ('GATE_ASSIGNMENT', 'update', 'Gate assigned', 'info'),
            ('STAFF_ASSIGNMENT', 'create', 'Staff assigned', 'info'),
            ('BAGGAGE_LOADED', 'update', 'Baggage loaded', 'info'),
            ('MAINTENANCE_COMPLETE', 'update', 'Maintenance completed', 'info'),
            ('SECURITY_CHECK', 'view', 'Security screening', 'info'),
            ('REPORT_GENERATED', 'export', 'Report generated', 'info'),
            ('FISCAL_APPROVED', 'approve', 'Assessment approved', 'info'),
            ('SYSTEM_ERROR', 'other', 'System error occurred', 'error'),
            ('USER_LOGIN', 'login', 'User login', 'info'),
            ('USER_LOGOUT', 'logout', 'User logout', 'info'),
        ]

        admin_user = users.get('admin')
        for day_offset in range(60):
            event_date = timezone.now() - timedelta(days=day_offset)
            # 5-15 events per day
            for _ in range(random.randint(5, 15)):
                event_type, action, desc_base, severity = random.choice(event_types)
                EventLog.objects.create(
                    event_type=event_type,
                    description=f"{desc_base} - Event {events_created + 1}",
                    user=admin_user if random.random() > 0.2 else None,
                    action=action,
                    severity=severity,
                    flight=random.choice(flights[:100]) if flights and random.random() > 0.3 else None,
                    timestamp=event_date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59)),
                    ip_address=f"192.168.1.{random.randint(1, 254)}"
                )
                events_created += 1

        self.stdout.write(f"    Created {incidents_created} incidents and {events_created} event logs.")

    def _create_report_schedules(self, airports, users):
        """Create scheduled reports."""
        schedules = [
            ('Daily Operations Summary', ReportType.OPERATIONAL, 'daily'),
            ('Weekly Financial Report', ReportType.FINANCIAL, 'weekly'),
            ('Monthly Performance Review', ReportType.PERFORMANCE, 'monthly'),
            ('Weekly Passenger Analytics', ReportType.PASSENGER, 'weekly'),
        ]

        for name, report_type, freq in schedules:
            ReportSchedule.objects.get_or_create(
                name=name,
                defaults={'report_type': report_type.value, 'frequency': freq,
                         'airport': random.choice(airports),
                         'hour': random.randint(6, 10),
                         'recipients': 'management@airportsim.local, ops@airportsim.local',
                         'format': ReportFormat.PDF.value,
                         'is_active': True,
                         'created_by': users.get('admin')}
            )
