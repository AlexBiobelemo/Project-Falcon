"""Comprehensive unit and integration tests for the Airport Operations Management System.

This module contains tests for:
- Core models (Airport, Gate, Flight, Passenger, Staff, StaffAssignment, EventLog)
- API endpoints (ViewSets)
- Dashboard and metrics endpoints
- Integration scenarios
"""

import json
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User, Group
from django.test import TestCase, Client
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.models import (
    Airport,
    AssessmentPeriod,
    AssessmentStatus,
    Document,
    EventLog,
    FiscalAssessment,
    Flight,
    FlightStatus,
    Gate,
    GateStatus,
    Passenger,
    PassengerStatus,
    Report,
    ReportFormat,
    ReportType,
    Staff,
    StaffAssignment,
    StaffRole,
)


class AirportModelTest(TestCase):
    """Tests for the Airport model."""
    
    def setUp(self):
        """Set up test data."""
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
            timezone="Africa/Lagos",
            is_active=True,
        )
    
    def test_airport_creation(self):
        """Test airport is created correctly."""
        self.assertEqual(self.airport.code, "LOS")
        self.assertEqual(self.airport.name, "Lagos International Airport")
        self.assertTrue(self.airport.is_active)
        self.assertEqual(self.airport.timezone, "Africa/Lagos")
    
    def test_airport_str(self):
        """Test airport string representation."""
        self.assertEqual(str(self.airport), "LOS - Lagos International Airport")
    
    def test_airport_inactive_default(self):
        """Test airport is_active defaults to True."""
        new_airport = Airport.objects.create(
            code="ABJ",
            name="Abuja International Airport",
            city="Abuja",
        )
        self.assertTrue(new_airport.is_active)


class GateModelTest(TestCase):
    """Tests for the Gate model."""
    
    def setUp(self):
        """Set up test data."""
        self.gate = Gate.objects.create(
            gate_id="A1",
            terminal="Terminal 1",
            capacity="wide-body",
            status=GateStatus.AVAILABLE.value,
        )
    
    def test_gate_creation(self):
        """Test gate is created correctly."""
        self.assertEqual(self.gate.gate_id, "A1")
        self.assertEqual(self.gate.terminal, "Terminal 1")
        self.assertEqual(self.gate.capacity, "wide-body")
        self.assertEqual(self.gate.status, GateStatus.AVAILABLE.value)
    
    def test_gate_str(self):
        """Test gate string representation."""
        self.assertEqual(str(self.gate), "A1 (Terminal 1)")
    
    def test_gate_status_default(self):
        """Test gate status defaults to available."""
        new_gate = Gate.objects.create(
            gate_id="B2",
            terminal="Terminal 2",
        )
        self.assertEqual(new_gate.status, GateStatus.AVAILABLE.value)
    
    def test_gate_manager_available(self):
        """Test GateManager.available() returns available gates."""
        Gate.objects.create(gate_id="C1", terminal="Terminal 1", status=GateStatus.AVAILABLE.value)
        Gate.objects.create(gate_id="C2", terminal="Terminal 1", status=GateStatus.OCCUPIED.value)
        
        available = Gate.objects.available()
        self.assertEqual(available.count(), 2)  # Including the one from setUp
    
    def test_gate_manager_by_status(self):
        """Test GateManager.by_status() filters by status."""
        Gate.objects.create(gate_id="D1", terminal="Terminal 1", status=GateStatus.MAINTENANCE.value)
        
        maintenance_gates = Gate.objects.by_status(GateStatus.MAINTENANCE.value)
        self.assertEqual(maintenance_gates.count(), 1)


class FlightModelTest(TestCase):
    """Tests for the Flight model."""
    
    def setUp(self):
        """Set up test data."""
        self.gate = Gate.objects.create(
            gate_id="A1",
            terminal="Terminal 1",
            status=GateStatus.AVAILABLE.value,
        )
        
        now = timezone.now()
        self.flight = Flight.objects.create(
            flight_number="AA123",
            airline="American Airlines",
            origin="LOS",
            destination="JFK",
            scheduled_departure=now + timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=10),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
            aircraft_type="Boeing 737",
        )
    
    def test_flight_creation(self):
        """Test flight is created correctly."""
        self.assertEqual(self.flight.flight_number, "AA123")
        self.assertEqual(self.flight.airline, "American Airlines")
        self.assertEqual(self.flight.origin, "LOS")
        self.assertEqual(self.flight.destination, "JFK")
        self.assertEqual(self.flight.status, FlightStatus.SCHEDULED.value)
    
    def test_flight_str(self):
        """Test flight string representation."""
        self.assertEqual(str(self.flight), "AA123 (LOS → JFK)")
    
    def test_flight_manager_upcoming(self):
        """Test FlightManager.upcoming() returns scheduled flights."""
        now = timezone.now()
        
        # Create a flight in the past (should not be in upcoming)
        Flight.objects.create(
            flight_number="BB456",
            origin="LOS",
            destination="ABJ",
            scheduled_departure=now - timedelta(hours=2),
            scheduled_arrival=now - timedelta(hours=1),
            status=FlightStatus.SCHEDULED.value,
        )
        
        upcoming = Flight.objects.upcoming()
        self.assertEqual(upcoming.count(), 1)
    
    def test_flight_manager_delayed(self):
        """Test FlightManager.delayed() returns delayed flights."""
        Flight.objects.create(
            flight_number="CC789",
            origin="LOS",
            destination="ABJ",
            scheduled_departure=timezone.now() + timedelta(hours=1),
            scheduled_arrival=timezone.now() + timedelta(hours=2),
            status=FlightStatus.DELAYED.value,
        )
        
        delayed = Flight.objects.delayed()
        self.assertEqual(delayed.count(), 1)
    
    def test_flight_gate_relationship(self):
        """Test flight can access its assigned gate."""
        self.assertEqual(self.flight.gate.gate_id, "A1")


class PassengerModelTest(TestCase):
    """Tests for the Passenger model."""
    
    def setUp(self):
        """Set up test data."""
        self.flight = Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            status=FlightStatus.SCHEDULED.value,
        )
        
        self.passenger = Passenger.objects.create(
            first_name="John",
            last_name="Doe",
            passport_number="AB123456",
            email="john.doe@example.com",
            phone="+1234567890",
            flight=self.flight,
            seat_number="12A",
            status=PassengerStatus.CHECKED_IN.value,
            checked_bags=2,
        )
    
    def test_passenger_creation(self):
        """Test passenger is created correctly."""
        self.assertEqual(self.passenger.first_name, "John")
        self.assertEqual(self.passenger.last_name, "Doe")
        self.assertEqual(self.passenger.passport_number, "AB123456")
        self.assertEqual(self.passenger.email, "john.doe@example.com")
        self.assertEqual(self.passenger.seat_number, "12A")
        self.assertEqual(self.passenger.status, PassengerStatus.CHECKED_IN.value)
    
    def test_passenger_str(self):
        """Test passenger string representation."""
        self.assertEqual(str(self.passenger), "Doe, John (AB123456)")
    
    def test_passenger_flight_relationship(self):
        """Test passenger can access its flight."""
        self.assertEqual(self.passenger.flight.flight_number, "AA123")
    
    def test_passenger_manager_by_flight(self):
        """Test PassengerManager.by_flight() filters by flight."""
        passengers = Passenger.objects.by_flight(self.flight.id)
        self.assertEqual(passengers.count(), 1)
    
    def test_passenger_manager_checked_in(self):
        """Test PassengerManager.checked_in() returns checked-in passengers."""
        checked_in = Passenger.objects.checked_in()
        self.assertEqual(checked_in.count(), 1)


class StaffModelTest(TestCase):
    """Tests for the Staff model."""
    
    def setUp(self):
        """Set up test data."""
        self.staff = Staff.objects.create(
            first_name="Jane",
            last_name="Smith",
            employee_number="EMP001",
            role=StaffRole.PILOT.value,
            certification="AT Rating BPL, Type737",
            is_available=True,
            email="jane.smith@example.com",
            phone="+1234567890",
        )
    
    def test_staff_creation(self):
        """Test staff is created correctly."""
        self.assertEqual(self.staff.first_name, "Jane")
        self.assertEqual(self.staff.last_name, "Smith")
        self.assertEqual(self.staff.employee_number, "EMP001")
        self.assertEqual(self.staff.role, StaffRole.PILOT.value)
        self.assertTrue(self.staff.is_available)
    
    def test_staff_str(self):
        """Test staff string representation."""
        self.assertEqual(str(self.staff), "Smith, Jane (pilot)")
    
    def test_staff_manager_by_role(self):
        """Test StaffManager.by_role() filters by role."""
        Staff.objects.create(
            first_name="Bob",
            last_name="Jones",
            employee_number="EMP002",
            role=StaffRole.CO_PILOT.value,
        )
        
        pilots = Staff.objects.by_role(StaffRole.PILOT.value)
        self.assertEqual(pilots.count(), 1)
    
    def test_staff_manager_available(self):
        """Test StaffManager.available() returns available staff."""
        available_staff = Staff.objects.available()
        self.assertEqual(available_staff.count(), 1)
    
    def test_staff_manager_unavailable(self):
        """Test StaffManager.unavailable() returns unavailable staff."""
        Staff.objects.create(
            first_name="Unavailable",
            last_name="Staff",
            employee_number="EMP003",
            role=StaffRole.GROUND_CREW.value,
            is_available=False,
        )
        
        unavailable = Staff.objects.unavailable()
        self.assertEqual(unavailable.count(), 1)


class StaffAssignmentModelTest(TestCase):
    """Tests for the StaffAssignment model."""
    
    def setUp(self):
        """Set up test data."""
        self.flight = Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            status=FlightStatus.SCHEDULED.value,
        )
        
        self.staff = Staff.objects.create(
            first_name="Jane",
            last_name="Smith",
            employee_number="EMP001",
            role=StaffRole.CABIN_CREW.value,
        )
        
        self.assignment = StaffAssignment.objects.create(
            staff=self.staff,
            flight=self.flight,
            assignment_type=StaffRole.CABIN_CREW.value,
        )
    
    def test_assignment_creation(self):
        """Test assignment is created correctly."""
        self.assertEqual(self.assignment.staff, self.staff)
        self.assertEqual(self.assignment.flight, self.flight)
        self.assertEqual(self.assignment.assignment_type, StaffRole.CABIN_CREW.value)
    
    def test_assignment_str(self):
        """Test assignment string representation."""
        expected = f"{self.staff} assigned to {self.flight} ({self.assignment.assignment_type})"
        self.assertEqual(str(self.assignment), expected)
    
    def test_assignment_unique_constraint(self):
        """Test unique constraint prevents duplicate assignments."""
        with self.assertRaises(Exception):
            StaffAssignment.objects.create(
                staff=self.staff,
                flight=self.flight,
                assignment_type=StaffRole.CABIN_CREW.value,
            )


class EventLogModelTest(TestCase):
    """Tests for the EventLog model."""
    
    def setUp(self):
        """Set up test data."""
        self.flight = Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            status=FlightStatus.SCHEDULED.value,
        )
        
        self.event = EventLog.objects.create(
            event_type="FLIGHT_DEPARTURE",
            description="Flight AA123 departed from gate A1",
            flight=self.flight,
            severity=EventLog.EventSeverity.INFO.value,
        )
    
    def test_event_creation(self):
        """Test event is created correctly."""
        self.assertEqual(self.event.event_type, "FLIGHT_DEPARTURE")
        self.assertEqual(self.event.severity, EventLog.EventSeverity.INFO.value)
    
    def test_event_timestamp_is_timezone_aware(self):
        """Test event timestamp is timezone-aware (not naive)."""
        # Verify timestamp is not naive (has timezone info)
        self.assertIsNotNone(self.event.timestamp.tzinfo)
        self.assertIs(self.event.timestamp.tzinfo.utcoffset(self.event.timestamp), not None)
        # Verify timestamp is close to now (within 1 minute)
        now = timezone.now()
        self.assertLess(abs((self.event.timestamp - now).total_seconds()), 60)
    
    def test_event_str(self):
        """Test event string representation."""
        self.assertIn("FLIGHT_DEPARTURE", str(self.event))
    
    def test_event_manager_errors(self):
        """Test EventManager.errors() returns error events."""
        EventLog.objects.create(
            event_type="SYSTEM_ERROR",
            description="System error occurred",
            severity=EventLog.EventSeverity.ERROR.value,
        )
        
        errors = EventLog.objects.errors()
        self.assertEqual(errors.count(), 1)
    
    def test_event_manager_by_flight(self):
        """Test EventManager.by_flight() filters by flight."""
        events = EventLog.objects.by_flight(self.flight.id)
        self.assertEqual(events.count(), 1)


class FiscalAssessmentModelTest(TestCase):
    """Tests for the FiscalAssessment model."""
    
    def setUp(self):
        """Set up test data."""
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status=AssessmentStatus.DRAFT.value,
            fuel_revenue=Decimal("100000.00"),
            parking_revenue=Decimal("50000.00"),
            retail_revenue=Decimal("30000.00"),
            landing_fees=Decimal("80000.00"),
            cargo_revenue=Decimal("40000.00"),
            other_revenue=Decimal("10000.00"),
            security_costs=Decimal("20000.00"),
            maintenance_costs=Decimal("15000.00"),
            operational_costs=Decimal("10000.00"),
            staff_costs=Decimal("25000.00"),
            utility_costs=Decimal("5000.00"),
            other_expenses=Decimal("5000.00"),
            passenger_count=10000,
            flight_count=500,
            assessed_by="Admin User",
        )
    
    def test_assessment_creation(self):
        """Test fiscal assessment is created correctly."""
        self.assertEqual(self.assessment.airport.code, "LOS")
        self.assertEqual(self.assessment.period_type, "monthly")
        self.assertEqual(self.assessment.status, "draft")
    
    def test_assessment_str(self):
        """Test fiscal assessment string representation."""
        expected = "LOS - monthly (2025-01-01 to 2025-01-31)"
        self.assertEqual(str(self.assessment), expected)
    
    def test_calculate_totals(self):
        """Test calculate_totals method."""
        self.assessment.calculate_totals()
        
        # Revenue: 100000 + 50000 + 30000 + 80000 + 40000 + 10000 = 310000
        self.assertEqual(self.assessment.total_revenue, Decimal("310000.00"))
        
        # Expenses: 20000 + 15000 + 10000 + 25000 + 5000 + 5000 = 80000
        self.assertEqual(self.assessment.total_expenses, Decimal("80000.00"))
        
        # Net profit: 310000 - 80000 = 230000
        self.assertEqual(self.assessment.net_profit, Decimal("230000.00"))
    
    def test_assessment_unique_constraint(self):
        """Test unique constraint on airport + period + dates."""
        with self.assertRaises(Exception):
            FiscalAssessment.objects.create(
                airport=self.airport,
                period_type=AssessmentPeriod.MONTHLY.value,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
            )
    
    def test_fiscal_assessment_manager_draft(self):
        """Test FiscalAssessmentManager.draft() returns draft assessments."""
        draft_assessments = FiscalAssessment.objects.draft()
        self.assertEqual(draft_assessments.count(), 1)
    
    def test_fiscal_assessment_manager_completed(self):
        """Test FiscalAssessmentManager.completed() returns completed assessments."""
        FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.QUARTERLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            status=AssessmentStatus.COMPLETED.value,
        )
        
        completed = FiscalAssessment.objects.completed()
        self.assertEqual(completed.count(), 1)


class ReportModelTest(TestCase):
    """Tests for the Report model."""
    
    def setUp(self):
        """Set up test data."""
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.report = Report.objects.create(
            airport=self.airport,
            report_type=ReportType.FISCAL_SUMMARY.value,
            title="Monthly Financial Report",
            description="January 2025 financial summary",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            format=ReportFormat.HTML.value,
            generated_by="system",
            content={"summary": {"total_revenue": 100000}},
            is_generated=True,
        )
    
    def test_report_creation(self):
        """Test report is created correctly."""
        self.assertEqual(self.report.airport.code, "LOS")
        self.assertEqual(self.report.report_type, "fiscal_summary")
        self.assertTrue(self.report.is_generated)
    
    def test_report_str(self):
        """Test report string representation."""
        expected = "Monthly Financial Report (fiscal_summary) - 2025-01-01 to 2025-01-31"
        self.assertEqual(str(self.report), expected)
    
    def test_report_content(self):
        """Test report content storage."""
        self.assertEqual(self.report.content["summary"]["total_revenue"], 100000)


class DocumentModelTest(TestCase):
    """Tests for the Document model."""
    
    def setUp(self):
        """Set up test data."""
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.document = Document.objects.create(
            name="Invoice #001",
            document_type="invoice",
            airport=self.airport,
            content={"invoice_number": "001", "amount": 5000},
            is_template=False,
            created_by="admin",
        )
    
    def test_document_creation(self):
        """Test document is created correctly."""
        self.assertEqual(self.document.name, "Invoice #001")
        self.assertEqual(self.document.document_type, "invoice")
        self.assertFalse(self.document.is_template)
    
    def test_document_str(self):
        """Test document string representation."""
        self.assertEqual(str(self.document), "Invoice #001 (invoice)")
    
    def test_document_content(self):
        """Test document content storage."""
        self.assertEqual(self.document.content["invoice_number"], "001")
        self.assertEqual(self.document.content["amount"], 5000)


class AirportAPITest(APITestCase):
    """Tests for the Airport API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticated user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            is_superuser=True,  # Enable superuser for delete tests
            is_staff=True,
        )
        # Add user to editors group for create/update permissions
        editors_group, _ = Group.objects.get_or_create(name='editors')
        self.user.groups.add(editors_group)
        self.client.force_authenticate(user=self.user)
        
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
    
    def test_list_airports(self):
        """Test listing airports."""
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_airport(self):
        """Test creating an airport."""
        data = {
            'code': 'ABJ',
            'name': 'Abuja International Airport',
            'city': 'Abuja',
            'timezone': 'Africa/Lagos',
        }
        response = self.client.post('/api/v1/airports/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airport.objects.count(), 2)
    
    def test_retrieve_airport(self):
        """Test retrieving a single airport."""
        response = self.client.get(f'/api/v1/airports/{self.airport.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'LOS')
    
    def test_update_airport(self):
        """Test updating an airport."""
        data = {
            'code': 'LOS',
            'name': 'Lagos Airport Updated',
            'city': 'Lagos',
        }
        response = self.client.put(f'/api/v1/airports/{self.airport.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airport.refresh_from_db()
        self.assertEqual(self.airport.name, 'Lagos Airport Updated')
    
    def test_delete_airport(self):
        """Test deleting an airport."""
        response = self.client.delete(f'/api/v1/airports/{self.airport.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Airport.objects.count(), 0)
    
    def test_unauthenticated_access_denied(self):
        """Test unauthenticated access is denied."""
        self.client.logout()
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GateAPITest(APITestCase):
    """Tests for the Gate API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticated user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.gate = Gate.objects.create(
            gate_id="A1",
            terminal="Terminal 1",
            capacity="wide-body",
            status=GateStatus.AVAILABLE.value,
        )
    
    def test_list_gates(self):
        """Test listing gates."""
        response = self.client.get('/api/v1/gates/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_gates_by_status(self):
        """Test filtering gates by status."""
        Gate.objects.create(
            gate_id="B1",
            terminal="Terminal 1",
            status=GateStatus.OCCUPIED.value,
        )
        
        response = self.client.get('/api/v1/gates/?status=available')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_gates_by_terminal(self):
        """Test filtering gates by terminal."""
        Gate.objects.create(
            gate_id="B1",
            terminal="Terminal 2",
            status=GateStatus.AVAILABLE.value,
        )
        
        response = self.client.get('/api/v1/gates/?terminal=Terminal 1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class FlightAPITest(APITestCase):
    """Tests for the Flight API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticated user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.gate = Gate.objects.create(
            gate_id="A1",
            terminal="Terminal 1",
            status=GateStatus.AVAILABLE.value,
        )
        
        self.flight = Flight.objects.create(
            flight_number="AA123",
            airline="American Airlines",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )
    
    def test_list_flights(self):
        """Test listing flights."""
        response = self.client.get('/api/v1/flights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_flights_by_status(self):
        """Test filtering flights by status."""
        Flight.objects.create(
            flight_number="BB456",
            origin="LOS",
            destination="ABJ",
            scheduled_departure=timezone.now() + timedelta(hours=3),
            scheduled_arrival=timezone.now() + timedelta(hours=4),
            status=FlightStatus.DELAYED.value,
        )
        
        response = self.client.get('/api/v1/flights/?status=scheduled')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_flights_by_airline(self):
        """Test filtering flights by airline."""
        response = self.client.get('/api/v1/flights/?airline=American Airlines')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_flights_by_route(self):
        """Test filtering flights by origin/destination."""
        response = self.client.get('/api/v1/flights/?origin=LOS&destination=JFK')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class StaffAPITest(APITestCase):
    """Tests for the Staff API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticated user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.staff = Staff.objects.create(
            first_name="Jane",
            last_name="Smith",
            employee_number="EMP001",
            role=StaffRole.PILOT.value,
            is_available=True,
        )
    
    def test_list_staff(self):
        """Test listing staff."""
        response = self.client.get('/api/v1/staff/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_staff_by_role(self):
        """Test filtering staff by role."""
        Staff.objects.create(
            first_name="Bob",
            last_name="Jones",
            employee_number="EMP002",
            role=StaffRole.GROUND_CREW.value,
        )
        
        response = self.client.get('/api/v1/staff/?role=pilot')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_staff_by_availability(self):
        """Test filtering staff by availability."""
        response = self.client.get('/api/v1/staff/?is_available=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class FiscalAssessmentAPITest(APITestCase):
    """Tests for the FiscalAssessment API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticated user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Add user to editors group for create permissions
        editors_group, _ = Group.objects.get_or_create(name='editors')
        self.user.groups.add(editors_group)
        self.client.force_authenticate(user=self.user)
        
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status=AssessmentStatus.DRAFT.value,
            total_revenue=Decimal("100000.00"),
            total_expenses=Decimal("50000.00"),
            net_profit=Decimal("50000.00"),
        )
    
    def test_list_assessments(self):
        """Test listing fiscal assessments."""
        response = self.client.get('/api/v1/assessments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filter_assessments_by_status(self):
        """Test filtering assessments by status."""
        FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.QUARTERLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 31),
            status=AssessmentStatus.COMPLETED.value,
        )
        
        response = self.client.get('/api/v1/assessments/?status=draft')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_assessment(self):
        """Test creating a fiscal assessment."""
        data = {
            'airport': self.airport.id,
            'period_type': 'quarterly',
            'start_date': '2025-04-01',
            'end_date': '2025-06-30',
            'status': 'draft',
            'fuel_revenue': 50000,
            'parking_revenue': 25000,
        }
        response = self.client.post('/api/v1/assessments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DashboardSummaryAPITest(APITestCase):
    """Tests for the Dashboard Summary API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticated user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create airports
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        # Create gates
        Gate.objects.create(gate_id="A1", terminal="T1", status=GateStatus.AVAILABLE.value)
        Gate.objects.create(gate_id="A2", terminal="T1", status=GateStatus.OCCUPIED.value)
        
        # Create flights
        now = timezone.now()
        Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=now + timedelta(hours=1),
            scheduled_arrival=now + timedelta(hours=8),
            status=FlightStatus.SCHEDULED.value,
        )
        
        # Create staff
        Staff.objects.create(
            first_name="Jane",
            last_name="Smith",
            employee_number="EMP001",
            role=StaffRole.PILOT.value,
            is_available=True,
        )
    
    def test_dashboard_summary(self):
        """Test dashboard summary endpoint."""
        response = self.client.get('/api/v1/dashboard-summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check structure
        self.assertIn('flights', response.data)
        self.assertIn('gates', response.data)
        self.assertIn('staff', response.data)
        
        # Check values
        self.assertEqual(response.data['gates']['total'], 2)
        self.assertEqual(response.data['gates']['available'], 1)
        self.assertEqual(response.data['staff']['total'], 1)


class MetricsAPITest(APITestCase):
    """Tests for the Metrics API endpoint."""
    
    def setUp(self):
        """Set up test data and authenticated user."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        # Create flights
        now = timezone.now()
        Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=now - timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=6),
            actual_departure=now - timedelta(hours=2),
            status=FlightStatus.DEPARTED.value,
            delay_minutes=5,
        )
        
        Flight.objects.create(
            flight_number="BB456",
            origin="LOS",
            destination="ABJ",
            scheduled_departure=now - timedelta(hours=1),
            scheduled_arrival=now + timedelta(hours=1),
            status=FlightStatus.DELAYED.value,
            delay_minutes=30,
        )
        
        # Create passengers
        flight = Flight.objects.first()
        Passenger.objects.create(
            first_name="John",
            last_name="Doe",
            passport_number="AB123456",
            flight=flight,
            status=PassengerStatus.BOARDED.value,
        )
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = self.client.get('/api/v1/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check structure
        self.assertIn('flights', response.data)
        self.assertIn('passengers', response.data)
    
    def test_metrics_by_period(self):
        """Test metrics filtering by period."""
        response = self.client.get('/api/v1/metrics/?period=day')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class FiscalAssessmentViewTest(TestCase):
    """Tests for fiscal assessment views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status=AssessmentStatus.DRAFT.value,
            total_revenue=Decimal("100000.00"),
            total_expenses=Decimal("50000.00"),
            net_profit=Decimal("50000.00"),
        )
    
    def test_assessment_list_view_requires_login(self):
        """Test assessment list view requires authentication."""
        response = self.client.get(reverse("core:fiscal_assessment_list"))
        self.assertEqual(response.status_code, 302)  # Redirects to login
    
    def test_assessment_list_view_authenticated(self):
        """Test assessment list view with authentication."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse("core:fiscal_assessment_list"))
        self.assertEqual(response.status_code, 200)
    
    def test_assessment_detail_view_requires_login(self):
        """Test assessment detail view requires authentication."""
        response = self.client.get(
            reverse("core:fiscal_assessment_detail", args=[self.assessment.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirects to login
    
    def test_assessment_detail_view_authenticated(self):
        """Test assessment detail view with authentication."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse("core:fiscal_assessment_detail", args=[self.assessment.id])
        )
        self.assertEqual(response.status_code, 200)
    
    def test_assessment_create_view_requires_login(self):
        """Test assessment create view requires authentication."""
        response = self.client.get(reverse("core:fiscal_assessment_create"))
        self.assertEqual(response.status_code, 302)  # Redirects to login


class ReportViewTest(TestCase):
    """Tests for report views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.report = Report.objects.create(
            airport=self.airport,
            report_type=ReportType.FISCAL_SUMMARY.value,
            title="Test Report",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
            format=ReportFormat.HTML.value,
        )
    
    def test_report_list_view_requires_login(self):
        """Test report list view requires authentication."""
        response = self.client.get(reverse("core:report_list"))
        self.assertEqual(response.status_code, 302)  # Redirects to login
    
    def test_report_list_view_authenticated(self):
        """Test report list view with authentication."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse("core:report_list"))
        self.assertEqual(response.status_code, 200)


class DocumentViewTest(TestCase):
    """Tests for document views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.document = Document.objects.create(
            name="Test Document",
            document_type="invoice",
            airport=self.airport,
            content={},
        )
    
    def test_document_list_view_requires_login(self):
        """Test document list view requires authentication."""
        response = self.client.get(reverse("core:document_list"))
        self.assertEqual(response.status_code, 302)  # Redirects to login
    
    def test_document_list_view_authenticated(self):
        """Test document list view with authentication."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse("core:document_list"))
        self.assertEqual(response.status_code, 200)

class FlightOperationsIntegrationTest(TestCase):
    """Integration tests for flight operations workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.gate = Gate.objects.create(
            gate_id="A1",
            terminal="Terminal 1",
            status=GateStatus.AVAILABLE.value,
        )
        
        self.flight = Flight.objects.create(
            flight_number="AA123",
            airline="American Airlines",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )
    
    def test_flight_assignment_updates_gate_status(self):
        """Test that assigning a flight to a gate updates gate status.
        
        When a flight is assigned to a gate, the post_save signal automatically
        updates the gate status to OCCUPIED. When the flight is deleted, the
        post_delete signal automatically sets it back to AVAILABLE.
        """
        # When flight is created with a gate, signal automatically sets gate to OCCUPIED
        self.gate.refresh_from_db()
        self.assertEqual(self.gate.status, GateStatus.OCCUPIED.value)
        
        # Delete the flight - signal should set gate back to AVAILABLE
        self.flight.delete()
        
        self.gate.refresh_from_db()
        self.assertEqual(self.gate.status, GateStatus.AVAILABLE.value)
    
    def test_passenger_boarding_workflow(self):
        """Test passenger boarding workflow."""
        # Create passenger
        passenger = Passenger.objects.create(
            first_name="John",
            last_name="Doe",
            passport_number="AB123456",
            flight=self.flight,
            status=PassengerStatus.CHECKED_IN.value,
        )
        
        # Verify passenger status
        self.assertEqual(passenger.status, PassengerStatus.CHECKED_IN.value)
        
        # Simulate boarding
        passenger.status = PassengerStatus.BOARDED.value
        passenger.save()
        
        passenger.refresh_from_db()
        self.assertEqual(passenger.status, PassengerStatus.BOARDED.value)
    
    def test_staff_assignment_workflow(self):
        """Test staff assignment to flights."""
        # Create staff
        pilot = Staff.objects.create(
            first_name="Jane",
            last_name="Smith",
            employee_number="EMP001",
            role=StaffRole.PILOT.value,
            is_available=True,
        )
        
        # Assign to flight
        assignment = StaffAssignment.objects.create(
            staff=pilot,
            flight=self.flight,
            assignment_type=StaffRole.PILOT.value,
        )
        
        # Verify assignment
        self.assertEqual(assignment.staff, pilot)
        self.assertEqual(assignment.flight, self.flight)
        
        # Mark staff as unavailable
        pilot.is_available = False
        pilot.save()
        
        pilot.refresh_from_db()
        self.assertFalse(pilot.is_available)


class FiscalAssessmentWorkflowTest(TestCase):
    """Integration tests for fiscal assessment workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.user = User.objects.create_user(
            username='assessor',
            password='testpass123'
        )
    
    def test_assessment_creation_and_calculation(self):
        """Test creating and calculating a fiscal assessment."""
        # Create assessment with financial data
        assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status=AssessmentStatus.DRAFT.value,
            fuel_revenue=Decimal("100000.00"),
            parking_revenue=Decimal("50000.00"),
            landing_fees=Decimal("80000.00"),
            security_costs=Decimal("20000.00"),
            maintenance_costs=Decimal("15000.00"),
            staff_costs=Decimal("25000.00"),
            passenger_count=10000,
            flight_count=500,
        )
        
        # Calculate totals
        assessment.calculate_totals()
        assessment.save()
        
        # Verify calculations
        assessment.refresh_from_db()
        
        # Revenue: 100000 + 50000 + 80000 = 230000
        self.assertEqual(assessment.total_revenue, Decimal("230000.00"))
        
        # Expenses: 20000 + 15000 + 25000 = 60000
        self.assertEqual(assessment.total_expenses, Decimal("60000.00"))
        
        # Net: 230000 - 60000 = 170000
        self.assertEqual(assessment.net_profit, Decimal("170000.00"))
    
    def test_assessment_approval_workflow(self):
        """Test assessment approval workflow."""
        # Create assessment
        assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status=AssessmentStatus.DRAFT.value,
            total_revenue=Decimal("100000.00"),
            total_expenses=Decimal("50000.00"),
            net_profit=Decimal("50000.00"),
        )
        
        # Update status to completed
        assessment.status = AssessmentStatus.COMPLETED.value
        assessment.save()
        
        assessment.refresh_from_db()
        self.assertEqual(assessment.status, AssessmentStatus.COMPLETED.value)
        
        # Approve assessment
        assessment.status = AssessmentStatus.APPROVED.value
        assessment.approved_by = "testuser"
        assessment.approved_at = timezone.now()
        assessment.save()
        
        assessment.refresh_from_db()
        self.assertEqual(assessment.status, AssessmentStatus.APPROVED.value)
        self.assertEqual(assessment.approved_by, "testuser")


class EventLoggingIntegrationTest(TestCase):
    """Integration tests for event logging."""
    
    def setUp(self):
        """Set up test data."""
        self.flight = Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            status=FlightStatus.SCHEDULED.value,
        )
    
    def test_flight_status_change_logging(self):
        """Test logging flight status changes."""
        # Create initial event
        EventLog.objects.create(
            event_type="FLIGHT_STATUS_CHANGE",
            description=f"Flight {self.flight.flight_number} status changed to scheduled",
            flight=self.flight,
            severity=EventLog.EventSeverity.INFO.value,
        )
        
        # Verify event was created
        events = EventLog.objects.by_flight(self.flight.id)
        self.assertEqual(events.count(), 1)
        
        # Update flight status
        self.flight.status = FlightStatus.BOARDING.value
        self.flight.save()
        
        # Log status change
        EventLog.objects.create(
            event_type="FLIGHT_STATUS_CHANGE",
            description=f"Flight {self.flight.flight_number} status changed to boarding",
            flight=self.flight,
            severity=EventLog.EventSeverity.INFO.value,
        )
        
        # Verify both events exist
        events = EventLog.objects.by_flight(self.flight.id)
        self.assertEqual(events.count(), 2)
    
    def test_error_event_logging(self):
        """Test logging error events."""
        # Create error event
        EventLog.objects.create(
            event_type="GATE_ERROR",
            description="Gate A1 communication failure",
            severity=EventLog.EventSeverity.ERROR.value,
        )
        
        # Verify error was logged
        errors = EventLog.objects.errors()
        self.assertEqual(errors.count(), 1)

class EdgeCaseTests(TestCase):
    """Tests for edge cases and error conditions."""
    
    def test_gate_unique_constraint(self):
        """Test unique constraint on gate_id."""
        Gate.objects.create(gate_id="A1", terminal="Terminal 1")
        
        with self.assertRaises(Exception):
            Gate.objects.create(gate_id="A1", terminal="Terminal 2")
    
    def test_passenger_unique_passport(self):
        """Test unique constraint on passport_number."""
        flight = Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
        )
        
        Passenger.objects.create(
            first_name="John",
            last_name="Doe",
            passport_number="AB123456",
            flight=flight,
        )
        
        with self.assertRaises(Exception):
            Passenger.objects.create(
                first_name="Jane",
                last_name="Doe",
                passport_number="AB123456",
                flight=flight,
            )
    
    def test_staff_unique_employee_number(self):
        """Test unique constraint on employee_number."""
        Staff.objects.create(
            first_name="John",
            last_name="Doe",
            employee_number="EMP001",
            role=StaffRole.PILOT.value,
        )
        
        with self.assertRaises(Exception):
            Staff.objects.create(
                first_name="Jane",
                last_name="Smith",
                employee_number="EMP001",
                role=StaffRole.CO_PILOT.value,
            )
    
    def test_flight_unique_flight_number(self):
        """Test unique constraint on flight_number."""
        Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
        )
        
        with self.assertRaises(Exception):
            Flight.objects.create(
                flight_number="AA123",
                origin="ABJ",
                destination="LOS",
                scheduled_departure=timezone.now() + timedelta(hours=3),
                scheduled_arrival=timezone.now() + timedelta(hours=4),
            )
    
    def test_cascade_delete_passengers(self):
        """Test cascade delete for passengers when flight is deleted."""
        flight = Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
        )
        
        Passenger.objects.create(
            first_name="John",
            last_name="Doe",
            passport_number="AB123456",
            flight=flight,
        )
        
        flight_id = flight.id
        flight.delete()
        
        # Passengers should be cascade deleted
        self.assertEqual(Passenger.objects.filter(flight_id=flight_id).count(), 0)
    
    def test_set_null_event_on_flight_delete(self):
        """Test event flight is set to null when flight is deleted."""
        flight = Flight.objects.create(
            flight_number="AA123",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
        )
        
        event = EventLog.objects.create(
            event_type="TEST",
            description="Test event",
            flight=flight,
        )
        
        flight.delete()
        
        event.refresh_from_db()
        self.assertIsNone(event.flight)
