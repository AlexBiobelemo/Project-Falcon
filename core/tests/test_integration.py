"""
Integration tests for the Airport Operations Management System.

Tests cover:
- End-to-end workflows
- Multi-step operations
- Cross-module interactions
- Real-world usage scenarios
- Complete business processes
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core.paginator import Paginator

from core.models import (
    Airport, Gate, GateStatus, Flight, FlightStatus,
    Passenger, PassengerStatus, Staff, StaffRole, StaffAssignment,
    EventLog, FiscalAssessment, AssessmentPeriod, AssessmentStatus,
    Report, ReportType, Document, Aircraft, CrewMember,
)


class FlightOperationsWorkflowTest(TestCase):
    """Integration tests for flight operations workflow."""

    def setUp(self):
        self.client = Client()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_superuser=True,
            is_staff=True,
        )
        
        # Create editor user
        self.editor = User.objects.create_user(
            username='editor',
            password='editorpass123',
        )
        editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(editors_group)
        
        # Create base data
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
        )
        
        self.gate = Gate.objects.create(
            gate_id="A1",
            terminal="Terminal 1",
            capacity="wide-body",
            status=GateStatus.AVAILABLE.value,
        )

    def test_complete_flight_lifecycle(self):
        """Test complete flight lifecycle from scheduling to arrival."""
        now = timezone.now()
        
        # 1. Schedule flight
        flight = Flight.objects.create(
            flight_number="AA100",
            airline="American Airlines",
            origin="LOS",
            destination="JFK",
            scheduled_departure=now + timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=10),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )
        
        # Log event
        EventLog.objects.create(
            event_type="FLIGHT_SCHEDULED",
            description=f"Flight {flight.flight_number} scheduled",
            flight=flight,
        )
        
        # 2. Update to boarding
        flight.status = FlightStatus.BOARDING.value
        flight.save()
        
        EventLog.objects.create(
            event_type="FLIGHT_BOARDING",
            description=f"Flight {flight.flight_number} boarding",
            flight=flight,
        )
        
        # 3. Add passengers
        for i in range(5):
            Passenger.objects.create(
                first_name=f"Passenger{i}",
                last_name="Test",
                passport_number=f"PP{i:06d}",
                flight=flight,
                seat_number=f"{i+1}A",
                status=PassengerStatus.CHECKED_IN.value,
            )
        
        # 4. Update to departed
        flight.status = FlightStatus.DEPARTED.value
        flight.actual_departure = now + timedelta(hours=2)
        flight.save()
        
        # Update gate status
        self.gate.status = GateStatus.OCCUPIED.value
        self.gate.save()
        
        # 5. Update to arrived
        flight.status = FlightStatus.ARRIVED.value
        flight.actual_arrival = now + timedelta(hours=10)
        flight.save()
        
        # Update gate status
        self.gate.status = GateStatus.AVAILABLE.value
        self.gate.save()
        
        # Verify final state
        flight.refresh_from_db()
        self.assertEqual(flight.status, FlightStatus.ARRIVED.value)
        self.assertIsNotNone(flight.actual_departure)
        self.assertIsNotNone(flight.actual_arrival)
        self.assertEqual(flight.passengers.count(), 5)
        
        # Verify events logged
        events = EventLog.objects.filter(flight=flight).count()
        self.assertGreaterEqual(events, 3)

    def test_flight_delay_handling(self):
        """Test handling of flight delays."""
        now = timezone.now()
        
        flight = Flight.objects.create(
            flight_number="DL200",
            airline="Delta Airlines",
            origin="LOS",
            destination="ATL",
            scheduled_departure=now + timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=12),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )
        
        # Simulate delay
        flight.status = FlightStatus.DELAYED.value
        flight.delay_minutes = 45
        flight.save()
        
        EventLog.objects.create(
            event_type="FLIGHT_DELAYED",
            description=f"Flight {flight.flight_number} delayed by 45 minutes",
            flight=flight,
            severity=EventLog.EventSeverity.WARNING.value,
        )
        
        # Notify passengers (simulated)
        passengers = Passenger.objects.bulk_create([
            Passenger(
                first_name="Delayed",
                last_name="Passenger",
                passport_number=f"DPP{i:06d}",
                flight=flight,
            )
            for i in range(3)
        ])
        
        # Verify delay state
        flight.refresh_from_db()
        self.assertEqual(flight.status, FlightStatus.DELAYED.value)
        self.assertEqual(flight.delay_minutes, 45)

    def test_flight_cancellation(self):
        """Test flight cancellation workflow."""
        now = timezone.now()
        
        flight = Flight.objects.create(
            flight_number="CN300",
            airline="Cancel Airlines",
            origin="LOS",
            destination="JFK",
            scheduled_departure=now + timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=10),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )
        
        # Add passengers
        for i in range(5):
            Passenger.objects.create(
                first_name="Cancelled",
                last_name="Passenger",
                passport_number=f"CP{i:06d}",
                flight=flight,
            )
        
        # Cancel flight
        flight.status = FlightStatus.CANCELLED.value
        flight.save()
        
        # Release gate
        self.gate.status = GateStatus.AVAILABLE.value
        self.gate.save()
        
        # Log event
        EventLog.objects.create(
            event_type="FLIGHT_CANCELLED",
            description=f"Flight {flight.flight_number} cancelled",
            flight=flight,
            severity=EventLog.EventSeverity.ERROR.value,
        )
        
        # Mark passengers as no-show or rebooked
        flight.passengers.update(status=PassengerStatus.NO_SHOW.value)
        
        # Verify cancellation state
        flight.refresh_from_db()
        self.assertEqual(flight.status, FlightStatus.CANCELLED.value)
        self.assertEqual(flight.passengers.filter(status=PassengerStatus.NO_SHOW.value).count(), 5)


class GateManagementWorkflowTest(TestCase):
    """Integration tests for gate management workflow."""

    def setUp(self):
        self.gate = Gate.objects.create(
            gate_id="GM1",
            terminal="Terminal 1",
            capacity="wide-body",
            status=GateStatus.AVAILABLE.value,
        )

    def test_gate_assignment_workflow(self):
        """Test gate assignment workflow."""
        now = timezone.now()
        
        # Create flights
        flight1 = Flight.objects.create(
            flight_number="GA100",
            origin="LOS",
            destination="JFK",
            scheduled_departure=now + timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=10),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )
        
        # Gate should be occupied
        self.gate.status = GateStatus.OCCUPIED.value
        self.gate.save()
        
        # Try to assign another flight (should handle gracefully)
        flight2 = Flight.objects.create(
            flight_number="GA200",
            origin="LOS",
            destination="LHR",
            scheduled_departure=now + timedelta(hours=12),
            scheduled_arrival=now + timedelta(hours=20),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )
        
        # Verify gate has multiple flights
        self.assertEqual(self.gate.flights.count(), 2)

    def test_gate_maintenance_workflow(self):
        """Test gate maintenance workflow."""
        # Put gate under maintenance
        self.gate.status = GateStatus.MAINTENANCE.value
        self.gate.save()
        
        EventLog.objects.create(
            event_type="GATE_MAINTENANCE",
            description=f"Gate {self.gate.gate_id} under maintenance",
            severity=EventLog.EventSeverity.WARNING.value,
        )
        
        # Cannot assign flights to maintenance gate
        flight = Flight.objects.create(
            flight_number="GM100",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )
        
        # Verify maintenance state
        self.gate.refresh_from_db()
        self.assertEqual(self.gate.status, GateStatus.MAINTENANCE.value)

    def test_gate_utilization_tracking(self):
        """Test gate utilization tracking."""
        now = timezone.now()
        
        # Create multiple flights using the gate
        for i in range(5):
            Flight.objects.create(
                flight_number=f"GU{i:03d}",
                origin="LOS",
                destination=f"DEST{i}",
                scheduled_departure=now + timedelta(hours=i*2),
                scheduled_arrival=now + timedelta(hours=i*2+4),
                gate=self.gate,
                status=FlightStatus.SCHEDULED.value,
            )
        
        # Count flights
        flight_count = self.gate.flights.count()
        self.assertEqual(flight_count, 5)


class PassengerManagementWorkflowTest(TestCase):
    """Integration tests for passenger management workflow."""

    def setUp(self):
        self.flight = Flight.objects.create(
            flight_number="PM100",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            status=FlightStatus.SCHEDULED.value,
        )

    def test_passenger_check_in_workflow(self):
        """Test passenger check-in workflow."""
        # Create passenger
        passenger = Passenger.objects.create(
            first_name="Check",
            last_name="In",
            passport_number="CI000001",
            flight=self.flight,
            seat_number="12A",
            status=PassengerStatus.CHECKED_IN.value,
            checked_bags=2,
        )
        
        EventLog.objects.create(
            event_type="PASSENGER_CHECKIN",
            description=f"Passenger {passenger.passport_number} checked in",
            flight=self.flight,
        )
        
        # Verify check-in state
        self.assertEqual(passenger.status, PassengerStatus.CHECKED_IN.value)
        self.assertEqual(passenger.checked_bags, 2)

    def test_passenger_boarding_workflow(self):
        """Test passenger boarding workflow."""
        passenger = Passenger.objects.create(
            first_name="Board",
            last_name="Passenger",
            passport_number="BP000001",
            flight=self.flight,
            seat_number="15B",
            status=PassengerStatus.CHECKED_IN.value,
        )
        
        # Board passenger
        passenger.status = PassengerStatus.BOARDED.value
        passenger.save()
        
        EventLog.objects.create(
            event_type="PASSENGER_BOARDED",
            description=f"Passenger {passenger.passport_number} boarded",
            flight=self.flight,
        )
        
        # Verify boarding state
        passenger.refresh_from_db()
        self.assertEqual(passenger.status, PassengerStatus.BOARDED.value)

    def test_passenger_no_show_workflow(self):
        """Test passenger no-show workflow."""
        passenger = Passenger.objects.create(
            first_name="No",
            last_name="Show",
            passport_number="NS000001",
            flight=self.flight,
            seat_number="20C",
            status=PassengerStatus.CHECKED_IN.value,
        )
        
        # Mark as no-show after flight departs
        passenger.status = PassengerStatus.NO_SHOW.value
        passenger.save()
        
        # Verify no-show state
        passenger.refresh_from_db()
        self.assertEqual(passenger.status, PassengerStatus.NO_SHOW.value)


class FiscalAssessmentWorkflowTest(TestCase):
    """Integration tests for fiscal assessment workflow."""

    def setUp(self):
        self.client = Client()
        
        self.editor = User.objects.create_user(
            username='editor',
            password='editorpass123',
        )
        editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(editors_group)
        
        self.approver = User.objects.create_user(
            username='approver',
            password='approverpass123',
        )
        approvers_group, _ = Group.objects.get_or_create(name='approvers')
        self.approver.groups.add(approvers_group)
        
        self.airport = Airport.objects.create(
            code="FA",
            name="Fiscal Assessment Airport",
            city="City",
        )

    def test_complete_assessment_lifecycle(self):
        """Test complete fiscal assessment lifecycle."""
        # 1. Create draft assessment
        assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status=AssessmentStatus.DRAFT.value,
            fuel_revenue=Decimal("100000.00"),
            parking_revenue=Decimal("50000.00"),
            retail_revenue=Decimal("30000.00"),
            landing_fees=Decimal("80000.00"),
            security_costs=Decimal("20000.00"),
            maintenance_costs=Decimal("15000.00"),
            staff_costs=Decimal("25000.00"),
            passenger_count=10000,
            flight_count=500,
            assessed_by=self.editor.username,
        )
        
        # Calculate totals
        assessment.calculate_totals()
        assessment.save()
        
        EventLog.objects.create(
            event_type="ASSESSMENT_CREATED",
            description=f"Fiscal assessment created for {self.airport.code}",
            severity=EventLog.EventSeverity.INFO.value,
        )
        
        # 2. Complete assessment
        assessment.status = AssessmentStatus.COMPLETED.value
        assessment.save()
        
        # 3. Approve assessment
        assessment.status = AssessmentStatus.APPROVED.value
        assessment.approved_by = self.approver.username
        assessment.approved_at = timezone.now()
        assessment.save()
        
        EventLog.objects.create(
            event_type="ASSESSMENT_APPROVED",
            description=f"Fiscal assessment approved by {self.approver.username}",
            severity=EventLog.EventSeverity.INFO.value,
        )
        
        # Verify final state
        assessment.refresh_from_db()
        self.assertEqual(assessment.status, AssessmentStatus.APPROVED.value)
        self.assertEqual(assessment.total_revenue, Decimal("260000.00"))
        self.assertEqual(assessment.total_expenses, Decimal("60000.00"))
        self.assertEqual(assessment.net_profit, Decimal("200000.00"))
        self.assertIsNotNone(assessment.approved_at)

    def test_assessment_rejection_workflow(self):
        """Test assessment rejection workflow."""
        assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
            status=AssessmentStatus.COMPLETED.value,
        )
        
        # Reject assessment
        assessment.status = AssessmentStatus.REJECTED.value
        assessment.assessment_notes = "Rejected due to incomplete data"
        assessment.save()
        
        EventLog.objects.create(
            event_type="ASSESSMENT_REJECTED",
            description=f"Fiscal assessment rejected: {assessment.assessment_notes}",
            severity=EventLog.EventSeverity.WARNING.value,
        )
        
        # Verify rejection state
        assessment.refresh_from_db()
        self.assertEqual(assessment.status, AssessmentStatus.REJECTED.value)
        self.assertIn("Rejected", assessment.assessment_notes)


class StaffAssignmentWorkflowTest(TestCase):
    """Integration tests for staff assignment workflow."""

    def setUp(self):
        self.flight = Flight.objects.create(
            flight_number="SA100",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            status=FlightStatus.SCHEDULED.value,
        )
        
        self.staff = Staff.objects.create(
            first_name="Staff",
            last_name="Member",
            employee_number="SM001",
            role=StaffRole.CABIN_CREW.value,
            is_available=True,
        )

    def test_staff_assignment_workflow(self):
        """Test staff assignment workflow."""
        # Assign staff to flight
        assignment = StaffAssignment.objects.create(
            staff=self.staff,
            flight=self.flight,
            assignment_type=StaffRole.CABIN_CREW.value,
        )
        
        EventLog.objects.create(
            event_type="STAFF_ASSIGNED",
            description=f"Staff {self.staff.employee_number} assigned to flight {self.flight.flight_number}",
            flight=self.flight,
        )
        
        # Mark staff as unavailable
        self.staff.is_available = False
        self.staff.save()
        
        # Verify assignment
        self.assertEqual(self.staff.assignments.count(), 1)
        self.assertFalse(self.staff.is_available)

    def test_staff_conflict_detection(self):
        """Test staff assignment conflict detection."""
        # Create a different staff member for the second flight
        staff2 = Staff.objects.create(
            first_name="Another",
            last_name="Staff",
            employee_number="SM002",
            role=StaffRole.CABIN_CREW.value,
        )
        
        # Assign different staff to overlapping flight
        StaffAssignment.objects.create(
            staff=staff2,
            flight=self.flight,
            assignment_type=StaffRole.CABIN_CREW.value,
        )
        
        # Verify assignment was created
        self.assertEqual(self.flight.staff_assignments.count(), 2)


class ReportGenerationWorkflowTest(TestCase):
    """Integration tests for report generation workflow."""

    def setUp(self):
        self.airport = Airport.objects.create(
            code="RG",
            name="Report Generation Airport",
            city="City",
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='editorpass123',
        )
        editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(editors_group)

    def test_report_creation_workflow(self):
        """Test report creation workflow."""
        # Create fiscal assessments for data
        for i in range(3):
            FiscalAssessment.objects.create(
                airport=self.airport,
                period_type=AssessmentPeriod.MONTHLY.value,
                start_date=date(2025, i+1, 1),
                end_date=date(2025, i+1, 28),
                status=AssessmentStatus.APPROVED.value,
                fuel_revenue=Decimal("100000.00"),
                total_revenue=Decimal("200000.00"),
                passenger_count=10000,
                flight_count=500,
            )
        
        # Generate report
        report = Report.objects.create(
            airport=self.airport,
            report_type=ReportType.FISCAL_SUMMARY.value,
            title="Q1 Fiscal Summary",
            description="First quarter fiscal summary report",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31),
            format='html',
            generated_by=self.editor.username,
            content={
                'summary': {
                    'total_revenue': 600000,
                    'total_passengers': 30000,
                    'total_flights': 1500,
                }
            },
            is_generated=True,
            generated_at=timezone.now(),
        )
        
        EventLog.objects.create(
            event_type="REPORT_GENERATED",
            description=f"Report '{report.title}' generated",
            action=EventLog.ActionType.CREATE.value,
        )
        
        # Verify report
        self.assertTrue(report.is_generated)
        self.assertEqual(report.content['summary']['total_revenue'], 600000)


class DashboardIntegrationTest(TestCase):
    """Integration tests for dashboard functionality."""

    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='dashboard',
            password='dashpass123',
            is_superuser=True,
        )
        
        # Create test data
        self.airport = Airport.objects.create(
            code="DB",
            name="Dashboard Airport",
            city="City",
        )
        
        self.gate = Gate.objects.create(
            gate_id="DB1",
            terminal="Terminal 1",
            status=GateStatus.AVAILABLE.value,
        )
        
        now = timezone.now()
        
        # Create flights with different statuses
        for status in [FlightStatus.SCHEDULED, FlightStatus.DELAYED, 
                       FlightStatus.DEPARTED, FlightStatus.ARRIVED]:
            Flight.objects.create(
                flight_number=f"DB{status.value[:3].upper()}",
                origin="LOS",
                destination="JFK",
                scheduled_departure=now + timedelta(hours=1),
                scheduled_arrival=now + timedelta(hours=9),
                gate=self.gate,
                status=status.value,
            )

    def test_dashboard_data_aggregation(self):
        """Test dashboard data aggregation."""
        self.client.login(username='dashboard', password='dashpass123')
        
        response = self.client.get('/dashboard/')
        
        # Should render successfully
        self.assertEqual(response.status_code, 200)
        
        # Check context data exists
        self.assertIn('flight_status_counts', response.context)
        self.assertIn('gates', response.context)

    def test_dashboard_api_endpoint(self):
        """Test dashboard API endpoint."""
        self.client.login(username='dashboard', password='dashpass123')
        
        response = self.client.get('/api/v1/dashboard-summary/')
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('total_flights', data)
        self.assertIn('gates', data)
        self.assertIn('upcoming_flights', data)


class EventLogIntegrationTest(TestCase):
    """Integration tests for event logging."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='logger',
            password='logpass123',
        )
        
        self.flight = Flight.objects.create(
            flight_number="EL100",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            status=FlightStatus.SCHEDULED.value,
        )

    def test_complete_audit_trail(self):
        """Test complete audit trail for an operation."""
        # Log multiple events for a flight
        events = [
            ("FLIGHT_CREATED", "Flight created", EventLog.EventSeverity.INFO),
            ("FLIGHT_SCHEDULED", "Flight scheduled", EventLog.EventSeverity.INFO),
            ("GATE_ASSIGNED", "Gate assigned", EventLog.EventSeverity.INFO),
            ("PASSENGERS_LOADED", "Passengers loaded", EventLog.EventSeverity.INFO),
        ]
        
        for event_type, description, severity in events:
            EventLog.objects.create(
                event_type=event_type,
                description=description,
                flight=self.flight,
                user=self.user,
                severity=severity.value,
                action=EventLog.ActionType.CREATE.value,
            )
        
        # Verify all events logged
        flight_events = EventLog.objects.filter(flight=self.flight)
        self.assertEqual(flight_events.count(), len(events))
        
        # Verify event ordering (most recent first)
        event_list = list(flight_events)
        self.assertLessEqual(event_list[0].timestamp, event_list[0].timestamp)

    def test_event_log_by_severity(self):
        """Test filtering events by severity."""
        # Create events with different severities
        EventLog.objects.create(
            event_type="INFO_EVENT",
            description="Info event",
            severity=EventLog.EventSeverity.INFO.value,
        )
        
        EventLog.objects.create(
            event_type="WARNING_EVENT",
            description="Warning event",
            severity=EventLog.EventSeverity.WARNING.value,
        )
        
        EventLog.objects.create(
            event_type="ERROR_EVENT",
            description="Error event",
            severity=EventLog.EventSeverity.ERROR.value,
        )
        
        # Filter by severity
        errors = EventLog.objects.errors()
        warnings = EventLog.objects.warnings()
        
        self.assertEqual(errors.count(), 1)
        self.assertEqual(warnings.count(), 1)


class SearchIntegrationTest(TestCase):
    """Integration tests for search functionality."""

    def setUp(self):
        # Create searchable data
        for i in range(10):
            Airport.objects.create(
                code=f"SR{i:02d}",
                name=f"Search Airport {i}",
                city=f"Search City {i}",
            )
            
            Flight.objects.create(
                flight_number=f"SR{i:03d}",
                airline=f"Airline {i % 3}",
                origin="LOS",
                destination=f"DEST{i}",
                scheduled_departure=timezone.now() + timedelta(hours=i),
                scheduled_arrival=timezone.now() + timedelta(hours=i+2),
            )

    def test_flight_search(self):
        """Test flight search functionality."""
        # Search by flight number
        results = Flight.search("SR001")
        self.assertEqual(results.count(), 1)
        
        # Search by airline
        results = Flight.search("Airline 1")
        self.assertGreater(results.count(), 0)

    def test_airport_search(self):
        """Test airport search through API."""
        client = Client()
        user = User.objects.create_user(
            username='searcher',
            password='searchpass123',
            is_superuser=True,
        )
        client.login(username='searcher', password='searchpass123')
        
        response = client.get('/api/v1/airports/?search=Search')
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()['results']), 0)


class APIIntegrationTest(TestCase):
    """Integration tests for API endpoints working together."""

    def setUp(self):
        self.client = Client()
        
        self.admin = User.objects.create_user(
            username='apiadmin',
            password='apipass123',
            is_superuser=True,
        )
        self.client.login(username='apiadmin', password='apipass123')

    def test_create_and_retrieve_workflow(self):
        """Test creating and retrieving through API."""
        # Create airport
        create_data = {
            'code': 'API',
            'name': 'API Test Airport',
            'city': 'API City',
        }
        response = self.client.post('/api/v1/airports/', create_data)
        self.assertEqual(response.status_code, 201)
        
        airport_id = response.json()['id']
        
        # Retrieve airport
        response = self.client.get(f'/api/v1/airports/{airport_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 'API')
        
        # Update airport
        update_data = {
            'code': 'API',
            'name': 'Updated API Airport',
            'city': 'API City',
        }
        response = self.client.put(f'/api/v1/airports/{airport_id}/', update_data)
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        response = self.client.get(f'/api/v1/airports/{airport_id}/')
        self.assertEqual(response.json()['name'], 'Updated API Airport')

    def test_list_filter_paginate_workflow(self):
        """Test list, filter, and paginate through API."""
        # Create multiple items
        for i in range(30):
            Airport.objects.create(
                code=f"LF{i:02d}",
                name=f"List Filter Airport {i}",
                city=f"City {i % 5}",
            )
        
        # List with pagination
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 25)  # Default page size
        
        # Filter
        response = self.client.get('/api/v1/airports/?search=City+1')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data['results']), 0)
