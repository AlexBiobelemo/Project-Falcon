"""Management command to populate comprehensive demo data for professional demonstration.

This command creates a complete, realistic dataset for the Airport Operations
Management System, showcasing all features and relationships.

NOTE: This script does NOT populate live API data (weather, fuel levels, etc.)
as those are dynamically fetched from external services.

Usage:
    python manage.py populate_demo_data
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
    """Command to populate the database with comprehensive demo data."""

    help = "Populate the database with realistic demo data for professional demonstration"

    def handle(self, *args, **options):
        """Execute the command."""
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("AIRPORT OPERATIONS MANAGEMENT SYSTEM"))
        self.stdout.write(self.style.SUCCESS("Professional Demo Data Population"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Check if user wants to clear existing data
        clear_data = input("Clear existing demo data first? (y/n): ").lower().strip()
        if clear_data == 'y':
            self.stdout.write("Clearing existing demo data...")
            self._clear_existing_data()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))
            self.stdout.write("")

        # 1. Setup permissions and groups
        self.stdout.write("[1/16] Setting up permissions and groups...")
        self._setup_permissions()

        # 2. Create Users with proper roles
        self.stdout.write("[2/16] Creating users with roles...")
        users = self._create_users()

        # 3. Create Airports (hub and spoke model)
        self.stdout.write("[3/16] Creating airports...")
        airports = self._create_airports()

        # 4. Create Gates with terminal organization
        self.stdout.write("[4/16] Creating gates...")
        gates = self._create_gates(airports)

        # 5. Create Staff members with diverse roles
        self.stdout.write("[5/16] Creating staff members...")
        staff_members = self._create_staff()

        # 6. Create Aircraft fleet
        self.stdout.write("[6/16] Creating aircraft fleet...")
        aircraft_list = self._create_aircraft()

        # 7. Create Crew Members
        self.stdout.write("[7/16] Creating crew members...")
        crew_members = self._create_crew(airports)

        # 8. Create Flights (realistic schedule)
        self.stdout.write("[8/16] Creating flight schedule...")
        flights = self._create_flights(airports, gates, aircraft_list)

        # 9. Create Passengers with bookings
        self.stdout.write("[9/16] Creating passengers...")
        self._create_passengers(flights)

        # 10. Create Baggage records
        self.stdout.write("[10/16] Creating baggage records...")
        self._create_baggage(flights)

        # 11. Create Staff Assignments
        self.stdout.write("[11/16] Creating staff assignments...")
        self._create_staff_assignments(flights, staff_members)

        # 12. Create Shifts and Assignments
        self.stdout.write("[12/16] Creating shift schedules...")
        self._create_shifts(staff_members)

        # 13. Create Fiscal Assessments
        self.stdout.write("[13/16] Creating fiscal assessments...")
        assessments = self._create_fiscal_assessments(airports)

        # 14. Create Reports and Documents
        self.stdout.write("[14/16] Creating reports and documents...")
        reports = self._create_reports(airports)
        self._create_documents(airports, assessments, reports)

        # 15. Create Maintenance Logs and Schedules
        self.stdout.write("[15/16] Creating maintenance records...")
        self._create_maintenance_records(gates, staff_members, airports)

        # 16. Create Incident Reports and Event Logs
        self.stdout.write("[16/16] Creating incident reports and event logs...")
        self._create_incidents_and_events(flights, gates, staff_members, users)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("DEMO DATA POPULATION COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo Credentials:"))
        self.stdout.write("  Admin:     alex / 12345")
        self.stdout.write("  Editor:    editor / 12345")
        self.stdout.write("  Approver:  approver / 12345")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Key Features Populated:"))
        self.stdout.write(f"  - {len(airports)} Airports (international hubs)")
        self.stdout.write(f"  - {len(gates)} Gates across terminals")
        self.stdout.write(f"  - {len(flights)} Flights (scheduled, departed, arrived)")
        self.stdout.write(f"  - {Passenger.objects.count()} Passengers with bookings")
        self.stdout.write(f"  - {len(staff_members)} Staff members")
        self.stdout.write(f"  - {len(crew_members)} Crew members")
        self.stdout.write(f"  - {len(aircraft_list)} Aircraft in fleet")
        self.stdout.write(f"  - {len(assessments)} Fiscal assessments")
        self.stdout.write(f"  - {len(reports)} Generated reports")
        self.stdout.write(f"  - {Document.objects.count()} Documents")
        self.stdout.write("")

    def _clear_existing_data(self):
        """Clear existing demo data (preserving users)."""
        # Delete in reverse dependency order
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
        # Keep airports and staff as they may have been customized
        self.stdout.write("  Demo data cleared (users and airports preserved).")

    def _setup_permissions(self):
        """Setup permission groups."""
        call_command('setup_permissions', verbosity=0)
        self.stdout.write("  Permission groups configured.")

    def _create_users(self):
        """Create users with different roles for demonstration."""
        users = {}

        # Superuser Admin
        admin_user, _ = User.objects.get_or_create(
            username='alex',
            defaults={
                'email': 'alex@airportsim.local',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Alexander',
                'last_name': 'Admin'
            }
        )
        admin_user.set_password('12345')
        admin_user.save()
        users['admin'] = admin_user

        # Editor User
        editor_user, _ = User.objects.get_or_create(
            username='editor',
            defaults={
                'email': 'editor@airportsim.local',
                'is_staff': True,
                'first_name': 'Emma',
                'last_name': 'Editor'
            }
        )
        editor_user.set_password('12345')
        editor_user.save()
        editors_group, _ = Group.objects.get_or_create(name='editors')
        editor_user.groups.add(editors_group)
        users['editor'] = editor_user

        # Approver User
        approver_user, _ = User.objects.get_or_create(
            username='approver',
            defaults={
                'email': 'approver@airportsim.local',
                'is_staff': True,
                'first_name': 'Andrew',
                'last_name': 'Approver'
            }
        )
        approver_user.set_password('12345')
        approver_user.save()
        approvers_group, _ = Group.objects.get_or_create(name='approvers')
        approver_user.groups.add(approvers_group)
        users['approver'] = approver_user

        # Viewer User (read-only access)
        viewer_user, _ = User.objects.get_or_create(
            username='viewer',
            defaults={
                'email': 'viewer@airportsim.local',
                'is_staff': False,
                'first_name': 'Victoria',
                'last_name': 'Viewer'
            }
        )
        viewer_user.set_password('12345')
        viewer_user.save()
        viewers_group, _ = Group.objects.get_or_create(name='viewers')
        viewer_user.groups.add(viewers_group)
        users['viewer'] = viewer_user

        # Operations Manager
        ops_user, _ = User.objects.get_or_create(
            username='operations',
            defaults={
                'email': 'operations@airportsim.local',
                'is_staff': True,
                'first_name': 'Oliver',
                'last_name': 'Operations'
            }
        )
        ops_user.set_password('12345')
        ops_user.save()
        editors_group, _ = Group.objects.get_or_create(name='editors')
        ops_user.groups.add(editors_group)
        users['operations'] = ops_user

        self.stdout.write(f"  Created {len(users)} users with various roles.")
        return users

    def _create_airports(self):
        """Create a network of international airports."""
        airport_data = [
            {
                'code': 'LOS',
                'name': "Murtala Muhammed International Airport",
                'city': 'Lagos',
                'country': 'Nigeria',
                'timezone': 'Africa/Lagos',
                'latitude': Decimal('6.5774'),
                'longitude': Decimal('3.3212'),
            },
            {
                'code': 'JFK',
                'name': "John F. Kennedy International Airport",
                'city': 'New York',
                'country': 'United States',
                'timezone': 'America/New_York',
                'latitude': Decimal('40.6413'),
                'longitude': Decimal('-73.7781'),
            },
            {
                'code': 'LHR',
                'name': "London Heathrow Airport",
                'city': 'London',
                'country': 'United Kingdom',
                'timezone': 'Europe/London',
                'latitude': Decimal('51.4700'),
                'longitude': Decimal('-0.4543'),
            },
            {
                'code': 'DXB',
                'name': "Dubai International Airport",
                'city': 'Dubai',
                'country': 'UAE',
                'timezone': 'Asia/Dubai',
                'latitude': Decimal('25.2532'),
                'longitude': Decimal('55.3657'),
            },
            {
                'code': 'SIN',
                'name': "Singapore Changi Airport",
                'city': 'Singapore',
                'country': 'Singapore',
                'timezone': 'Asia/Singapore',
                'latitude': Decimal('1.3644'),
                'longitude': Decimal('103.9915'),
            },
            {
                'code': 'FRA',
                'name': "Frankfurt Airport",
                'city': 'Frankfurt',
                'country': 'Germany',
                'timezone': 'Europe/Berlin',
                'latitude': Decimal('50.0379'),
                'longitude': Decimal('8.5622'),
            },
            {
                'code': 'NRT',
                'name': "Narita International Airport",
                'city': 'Tokyo',
                'country': 'Japan',
                'timezone': 'Asia/Tokyo',
                'latitude': Decimal('35.7720'),
                'longitude': Decimal('140.3929'),
            },
            {
                'code': 'SYD',
                'name': "Sydney Kingsford Smith Airport",
                'city': 'Sydney',
                'country': 'Australia',
                'timezone': 'Australia/Sydney',
                'latitude': Decimal('-33.9399'),
                'longitude': Decimal('151.1753'),
            },
        ]

        airports = []
        for data in airport_data:
            airport, _ = Airport.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'city': data['city'],
                    'timezone': data['timezone'],
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'is_active': True,
                }
            )
            airports.append(airport)

        self.stdout.write(f"  Created {len(airports)} international airports.")
        return airports

    def _create_gates(self, airports):
        """Create gates organized by terminals."""
        gates = []
        terminal_config = {
            'T1': {'capacity': 'regional', 'count': 4},
            'T2': {'capacity': 'narrow-body', 'count': 6},
            'T3': {'capacity': 'wide-body', 'count': 5},
        }

        for airport in airports:
            for terminal, config in terminal_config.items():
                for i in range(1, config['count'] + 1):
                    gate_id = f"{airport.code}-{terminal}{i:02d}"
                    gate, created = Gate.objects.get_or_create(
                        gate_id=gate_id,
                        defaults={
                            'terminal': terminal,
                            'capacity': config['capacity'],
                            'status': random.choice([
                                GateStatus.AVAILABLE.value,
                                GateStatus.AVAILABLE.value,
                                GateStatus.AVAILABLE.value,
                                GateStatus.OCCUPIED.value,
                                GateStatus.MAINTENANCE.value,
                            ]),
                        }
                    )
                    if created:
                        gates.append(gate)

        self.stdout.write(f"  Created {len(gates)} gates across all terminals.")
        return gates

    def _create_staff(self):
        """Create diverse staff members with various roles."""
        staff_data = [
            # Ground Crew
            {'first_name': 'Marcus', 'last_name': 'Johnson', 'role': StaffRole.GROUND_CREW.value, 'cert': 'Ground Ops Level 2'},
            {'first_name': 'Sarah', 'last_name': 'Williams', 'role': StaffRole.GROUND_CREW.value, 'cert': 'Aircraft Marshalling'},
            {'first_name': 'David', 'last_name': 'Brown', 'role': StaffRole.GROUND_CREW.value, 'cert': 'Baggage Handling'},
            {'first_name': 'Lisa', 'last_name': 'Davis', 'role': StaffRole.GROUND_CREW.value, 'cert': 'Ramp Operations'},
            # Security
            {'first_name': 'Michael', 'last_name': 'Wilson', 'role': StaffRole.SECURITY.value, 'cert': 'TSA Certified'},
            {'first_name': 'Jennifer', 'last_name': 'Martinez', 'role': StaffRole.SECURITY.value, 'cert': 'X-Ray Operator'},
            {'first_name': 'Robert', 'last_name': 'Garcia', 'role': StaffRole.SECURITY.value, 'cert': 'Security Supervisor'},
            # Maintenance
            {'first_name': 'William', 'last_name': 'Anderson', 'role': StaffRole.MAINTENANCE.value, 'cert': 'A&P License'},
            {'first_name': 'Patricia', 'last_name': 'Thomas', 'role': StaffRole.MAINTENANCE.value, 'cert': 'Avionics Specialist'},
            {'first_name': 'James', 'last_name': 'Jackson', 'role': StaffRole.MAINTENANCE.value, 'cert': 'Hydraulics Expert'},
            # Cleaning
            {'first_name': 'Mary', 'last_name': 'White', 'role': StaffRole.CLEANING.value, 'cert': 'Hazmat Handling'},
            {'first_name': 'Christopher', 'last_name': 'Harris', 'role': StaffRole.CLEANING.value, 'cert': 'Aircraft Cleaning'},
            # Pilots
            {'first_name': 'Daniel', 'last_name': 'Clark', 'role': StaffRole.PILOT.value, 'cert': 'ATP - B737'},
            {'first_name': 'Nancy', 'last_name': 'Lewis', 'role': StaffRole.PILOT.value, 'cert': 'ATP - A320'},
            {'first_name': 'Matthew', 'last_name': 'Robinson', 'role': StaffRole.PILOT.value, 'cert': 'ATP - B777'},
            # Co-Pilots
            {'first_name': 'Karen', 'last_name': 'Walker', 'role': StaffRole.CO_PILOT.value, 'cert': 'Commercial - B737'},
            {'first_name': 'Steven', 'last_name': 'Hall', 'role': StaffRole.CO_PILOT.value, 'cert': 'Commercial - A320'},
            # Cabin Crew
            {'first_name': 'Betty', 'last_name': 'Allen', 'role': StaffRole.CABIN_CREW.value, 'cert': 'Flight Attendant'},
            {'first_name': 'Edward', 'last_name': 'Young', 'role': StaffRole.CABIN_CREW.value, 'cert': 'Lead Attendant'},
            {'first_name': 'Helen', 'last_name': 'King', 'role': StaffRole.CABIN_CREW.value, 'cert': 'Purser Certified'},
            {'first_name': 'Brian', 'last_name': 'Wright', 'role': StaffRole.CABIN_CREW.value, 'cert': 'Safety Officer'},
            {'first_name': 'Sandra', 'last_name': 'Scott', 'role': StaffRole.CABIN_CREW.value, 'cert': 'First Class Service'},
        ]

        staff_members = []
        for i, data in enumerate(staff_data, start=1):
            staff, _ = Staff.objects.get_or_create(
                employee_number=f"EMP{i:04d}",
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'role': data['role'],
                    'certification': data.get('cert', ''),
                    'is_available': True,
                    'email': f"{data['first_name'].lower()}.{data['last_name'].lower()}@airportsim.local",
                    'phone': f"+234-800-{i:04d}",
                }
            )
            staff_members.append(staff)

        self.stdout.write(f"  Created {len(staff_members)} staff members across all roles.")
        return staff_members

    def _create_aircraft(self):
        """Create a diverse aircraft fleet."""
        aircraft_data = [
            {'tail': 'N101AF', 'type': AircraftType.NARROW_BODY, 'mfr': 'Boeing', 'model': '737-800', 'pax': 162, 'cargo': 4400},
            {'tail': 'N102AF', 'type': AircraftType.NARROW_BODY, 'mfr': 'Boeing', 'model': '737 MAX 8', 'pax': 172, 'cargo': 4500},
            {'tail': 'N103AF', 'type': AircraftType.NARROW_BODY, 'mfr': 'Airbus', 'model': 'A320neo', 'pax': 165, 'cargo': 4200},
            {'tail': 'N104AF', 'type': AircraftType.NARROW_BODY, 'mfr': 'Airbus', 'model': 'A321neo', 'pax': 194, 'cargo': 4800},
            {'tail': 'N201AF', 'type': AircraftType.WIDE_BODY, 'mfr': 'Boeing', 'model': '777-300ER', 'pax': 350, 'cargo': 20000},
            {'tail': 'N202AF', 'type': AircraftType.WIDE_BODY, 'mfr': 'Boeing', 'model': '787-9', 'pax': 290, 'cargo': 17000},
            {'tail': 'N203AF', 'type': AircraftType.WIDE_BODY, 'mfr': 'Airbus', 'model': 'A350-900', 'pax': 315, 'cargo': 18000},
            {'tail': 'N204AF', 'type': AircraftType.WIDE_BODY, 'mfr': 'Airbus', 'model': 'A330-300', 'pax': 277, 'cargo': 15000},
            {'tail': 'N301AF', 'type': AircraftType.REGIONAL, 'mfr': 'Embraer', 'model': 'E195-E2', 'pax': 146, 'cargo': 3500},
            {'tail': 'N302AF', 'type': AircraftType.REGIONAL, 'mfr': 'Embraer', 'model': 'E175', 'pax': 88, 'cargo': 2500},
            {'tail': 'N303AF', 'type': AircraftType.REGIONAL, 'mfr': 'Bombardier', 'model': 'CRJ900', 'pax': 90, 'cargo': 2800},
            {'tail': 'N401AF', 'type': AircraftType.CARGO, 'mfr': 'Boeing', 'model': '747-8F', 'pax': 0, 'cargo': 140000},
            {'tail': 'N402AF', 'type': AircraftType.CARGO, 'mfr': 'Boeing', 'model': '767-300F', 'pax': 0, 'cargo': 52000},
        ]

        aircraft_list = []
        for data in aircraft_data:
            aircraft, _ = Aircraft.objects.get_or_create(
                tail_number=data['tail'],
                defaults={
                    'aircraft_type': data['type'].value,
                    'model': data['model'],
                    'manufacturer': data['mfr'],
                    'capacity_passengers': data['pax'],
                    'capacity_cargo': Decimal(data['cargo']),
                    'status': AircraftStatus.ACTIVE.value,
                    'registration_country': 'USA',
                    'year_manufactured': random.randint(2015, 2024),
                    'total_flight_hours': Decimal(random.randint(500, 15000)),
                }
            )
            aircraft_list.append(aircraft)

        self.stdout.write(f"  Created {len(aircraft_list)} aircraft in fleet.")
        return aircraft_list

    def _create_crew(self, airports):
        """Create crew members for flight operations."""
        crew_data = [
            # Pilots
            {'first': 'Captain John', 'last': 'Peterson', 'type': CrewMemberType.PILOT, 'rank': 'Captain', 'hours': 12000},
            {'first': 'Captain Maria', 'last': 'Rodriguez', 'type': CrewMemberType.PILOT, 'rank': 'Captain', 'hours': 10500},
            {'first': 'Captain Ahmed', 'last': 'Hassan', 'type': CrewMemberType.PILOT, 'rank': 'Senior Captain', 'hours': 15000},
            {'first': 'Captain Yuki', 'last': 'Tanaka', 'type': CrewMemberType.PILOT, 'rank': 'Captain', 'hours': 9800},
            # First Officers
            {'first': 'FO Michael', 'last': 'Chen', 'type': CrewMemberType.FIRST_OFFICER, 'rank': 'First Officer', 'hours': 4500},
            {'first': 'FO Sophie', 'last': 'Mueller', 'type': CrewMemberType.FIRST_OFFICER, 'rank': 'First Officer', 'hours': 3800},
            {'first': 'FO David', 'last': 'Okonkwo', 'type': CrewMemberType.FIRST_OFFICER, 'rank': 'Senior FO', 'hours': 6200},
            # Flight Attendants
            {'first': 'FA Emily', 'last': 'Thompson', 'type': CrewMemberType.FLIGHT_ATTENDANT, 'rank': 'Flight Attendant', 'hours': 5000},
            {'first': 'FA Carlos', 'last': 'Silva', 'type': CrewMemberType.FLIGHT_ATTENDANT, 'rank': 'Flight Attendant', 'hours': 4200},
            {'first': 'FA Aisha', 'last': 'Mohammed', 'type': CrewMemberType.FLIGHT_ATTENDANT, 'rank': 'Flight Attendant', 'hours': 3500},
            {'first': 'FA James', 'last': 'O\'Brien', 'type': CrewMemberType.FLIGHT_ATTENDANT, 'rank': 'Flight Attendant', 'hours': 2800},
            # Lead Flight Attendants
            {'first': 'LFA Rachel', 'last': 'Kim', 'type': CrewMemberType.LEAD_FATTENDANT, 'rank': 'Lead FA', 'hours': 8500},
            {'first': 'LFA Thomas', 'last': 'Anderson', 'type': CrewMemberType.LEAD_FATTENDANT, 'rank': 'Purser', 'hours': 9200},
        ]

        crew_members = []
        for i, data in enumerate(crew_data, start=1):
            crew, _ = CrewMember.objects.get_or_create(
                employee_id=f"CREW{i:04d}",
                defaults={
                    'first_name': data['first'],
                    'last_name': data['last'],
                    'crew_type': data['type'].value,
                    'license_number': f"LIC-{i:05d}-FAA",
                    'license_expiry': timezone.now().date() + timedelta(days=random.randint(180, 730)),
                    'status': CrewMemberStatus.AVAILABLE.value,
                    'total_flight_hours': Decimal(data['hours']),
                    'rank': data['rank'],
                    'base_airport': random.choice(airports),
                    'email': f"crew{i}@airportsim.local",
                    'hire_date': timezone.now().date() - timedelta(days=random.randint(365, 2500)),
                }
            )
            crew_members.append(crew)

        self.stdout.write(f"  Created {len(crew_members)} crew members.")
        return crew_members

    def _create_flights(self, airports, gates, aircraft_list):
        """Create a realistic flight schedule."""
        airlines = [
            ('Delta Air Lines', 'DL'),
            ('United Airlines', 'UA'),
            ('British Airways', 'BA'),
            ('Emirates', 'EK'),
            ('Lufthansa', 'LH'),
            ('Air Peace', 'P4'),
            ('Singapore Airlines', 'SQ'),
            ('Qatar Airways', 'QR'),
        ]

        aircraft_types = ['B737', 'B777', 'A320', 'A350', 'E195']

        flights = []
        now = timezone.now()

        # Create flights for different time periods
        flight_configs = [
            # Departed flights (past)
            {'prefix': 'DL', 'num': 101, 'origin_idx': 0, 'dest_idx': 1, 'days_ago': 1, 'status': FlightStatus.DEPARTED},
            {'prefix': 'BA', 'num': 202, 'origin_idx': 1, 'dest_idx': 2, 'days_ago': 1, 'status': FlightStatus.DEPARTED},
            {'prefix': 'EK', 'num': 303, 'origin_idx': 2, 'dest_idx': 3, 'days_ago': 2, 'status': FlightStatus.ARRIVED},
            {'prefix': 'LH', 'num': 404, 'origin_idx': 3, 'dest_idx': 4, 'days_ago': 2, 'status': FlightStatus.ARRIVED},
            # Boarding flights (current)
            {'prefix': 'P4', 'num': 505, 'origin_idx': 4, 'dest_idx': 0, 'days_ago': 0, 'status': FlightStatus.BOARDING},
            {'prefix': 'SQ', 'num': 606, 'origin_idx': 0, 'dest_idx': 5, 'days_ago': 0, 'status': FlightStatus.BOARDING},
            # Scheduled flights (upcoming)
            {'prefix': 'QR', 'num': 707, 'origin_idx': 5, 'dest_idx': 6, 'days_ago': 0, 'hours_ahead': 2, 'status': FlightStatus.SCHEDULED},
            {'prefix': 'DL', 'num': 808, 'origin_idx': 6, 'dest_idx': 7, 'days_ago': 0, 'hours_ahead': 4, 'status': FlightStatus.SCHEDULED},
            {'prefix': 'UA', 'num': 909, 'origin_idx': 7, 'dest_idx': 0, 'days_ago': 0, 'hours_ahead': 6, 'status': FlightStatus.SCHEDULED},
            {'prefix': 'BA', 'num': 110, 'origin_idx': 0, 'dest_idx': 2, 'days_ago': 0, 'hours_ahead': 8, 'status': FlightStatus.SCHEDULED},
            # Delayed flights
            {'prefix': 'EK', 'num': 220, 'origin_idx': 1, 'dest_idx': 3, 'days_ago': 0, 'hours_ahead': 3, 'status': FlightStatus.DELAYED, 'delay': 45},
            {'prefix': 'LH', 'num': 330, 'origin_idx': 2, 'dest_idx': 5, 'days_ago': 0, 'hours_ahead': 5, 'status': FlightStatus.DELAYED, 'delay': 90},
            # Future scheduled
            {'prefix': 'P4', 'num': 440, 'origin_idx': 0, 'dest_idx': 1, 'days_ahead': 1, 'status': FlightStatus.SCHEDULED},
            {'prefix': 'SQ', 'num': 550, 'origin_idx': 4, 'dest_idx': 6, 'days_ahead': 1, 'status': FlightStatus.SCHEDULED},
            {'prefix': 'QR', 'num': 660, 'origin_idx': 3, 'dest_idx': 7, 'days_ahead': 2, 'status': FlightStatus.SCHEDULED},
            {'prefix': 'DL', 'num': 770, 'origin_idx': 5, 'dest_idx': 0, 'days_ahead': 2, 'status': FlightStatus.SCHEDULED},
            {'prefix': 'UA', 'num': 880, 'origin_idx': 6, 'dest_idx': 1, 'days_ahead': 3, 'status': FlightStatus.SCHEDULED},
            # Cancelled flight
            {'prefix': 'BA', 'num': 990, 'origin_idx': 7, 'dest_idx': 2, 'days_ahead': 1, 'status': FlightStatus.CANCELLED},
        ]

        for config in flight_configs:
            flight_number = f"{config['prefix']}{config['num']}"
            origin = airports[config['origin_idx']]
            destination = airports[config['dest_idx']]

            # Calculate times
            if 'days_ago' in config:
                scheduled_departure = now - timedelta(days=config['days_ago'])
            elif 'hours_ahead' in config:
                scheduled_departure = now + timedelta(hours=config['hours_ahead'])
            elif 'days_ahead' in config:
                scheduled_departure = now + timedelta(days=config['days_ahead'])
            else:
                scheduled_departure = now + timedelta(hours=2)

            # Flight duration based on distance (simplified)
            flight_duration = timedelta(hours=random.randint(2, 14))
            scheduled_arrival = scheduled_departure + flight_duration

            # Select gate at origin airport
            origin_gates = [g for g in gates if g.gate_id.startswith(origin.code)]
            gate = random.choice(origin_gates) if origin_gates else None

            # Get airline info
            airline_info = next((a for a in airlines if a[1] == config['prefix']), ('Unknown', config['prefix']))

            flight, _ = Flight.objects.get_or_create(
                flight_number=flight_number,
                defaults={
                    'airline': airline_info[0],
                    'origin': origin.code,
                    'destination': destination.code,
                    'scheduled_departure': scheduled_departure,
                    'scheduled_arrival': scheduled_arrival,
                    'gate': gate,
                    'status': config['status'].value,
                    'delay_minutes': config.get('delay', 0),
                    'aircraft_type': random.choice(aircraft_types),
                }
            )

            # Update actual times for departed/arrived flights
            if config['status'] == FlightStatus.DEPARTED:
                flight.actual_departure = scheduled_departure + timedelta(minutes=random.randint(0, 30))
                flight.save()
            elif config['status'] == FlightStatus.ARRIVED:
                flight.actual_departure = scheduled_departure
                flight.actual_arrival = scheduled_arrival
                flight.save()

            flights.append(flight)

        self.stdout.write(f"  Created {len(flights)} flights with various statuses.")
        return flights

    def _create_passengers(self, flights):
        """Create passengers booked on flights."""
        first_names = [
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
            'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
            'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Lisa',
            'Matthew', 'Betty', 'Anthony', 'Margaret', 'Mark', 'Sandra', 'Donald', 'Ashley',
            'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
        ]

        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
            'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
            'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
        ]

        passenger_count = 0
        statuses = [
            PassengerStatus.CHECKED_IN,
            PassengerStatus.CHECKED_IN,
            PassengerStatus.CHECKED_IN,
            PassengerStatus.BOARDED,
            PassengerStatus.BOARDED,
            PassengerStatus.ARRIVED,
        ]

        for flight in flights:
            # Create 8-15 passengers per flight
            num_passengers = random.randint(8, 15)
            for i in range(num_passengers):
                passport = f"P{flight.id:04d}{i:04d}"
                status = random.choice(statuses) if flight.status not in [FlightStatus.SCHEDULED] else PassengerStatus.CHECKED_IN

                Passenger.objects.get_or_create(
                    passport_number=passport,
                    defaults={
                        'first_name': random.choice(first_names),
                        'last_name': random.choice(last_names),
                        'email': f"passenger{passport}@example.com",
                        'phone': f"+1-555-{random.randint(1000, 9999)}",
                        'flight': flight,
                        'seat_number': f"{random.randint(1, 35)}{random.choice('ABCDEF')}",
                        'status': status.value,
                        'checked_bags': random.randint(0, 3),
                    }
                )
                passenger_count += 1

        self.stdout.write(f"  Created {passenger_count} passenger bookings.")

    def _create_baggage(self, flights):
        """Create baggage records for passengers."""
        baggage_count = 0
        statuses = [
            Baggage.BaggageStatus.CHECKED_IN,
            Baggage.BaggageStatus.CHECKED_IN,
            Baggage.BaggageStatus.SCREENED,
            Baggage.BaggageStatus.SORTED,
            Baggage.BaggageStatus.LOADED,
        ]

        for flight in flights:
            passengers = flight.passengers.all()
            for passenger in passengers:
                if passenger.checked_bags > 0:
                    for bag_num in range(passenger.checked_bags):
                        tag = f"{flight.flight_number.replace(' ', '')}{bag_num + 1:03d}{passenger.passenger_id.hex[:4].upper()}"
                        status = random.choice(statuses) if flight.status not in [FlightStatus.ARRIVED] else Baggage.BaggageStatus.CLAIMED

                        Baggage.objects.get_or_create(
                            tag_number=tag[:20],  # Truncate to max length
                            defaults={
                                'passenger': passenger,
                                'flight': flight,
                                'status': status.value,
                                'origin': flight.origin,
                                'destination': flight.destination,
                                'weight': Decimal(f"{random.randint(15, 32)}.{random.randint(0, 9)}"),
                                'pieces': 1,
                                'location': f"Terminal {random.choice(['1', '2', '3'])}, Belt {random.randint(1, 12)}",
                            }
                        )
                        baggage_count += 1

        self.stdout.write(f"  Created {baggage_count} baggage records.")

    def _create_staff_assignments(self, flights, staff_members):
        """Assign staff to flights."""
        assignments = 0
        roles_for_assignment = [
            StaffRole.GROUND_CREW.value,
            StaffRole.SECURITY.value,
            StaffRole.CLEANING.value,
        ]

        for flight in flights:
            # Assign 2-4 staff per flight
            num_assignments = random.randint(2, 4)
            assigned_staff = random.sample(
                [s for s in staff_members if s.role in roles_for_assignment],
                min(num_assignments, len([s for s in staff_members if s.role in roles_for_assignment]))
            )

            for staff in assigned_staff:
                try:
                    StaffAssignment.objects.get_or_create(
                        staff=staff,
                        flight=flight,
                        defaults={'assignment_type': staff.role}
                    )
                    assignments += 1
                except Exception:
                    pass  # Skip duplicate assignments

        self.stdout.write(f"  Created {assignments} staff assignments.")

    def _create_shifts(self, staff_members):
        """Create shift schedules and assignments."""
        shift_configs = [
            {'name': 'Morning Shift', 'start': '06:00', 'end': '14:00', 'min': 5, 'max': 15},
            {'name': 'Afternoon Shift', 'start': '14:00', 'end': '22:00', 'min': 5, 'max': 15},
            {'name': 'Night Shift', 'start': '22:00', 'end': '06:00', 'min': 3, 'max': 10},
        ]

        shifts = []
        for config in shift_configs:
            shift, _ = Shift.objects.get_or_create(
                name=config['name'],
                defaults={
                    'start_time': datetime.strptime(config['start'], '%H:%M').time(),
                    'end_time': datetime.strptime(config['end'], '%H:%M').time(),
                    'min_staff': config['min'],
                    'max_staff': config['max'],
                    'is_active': True,
                }
            )
            shifts.append(shift)

        # Create shift assignments for the next 7 days
        assignments = 0
        for day_offset in range(7):
            shift_date = (timezone.now() + timedelta(days=day_offset)).date()
            for shift in shifts:
                # Assign 3-8 staff per shift
                num_staff = random.randint(3, 8)
                assigned_staff = random.sample(staff_members, min(num_staff, len(staff_members)))

                for staff in assigned_staff:
                    StaffShiftAssignment.objects.get_or_create(
                        staff=staff,
                        shift=shift,
                        date=shift_date,
                        defaults={
                            'status': StaffShiftAssignment.AssignmentStatus.SCHEDULED,
                        }
                    )
                    assignments += 1

        self.stdout.write(f"  Created {len(shifts)} shifts with {assignments} assignments.")

    def _create_fiscal_assessments(self, airports):
        """Create comprehensive fiscal assessments."""
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
            # Create monthly assessments for past 3 months
            for months_ago in range(3):
                start_date = (timezone.now() - timedelta(days=30 * (months_ago + 1))).date().replace(day=1)
                # Calculate end of month
                if start_date.month == 12:
                    end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)

                # Generate realistic financial data
                base_revenue = Decimal(f"{random.randint(1200000, 2500000)}")
                base_expenses = Decimal(f"{random.randint(700000, 1400000)}")

                status = random.choice([
                    AssessmentStatus.APPROVED,
                    AssessmentStatus.COMPLETED,
                    AssessmentStatus.COMPLETED,
                ])

                assessment, created = FiscalAssessment.objects.get_or_create(
                    airport=airport,
                    period_type=AssessmentPeriod.MONTHLY.value,
                    start_date=start_date,
                    end_date=end_date,
                    defaults={
                        'status': status.value,
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
                        'passenger_count': random.randint(80000, 200000),
                        'flight_count': random.randint(1500, 3500),
                        'assessed_by': 'alex',
                        'approved_by': 'approver' if status != AssessmentStatus.COMPLETED else 'alex',
                        'assessment_notes': random.choice(assessment_notes),
                    }
                )
                
                if created or assessment.status != status.value:
                    assessment.status = status.value
                    assessment.assessed_by = 'alex'
                    assessment.approved_by = 'approver' if status != AssessmentStatus.COMPLETED else 'alex'
                    assessment.assessment_notes = random.choice(assessment_notes)
                    assessment.calculate_totals().save()
                
                assessments.append(assessment)

        self.stdout.write(f"  Created/updated {len(assessments)} fiscal assessments.")
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
                    airport=airport,
                    report_type=report_type.value,
                    title=title,
                    defaults={
                        'description': desc,
                        'period_start': (timezone.now() - timedelta(days=30)).date(),
                        'period_end': timezone.now().date(),
                        'format': ReportFormat.HTML.value,
                        'generated_by': 'alex',
                        'is_generated': True,
                        'generated_at': timezone.now() - timedelta(hours=random.randint(1, 24)),
                        'content': {
                            'summary': f"This report provides comprehensive analysis for {airport.name}.",
                            'highlights': [
                                'Performance exceeded targets by 8%',
                                'Operational efficiency improved',
                                'Customer satisfaction at 94%'
                            ],
                            'metrics': {
                                'efficiency': round(random.uniform(0.85, 0.98), 2),
                                'on_time_performance': round(random.uniform(0.80, 0.95), 2),
                                'customer_satisfaction': round(random.uniform(0.88, 0.98), 2),
                            }
                        }
                    }
                )
                reports.append(report)

        self.stdout.write(f"  Created {len(reports)} operational reports.")
        return reports

    def _create_documents(self, airports, assessments, reports):
        """Create documents and templates."""
        doc_count = 0

        # Facility agreements for each airport
        for airport in airports:
            Document.objects.get_or_create(
                name=f"{airport.code} Facility Access Agreement 2024",
                airport=airport,
                defaults={
                    'document_type': Document.DocumentType.AGREEMENT.value,
                    'content': {
                        'version': '2024.1',
                        'effective_date': '2024-01-01',
                        'parties': [airport.name, 'Airline Consortium'],
                        'terms': 'Standard facility access terms and conditions'
                    },
                    'created_by': 'alex',
                }
            )
            doc_count += 1

            # Safety certificates
            Document.objects.get_or_create(
                name=f"{airport.code} Safety Compliance Certificate",
                airport=airport,
                defaults={
                    'document_type': Document.DocumentType.CERTIFICATE.value,
                    'content': {
                        'cert_number': f"CERT-{airport.code}-2024",
                        'issue_date': '2024-01-15',
                        'expiry_date': '2025-01-14',
                        'authority': 'International Aviation Safety Board',
                        'rating': 'A+'
                    },
                    'created_by': 'approver',
                }
            )
            doc_count += 1

        # Invoices for assessments
        for assessment in assessments[:10]:
            if assessment.status != AssessmentStatus.DRAFT.value:
                Document.objects.get_or_create(
                    name=f"Invoice INV-{assessment.id:05d}",
                    fiscal_assessment=assessment,
                    defaults={
                        'document_type': Document.DocumentType.INVOICE.value,
                        'airport': assessment.airport,
                        'content': {
                            'invoice_number': f"INV-{assessment.id:05d}",
                            'date': assessment.start_date.strftime('%Y-%m-%d'),
                            'total_amount': str(assessment.total_revenue),
                            'status': 'Paid' if assessment.status == AssessmentStatus.APPROVED else 'Pending'
                        },
                        'created_by': 'alex',
                    }
                )
                doc_count += 1

        # Report documents
        for report in reports[:5]:
            Document.objects.get_or_create(
                name=f"Report Doc - {report.title[:30]}",
                report=report,
                defaults={
                    'document_type': Document.DocumentType.REPORT.value,
                    'airport': report.airport,
                    'content': report.content,
                    'created_by': report.generated_by,
                }
            )
            doc_count += 1

        self.stdout.write(f"  Created {doc_count} documents.")

    def _create_maintenance_records(self, gates, staff_members, airports):
        """Create maintenance logs and schedules."""
        maintenance_staff = [s for s in staff_members if s.role == StaffRole.MAINTENANCE.value]
        if not maintenance_staff:
            maintenance_staff = staff_members[:5]

        logs_created = 0
        schedules_created = 0

        # Maintenance logs for gates
        for gate in gates[:15]:
            MaintenanceLog.objects.get_or_create(
                equipment_type=MaintenanceLog.EquipmentType.GATE.value,
                equipment_id=gate.gate_id,
                description=f"Routine maintenance for {gate.gate_id}",
                defaults={
                    'maintenance_type': MaintenanceType.ROUTINE.value,
                    'status': MaintenanceStatus.COMPLETED.value,
                    'started_at': timezone.now() - timedelta(days=random.randint(1, 30)),
                    'completed_at': timezone.now() - timedelta(days=random.randint(0, 28)),
                    'performed_by': random.choice(maintenance_staff),
                    'cost': Decimal(f"{random.randint(500, 5000)}"),
                    'notes': 'All systems checked and operational'
                }
            )
            logs_created += 1

        # Maintenance schedules - using valid EquipmentType values
        schedule_types = [
            ('Gate Systems Inspection', MaintenanceLog.EquipmentType.GATE.value, 'weekly', 'High'),
            ('Ground Equipment Service', MaintenanceLog.EquipmentType.GROUND_EQUIPMENT.value, 'weekly', 'Medium'),
            ('Baggage System Check', MaintenanceLog.EquipmentType.BAGGAGE_SYSTEM.value, 'monthly', 'High'),
            ('Security Equipment Test', MaintenanceLog.EquipmentType.SECURITY_EQUIPMENT.value, 'monthly', 'Medium'),
        ]

        for airport in airports:
            for title, equip_type, freq, priority in schedule_types:
                # Use MaintenanceSchedule's EquipmentType choices
                maint_equip_type = equip_type  # Already a string value
                MaintenanceSchedule.objects.get_or_create(
                    title=title,
                    equipment_type=maint_equip_type,
                    equipment_id=f"{airport.code}-{equip_type.upper()[:3]}001",
                    airport=airport,
                    defaults={
                        'maintenance_type': title,
                        'description': f"Preventive maintenance for {equip_type}",
                        'frequency': freq,
                        'last_performed': timezone.now() - timedelta(days=random.randint(1, 14)),
                        'next_due': timezone.now() + timedelta(days=random.randint(1, 30)),
                        'priority': priority.lower(),
                        'status': MaintenanceSchedule.Status.SCHEDULED.value,
                        'assigned_to': random.choice(maintenance_staff),
                    }
                )
                schedules_created += 1

        self.stdout.write(f"  Created {logs_created} maintenance logs and {schedules_created} schedules.")

    def _create_incidents_and_events(self, flights, gates, staff_members, users):
        """Create incident reports and event logs."""
        incidents_created = 0
        events_created = 0

        # Incident reports
        incident_types = [
            (IncidentType.OPERATIONAL, IncidentSeverity.LOW, "Minor operational delay"),
            (IncidentType.SAFETY, IncidentSeverity.MEDIUM, "Safety protocol observation"),
            (IncidentType.EQUIPMENT, IncidentSeverity.LOW, "Equipment malfunction reported"),
            (IncidentType.OPERATIONAL, IncidentSeverity.LOW, "Ground handling incident"),
            (IncidentType.SECURITY, IncidentSeverity.MEDIUM, "Security screening alert"),
        ]

        for inc_type, severity, desc in incident_types:
            IncidentReport.objects.get_or_create(
                title=f"Incident INC-{incidents_created + 1:03d}",
                defaults={
                    'incident_type': inc_type.value,
                    'severity': severity.value,
                    'status': random.choice([IncidentStatus.RESOLVED.value, IncidentStatus.INVESTIGATING.value]),
                    'description': f"{desc} - Automated demo data",
                    'location': f"Gate {random.choice([g.gate_id for g in gates[:10]])}",
                    'reported_by': random.choice(staff_members),
                    'date_occurred': timezone.now() - timedelta(days=random.randint(1, 14)),
                    'related_flight': random.choice(flights) if flights else None,
                    'root_cause': 'Under investigation' if random.random() > 0.5 else 'Procedural error',
                    'corrective_action': 'Additional training scheduled' if random.random() > 0.5 else 'Process updated',
                }
            )
            incidents_created += 1

        # Event logs
        event_types = [
            ('FLIGHT_CREATE', 'create', 'Flight created in system'),
            ('FLIGHT_UPDATE', 'update', 'Flight status updated'),
            ('PASSENGER_CHECKIN', 'create', 'Passenger check-in completed'),
            ('GATE_ASSIGNMENT', 'update', 'Gate assigned to flight'),
            ('STAFF_ASSIGNMENT', 'create', 'Staff assigned to flight'),
            ('BAGGAGE_LOADED', 'update', 'Baggage loaded onto aircraft'),
            ('MAINTENANCE_COMPLETE', 'update', 'Maintenance task completed'),
            ('SECURITY_CHECK', 'view', 'Security screening completed'),
            ('REPORT_GENERATED', 'export', 'Operational report generated'),
            ('FISCAL_APPROVED', 'approve', 'Fiscal assessment approved'),
        ]

        admin_user = users.get('admin')
        for event_type, action, desc_base in event_types:
            for i in range(3):
                EventLog.objects.create(
                    event_type=event_type,
                    description=f"{desc_base} - Demo Event {events_created + 1}",
                    user=admin_user,
                    action=action,
                    severity=random.choice(['info', 'info', 'info', 'warning']),
                    flight=random.choice(flights) if flights and random.random() > 0.3 else None,
                    timestamp=timezone.now() - timedelta(hours=random.randint(1, 168)),
                    ip_address=f"192.168.1.{random.randint(1, 254)}"
                )
                events_created += 1

        self.stdout.write(f"  Created {incidents_created} incidents and {events_created} event logs.")
