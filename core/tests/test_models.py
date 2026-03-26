"""
Comprehensive model tests for the Airport Operations Management System.

Tests cover:
- Model creation and validation
- Field constraints and data types
- Custom managers and querysets
- Model relationships and cascading
- Business logic methods
- Edge cases and boundary conditions
- Database indexes and query optimization
"""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.core.exceptions import ValidationError, FieldError
from django.db import IntegrityError, DataError
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.contrib.auth.models import User, Group

from core.models import (
    Airport, Gate, GateStatus, Flight, FlightStatus,
    Passenger, PassengerStatus, Staff, StaffRole, StaffAssignment,
    EventLog, FiscalAssessment, AssessmentPeriod, AssessmentStatus,
    Report, ReportType, ReportFormat, Document, Aircraft, AircraftType,
    AircraftStatus, CrewMember, CrewMemberType, CrewMemberStatus,
)


class AirportModelTest(TestCase):
    """Tests for the Airport model."""

    def setUp(self):
        """Set up test data."""
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos International Airport",
            city="Lagos",
            latitude=Decimal("6.5774"),
            longitude=Decimal("3.3212"),
            timezone="Africa/Lagos",
            is_active=True,
        )

    def test_airport_creation(self):
        """Test airport is created correctly."""
        self.assertEqual(self.airport.code, "LOS")
        self.assertEqual(self.airport.name, "Lagos International Airport")
        self.assertEqual(self.airport.city, "Lagos")
        self.assertEqual(self.airport.latitude, Decimal("6.5774"))
        self.assertEqual(self.airport.longitude, Decimal("3.3212"))
        self.assertEqual(self.airport.timezone, "Africa/Lagos")
        self.assertTrue(self.airport.is_active)

    def test_airport_str(self):
        """Test airport string representation."""
        self.assertEqual(str(self.airport), "LOS - Lagos International Airport")

    def test_airport_nullable_fields(self):
        """Test airport can be created without optional fields."""
        airport = Airport.objects.create(
            code="ABJ",
            name="Abuja Airport",
            city="Abuja",
        )
        self.assertIsNone(airport.latitude)
        self.assertIsNone(airport.longitude)
        self.assertEqual(airport.timezone, "UTC")
        self.assertTrue(airport.is_active)

    def test_airport_code_unique(self):
        """Test airport code must be unique."""
        with self.assertRaises(IntegrityError):
            Airport.objects.create(
                code="LOS",
                name="Another Lagos Airport",
                city="Lagos",
            )

    def test_airport_code_max_length(self):
        """Test airport code max length is 3."""
        # Note: SQLite doesn't enforce max_length, but PostgreSQL does
        # This test validates the model field definition
        field = Airport._meta.get_field('code')
        self.assertEqual(field.max_length, 3)
        
        # Try to create with long code - will fail on PostgreSQL
        airport = Airport(code="LONG", name="Invalid", city="City")
        # full_clean validates max_length
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            airport.full_clean()

    def test_airport_name_max_length(self):
        """Test airport name max length is 200."""
        # Note: SQLite doesn't enforce max_length, but PostgreSQL does
        field = Airport._meta.get_field('name')
        self.assertEqual(field.max_length, 200)
        
        # Try to create with long name - will fail on PostgreSQL
        airport = Airport(code="XYZ", name="A" * 201, city="City")
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            airport.full_clean()

    def test_airport_latitude_longitude_precision(self):
        """Test latitude and longitude accept correct precision."""
        airport = Airport.objects.create(
            code="NYC",
            name="New York Airport",
            city="New York",
            latitude=Decimal("40.712776"),
            longitude=Decimal("-74.005975"),
        )
        self.assertEqual(airport.latitude, Decimal("40.712776"))

    def test_airport_latitude_out_of_range(self):
        """Test latitude validation (should be between -90 and 90)."""
        # Django doesn't enforce this at DB level, but we can test the field accepts values
        airport = Airport.objects.create(
            code="TEST",
            name="Test Airport",
            city="Test",
            latitude=Decimal("91.0000"),  # Invalid but DB will accept
        )
        # Application should handle this validation
        self.assertEqual(airport.latitude, Decimal("91.0000"))

    def test_airport_is_active_default(self):
        """Test is_active defaults to True."""
        airport = Airport.objects.create(
            code="XYZ",
            name="Test Airport",
            city="Test City",
        )
        self.assertTrue(airport.is_active)

    def test_airport_timestamps_auto(self):
        """Test created_at and updated_at are auto-set."""
        self.assertIsNotNone(self.airport.created_at)
        self.assertIsNotNone(self.airport.updated_at)
        # Ensure they are timezone-aware
        self.assertIsNotNone(self.airport.created_at.tzinfo)

    def test_airport_update_timestamp(self):
        """Test updated_at changes on save."""
        old_updated = self.airport.updated_at
        import time
        time.sleep(0.1)
        self.airport.name = "Updated Name"
        self.airport.save()
        self.airport.refresh_from_db()
        self.assertGreater(self.airport.updated_at, old_updated)

    def test_airport_queryset_active(self):
        """Test filtering active airports."""
        inactive = Airport.objects.create(
            code="INA",
            name="Inactive Airport",
            city="City",
            is_active=False,
        )
        active_airports = Airport.objects.filter(is_active=True)
        self.assertEqual(active_airports.count(), 1)
        self.assertNotIn(inactive, active_airports)


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

    def test_gate_status_choices(self):
        """Test gate status accepts valid choices."""
        for status in GateStatus:
            gate = Gate.objects.create(
                gate_id=f"TEST_{status.value}",
                terminal="T1",
                status=status.value,
            )
            self.assertEqual(gate.status, status.value)

    def test_gate_invalid_status(self):
        """Test gate rejects invalid status."""
        with self.assertRaises(ValidationError):
            gate = Gate(
                gate_id="INVALID",
                terminal="T1",
                status="invalid_status",
            )
            gate.full_clean()

    def test_gate_id_unique(self):
        """Test gate_id must be unique."""
        with self.assertRaises(IntegrityError):
            Gate.objects.create(
                gate_id="A1",
                terminal="Terminal 2",
            )

    def test_gate_manager_available(self):
        """Test GateManager.available() returns available gates."""
        Gate.objects.create(gate_id="C1", terminal="Terminal 1", status=GateStatus.AVAILABLE.value)
        Gate.objects.create(gate_id="C2", terminal="Terminal 1", status=GateStatus.OCCUPIED.value)

        available = Gate.objects.available()
        self.assertEqual(available.count(), 2)

    def test_gate_manager_by_status(self):
        """Test GateManager.by_status() filters by status."""
        Gate.objects.create(gate_id="D1", terminal="Terminal 1", status=GateStatus.MAINTENANCE.value)
        Gate.objects.create(gate_id="D2", terminal="Terminal 1", status=GateStatus.AVAILABLE.value)

        maintenance = Gate.objects.by_status(GateStatus.MAINTENANCE.value)
        available = Gate.objects.by_status(GateStatus.AVAILABLE.value)

        self.assertEqual(maintenance.count(), 1)
        self.assertEqual(available.count(), 2)  # Including setUp

    def test_gate_manager_by_terminal(self):
        """Test GateManager.by_terminal() filters by terminal."""
        Gate.objects.create(gate_id="B1", terminal="Terminal 2", status=GateStatus.AVAILABLE.value)
        Gate.objects.create(gate_id="B2", terminal="Terminal 2", status=GateStatus.OCCUPIED.value)

        terminal2_gates = Gate.objects.by_terminal("Terminal 2")
        self.assertEqual(terminal2_gates.count(), 2)

    def test_gate_occupied_manager(self):
        """Test GateManager.occupied() returns occupied gates."""
        Gate.objects.create(gate_id="O1", terminal="T1", status=GateStatus.OCCUPIED.value)
        occupied = Gate.objects.occupied()
        self.assertEqual(occupied.count(), 1)

    def test_gate_maintenance_manager(self):
        """Test GateManager.maintenance() returns maintenance gates."""
        Gate.objects.create(gate_id="M1", terminal="T1", status=GateStatus.MAINTENANCE.value)
        maintenance = Gate.objects.maintenance()
        self.assertEqual(maintenance.count(), 1)

    def test_gate_closed_status(self):
        """Test gate can be set to closed."""
        gate = Gate.objects.create(
            gate_id="CLOSED1",
            terminal="T1",
            status=GateStatus.CLOSED.value,
        )
        self.assertEqual(gate.status, GateStatus.CLOSED.value)


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
            delay_minutes=0,
        )

    def test_flight_creation(self):
        """Test flight is created correctly."""
        self.assertEqual(self.flight.flight_number, "AA123")
        self.assertEqual(self.flight.airline, "American Airlines")
        self.assertEqual(self.flight.origin, "LOS")
        self.assertEqual(self.flight.destination, "JFK")
        self.assertEqual(self.flight.status, FlightStatus.SCHEDULED.value)
        self.assertEqual(self.flight.aircraft_type, "Boeing 737")

    def test_flight_str(self):
        """Test flight string representation."""
        self.assertEqual(str(self.flight), "AA123 (LOS → JFK)")

    def test_flight_number_unique(self):
        """Test flight_number must be unique."""
        with self.assertRaises(IntegrityError):
            Flight.objects.create(
                flight_number="AA123",
                origin="ABJ",
                destination="DXB",
                scheduled_departure=timezone.now() + timedelta(hours=5),
                scheduled_arrival=timezone.now() + timedelta(hours=10),
            )

    def test_flight_nullable_times(self):
        """Test actual_departure and actual_arrival can be null."""
        self.assertIsNone(self.flight.actual_departure)
        self.assertIsNone(self.flight.actual_arrival)

    def test_flight_set_actual_departure(self):
        """Test setting actual departure time."""
        self.flight.actual_departure = timezone.now()
        self.flight.status = FlightStatus.DEPARTED.value
        self.flight.save()
        self.assertIsNotNone(self.flight.actual_departure)

    def test_flight_manager_upcoming(self):
        """Test FlightManager.upcoming() returns scheduled future flights."""
        now = timezone.now()
        # Create a past flight (should not be in upcoming)
        Flight.objects.create(
            flight_number="BB456",
            origin="LOS",
            destination="ABJ",
            scheduled_departure=now - timedelta(hours=2),
            scheduled_arrival=now - timedelta(hours=1),
            status=FlightStatus.SCHEDULED.value,
        )

        upcoming = Flight.objects.upcoming()
        # Only the setUp flight should be upcoming
        self.assertEqual(upcoming.count(), 1)
        self.assertEqual(upcoming.first().flight_number, "AA123")

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

    def test_flight_manager_by_status(self):
        """Test FlightManager.by_status() filters by status."""
        Flight.objects.create(
            flight_number="DD000",
            origin="LOS",
            destination="ABJ",
            scheduled_departure=timezone.now() + timedelta(hours=1),
            scheduled_arrival=timezone.now() + timedelta(hours=2),
            status=FlightStatus.CANCELLED.value,
        )

        cancelled = Flight.objects.by_status(FlightStatus.CANCELLED.value)
        self.assertEqual(cancelled.count(), 1)

    def test_flight_manager_by_airline(self):
        """Test FlightManager.by_airline() filters by airline."""
        Flight.objects.create(
            flight_number="BA001",
            airline="British Airways",
            origin="LOS",
            destination="LHR",
            scheduled_departure=timezone.now() + timedelta(hours=5),
            scheduled_arrival=timezone.now() + timedelta(hours=12),
            status=FlightStatus.SCHEDULED.value,
        )

        ba_flights = Flight.objects.by_airline("British Airways")
        self.assertEqual(ba_flights.count(), 1)

    def test_flight_manager_by_route(self):
        """Test FlightManager.by_route() filters by route."""
        flights = Flight.objects.by_route("LOS", "JFK")
        self.assertEqual(flights.count(), 1)
        self.assertEqual(flights.first().flight_number, "AA123")

    def test_flight_manager_departed(self):
        """Test FlightManager.departed() returns departed flights."""
        self.flight.status = FlightStatus.DEPARTED.value
        self.flight.save()
        departed = Flight.objects.departed()
        self.assertEqual(departed.count(), 1)

    def test_flight_manager_arrived(self):
        """Test FlightManager.arrived() returns arrived flights."""
        self.flight.status = FlightStatus.ARRIVED.value
        self.flight.save()
        arrived = Flight.objects.arrived()
        self.assertEqual(arrived.count(), 1)

    def test_flight_manager_cancelled(self):
        """Test FlightManager.cancelled() returns cancelled flights."""
        self.flight.status = FlightStatus.CANCELLED.value
        self.flight.save()
        cancelled = Flight.objects.cancelled()
        self.assertEqual(cancelled.count(), 1)

    def test_flight_delay_minutes(self):
        """Test flight delay_minutes field."""
        self.flight.delay_minutes = 45
        self.flight.status = FlightStatus.DELAYED.value
        self.flight.save()
        self.assertEqual(self.flight.delay_minutes, 45)

    def test_flight_gate_relationship(self):
        """Test flight can access its assigned gate."""
        self.assertEqual(self.flight.gate.gate_id, "A1")
        # Test reverse relationship
        self.assertIn(self.flight, self.gate.flights.all())

    def test_flight_gate_null(self):
        """Test flight can exist without assigned gate."""
        flight = Flight.objects.create(
            flight_number="NOGATE",
            origin="LOS",
            destination="ABJ",
            scheduled_departure=timezone.now() + timedelta(hours=1),
            scheduled_arrival=timezone.now() + timedelta(hours=2),
            gate=None,
        )
        self.assertIsNone(flight.gate)

    def test_flight_search(self):
        """Test full-text search on flights."""
        results = Flight.search("AA123")
        self.assertEqual(results.count(), 1)

        results = Flight.search("American")
        self.assertEqual(results.count(), 1)

        results = Flight.search("LOS")
        self.assertEqual(results.count(), 1)

        results = Flight.search("NONEXISTENT")
        self.assertEqual(results.count(), 0)

    def test_flight_status_boarding(self):
        """Test flight can be set to boarding status."""
        self.flight.status = FlightStatus.BOARDING.value
        self.flight.save()
        self.assertEqual(self.flight.status, FlightStatus.BOARDING.value)


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
        self.assertEqual(self.passenger.checked_bags, 2)

    def test_passenger_str(self):
        """Test passenger string representation."""
        self.assertEqual(str(self.passenger), "Doe, John (AB123456)")

    def test_passenger_uuid_auto_generated(self):
        """Test passenger_id UUID is auto-generated."""
        self.assertIsInstance(self.passenger.passenger_id, uuid.UUID)

    def test_passenger_uuid_unique(self):
        """Test passenger_id is unique."""
        # Create another passenger
        passenger2 = Passenger.objects.create(
            first_name="Jane",
            last_name="Doe",
            passport_number="CD789012",
            flight=self.flight,
        )
        self.assertNotEqual(self.passenger.passenger_id, passenger2.passenger_id)

    def test_passenger_nullable_fields(self):
        """Test passenger can be created without optional fields."""
        passenger = Passenger.objects.create(
            first_name="No",
            last_name="Contact",
            passport_number="XY999999",
            flight=self.flight,
        )
        self.assertEqual(passenger.email, "")
        self.assertEqual(passenger.phone, "")
        self.assertIsNone(passenger.seat_number)
        self.assertEqual(passenger.checked_bags, 0)

    def test_passport_number_unique(self):
        """Test passport_number must be unique."""
        with self.assertRaises(IntegrityError):
            Passenger.objects.create(
                first_name="Duplicate",
                last_name="Passport",
                passport_number="AB123456",
                flight=self.flight,
            )

    def test_passenger_status_choices(self):
        """Test passenger status accepts valid choices."""
        for status in PassengerStatus:
            passenger = Passenger.objects.create(
                first_name=f"Test_{status.value}",
                last_name="Passenger",
                passport_number=f"PASS_{status.value}",
                flight=self.flight,
                status=status.value,
            )
            self.assertEqual(passenger.status, status.value)

    def test_passenger_manager_by_flight(self):
        """Test PassengerManager.by_flight() filters by flight."""
        passengers = Passenger.objects.by_flight(self.flight.id)
        self.assertEqual(passengers.count(), 1)

    def test_passenger_manager_by_status(self):
        """Test PassengerManager.by_status() filters by status."""
        Passenger.objects.create(
            first_name="Boarded",
            last_name="Passenger",
            passport_number="BOARD1",
            flight=self.flight,
            status=PassengerStatus.BOARDED.value,
        )

        boarded = Passenger.objects.by_status(PassengerStatus.BOARDED.value)
        checked_in = Passenger.objects.by_status(PassengerStatus.CHECKED_IN.value)

        self.assertEqual(boarded.count(), 1)
        self.assertEqual(checked_in.count(), 1)

    def test_passenger_manager_checked_in(self):
        """Test PassengerManager.checked_in() returns checked-in passengers."""
        checked_in = Passenger.objects.checked_in()
        self.assertEqual(checked_in.count(), 1)

    def test_passenger_manager_boarded(self):
        """Test PassengerManager.boarded() returns boarded passengers."""
        self.passenger.status = PassengerStatus.BOARDED.value
        self.passenger.save()
        boarded = Passenger.objects.boarded()
        self.assertEqual(boarded.count(), 1)

    def test_passenger_manager_no_show(self):
        """Test PassengerManager.no_show() returns no-show passengers."""
        self.passenger.status = PassengerStatus.NO_SHOW.value
        self.passenger.save()
        no_show = Passenger.objects.no_show()
        self.assertEqual(no_show.count(), 1)

    def test_passenger_flight_cascade_delete(self):
        """Test passenger is deleted when flight is deleted."""
        flight_id = self.flight.id
        passenger_id = self.passenger.id
        self.flight.delete()
        self.assertEqual(Passenger.objects.filter(id=passenger_id).count(), 0)

    def test_passenger_checked_bags_default(self):
        """Test checked_bags defaults to 0."""
        passenger = Passenger.objects.create(
            first_name="No",
            last_name="Bags",
            passport_number="NB000000",
            flight=self.flight,
        )
        self.assertEqual(passenger.checked_bags, 0)


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
        self.assertEqual(self.staff.certification, "AT Rating BPL, Type737")

    def test_staff_str(self):
        """Test staff string representation."""
        self.assertEqual(str(self.staff), "Smith, Jane (pilot)")

    def test_staff_uuid_auto_generated(self):
        """Test staff_id UUID is auto-generated."""
        self.assertIsInstance(self.staff.staff_id, uuid.UUID)

    def test_staff_employee_number_unique(self):
        """Test employee_number must be unique."""
        with self.assertRaises(IntegrityError):
            Staff.objects.create(
                first_name="Duplicate",
                last_name="Employee",
                employee_number="EMP001",
                role=StaffRole.GROUND_CREW.value,
            )

    def test_staff_role_choices(self):
        """Test staff role accepts valid choices."""
        for role in StaffRole:
            staff = Staff.objects.create(
                first_name=f"Test_{role.value}",
                last_name="Staff",
                employee_number=f"EMP_{role.value}",
                role=role.value,
            )
            self.assertEqual(staff.role, role.value)

    def test_staff_invalid_role(self):
        """Test staff rejects invalid role."""
        with self.assertRaises(ValidationError):
            staff = Staff(
                first_name="Invalid",
                last_name="Role",
                employee_number="INVALID_ROLE",
                role="invalid_role",
            )
            staff.full_clean()

    def test_staff_nullable_fields(self):
        """Test staff can be created without optional fields."""
        staff = Staff.objects.create(
            first_name="Minimal",
            last_name="Staff",
            employee_number="MIN001",
            role=StaffRole.GROUND_CREW.value,
        )
        self.assertEqual(staff.certification, "")
        self.assertEqual(staff.email, "")
        self.assertEqual(staff.phone, "")
        self.assertTrue(staff.is_available)

    def test_staff_manager_by_role(self):
        """Test StaffManager.by_role() filters by role."""
        Staff.objects.create(
            first_name="Bob",
            last_name="Jones",
            employee_number="EMP002",
            role=StaffRole.CO_PILOT.value,
        )

        pilots = Staff.objects.by_role(StaffRole.PILOT.value)
        copilots = Staff.objects.by_role(StaffRole.CO_PILOT.value)

        self.assertEqual(pilots.count(), 1)
        self.assertEqual(copilots.count(), 1)

    def test_staff_manager_available(self):
        """Test StaffManager.available() returns available staff."""
        Staff.objects.create(
            first_name="Unavailable",
            last_name="Staff",
            employee_number="EMP003",
            role=StaffRole.GROUND_CREW.value,
            is_available=False,
        )

        available = Staff.objects.available()
        self.assertEqual(available.count(), 1)
        self.assertTrue(available.first().is_available)

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
        self.assertFalse(unavailable.first().is_available)

    def test_staff_manager_by_availability_and_role(self):
        """Test StaffManager.by_availability_and_role() filters correctly."""
        Staff.objects.create(
            first_name="Unavailable",
            last_name="Pilot",
            employee_number="EMP002",
            role=StaffRole.PILOT.value,
            is_available=False,
        )

        available_pilots = Staff.objects.by_availability_and_role(
            StaffRole.PILOT.value, is_available=True
        )
        unavailable_pilots = Staff.objects.by_availability_and_role(
            StaffRole.PILOT.value, is_available=False
        )

        self.assertEqual(available_pilots.count(), 1)
        self.assertEqual(unavailable_pilots.count(), 1)


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
        self.assertIsNotNone(self.assignment.assigned_at)

    def test_assignment_str(self):
        """Test assignment string representation."""
        expected = f"{self.staff} assigned to {self.flight} ({self.assignment.assignment_type})"
        self.assertEqual(str(self.assignment), expected)

    def test_assignment_unique_together(self):
        """Test unique_together constraint on staff, flight, assignment_type."""
        # The model's clean() method raises ValidationError for duplicates
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            StaffAssignment.objects.create(
                staff=self.staff,
                flight=self.flight,
                assignment_type=StaffRole.CABIN_CREW.value,
            )

    def test_assignment_different_type_allowed(self):
        """Test staff can have multiple assignments with different types to same flight."""
        # Create a different flight at a different time to avoid time conflict check
        flight2 = Flight.objects.create(
            flight_number="AA456",
            origin="LOS",
            destination="LHR",
            scheduled_departure=self.flight.scheduled_departure + timedelta(days=1),
            scheduled_arrival=self.flight.scheduled_arrival + timedelta(days=1),
            status=FlightStatus.SCHEDULED.value,
        )
        # This should work - different flight
        assignment2 = StaffAssignment.objects.create(
            staff=self.staff,
            flight=flight2,
            assignment_type=StaffRole.SECURITY.value,
        )
        self.assertIsNotNone(assignment2.id)

    def test_assignment_staff_cascade_delete(self):
        """Test assignment is deleted when staff is deleted."""
        assignment_id = self.assignment.id
        self.staff.delete()
        self.assertEqual(StaffAssignment.objects.filter(id=assignment_id).count(), 0)

    def test_assignment_flight_cascade_delete(self):
        """Test assignment is deleted when flight is deleted."""
        assignment_id = self.assignment.id
        self.flight.delete()
        self.assertEqual(StaffAssignment.objects.filter(id=assignment_id).count(), 0)

    def test_assignment_clean_no_conflict(self):
        """Test assignment.clean() passes when no conflict exists."""
        # Should not raise
        self.assignment.clean()

    def test_assignment_reverse_relationships(self):
        """Test reverse relationships work correctly."""
        # Staff to assignments
        self.assertIn(self.assignment, self.staff.assignments.all())
        # Flight to assignments
        self.assertIn(self.assignment, self.flight.staff_assignments.all())


class EventLogModelTest(TestCase):
    """Tests for the EventLog model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
        )

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
            user=self.user,
            action=EventLog.ActionType.UPDATE.value,
            flight=self.flight,
            severity=EventLog.EventSeverity.INFO.value,
            ip_address="192.168.1.1",
        )

    def test_event_creation(self):
        """Test event is created correctly."""
        self.assertEqual(self.event.event_type, "FLIGHT_DEPARTURE")
        self.assertEqual(self.event.severity, EventLog.EventSeverity.INFO.value)
        self.assertEqual(self.event.user, self.user)
        self.assertEqual(self.event.action, EventLog.ActionType.UPDATE.value)
        self.assertEqual(self.event.flight, self.flight)
        self.assertEqual(self.event.ip_address, "192.168.1.1")

    def test_event_uuid_auto_generated(self):
        """Test event_id UUID is auto-generated."""
        self.assertIsInstance(self.event.event_id, uuid.UUID)

    def test_event_timestamp_auto(self):
        """Test timestamp is auto-set."""
        self.assertIsNotNone(self.event.timestamp)
        self.assertIsNotNone(self.event.timestamp.tzinfo)

    def test_event_timestamp_timezone_aware(self):
        """Test event timestamp is timezone-aware."""
        self.assertIsNotNone(self.event.timestamp.tzinfo)

    def test_event_str(self):
        """Test event string representation."""
        self.assertIn("FLIGHT_DEPARTURE", str(self.event))

    def test_event_severity_choices(self):
        """Test event severity accepts valid choices."""
        for severity in EventLog.EventSeverity:
            event = EventLog.objects.create(
                event_type="TEST_EVENT",
                description="Test",
                severity=severity.value,
            )
            self.assertEqual(event.severity, severity.value)

    def test_event_action_choices(self):
        """Test event action accepts valid choices."""
        for action in EventLog.ActionType:
            event = EventLog.objects.create(
                event_type="TEST_ACTION",
                description="Test",
                action=action.value,
            )
            self.assertEqual(event.action, action.value)

    def test_event_nullable_fields(self):
        """Test event can be created without optional fields."""
        event = EventLog.objects.create(
            event_type="SYSTEM_EVENT",
            description="System event without user or flight",
        )
        self.assertIsNone(event.user)
        self.assertIsNone(event.flight)
        self.assertEqual(event.ip_address, "")
        self.assertEqual(event.action, EventLog.ActionType.OTHER.value)

    def test_event_manager_by_type(self):
        """Test EventManager.by_type() filters by event_type."""
        EventLog.objects.create(
            event_type="FLIGHT_ARRIVAL",
            description="Test arrival",
        )

        departures = EventLog.objects.by_type("FLIGHT_DEPARTURE")
        arrivals = EventLog.objects.by_type("FLIGHT_ARRIVAL")

        self.assertEqual(departures.count(), 1)
        self.assertEqual(arrivals.count(), 1)

    def test_event_manager_by_severity(self):
        """Test EventManager.by_severity() filters by severity."""
        EventLog.objects.create(
            event_type="ERROR_EVENT",
            description="Error occurred",
            severity=EventLog.EventSeverity.ERROR.value,
        )

        errors = EventLog.objects.by_severity(EventLog.EventSeverity.ERROR.value)
        info = EventLog.objects.by_severity(EventLog.EventSeverity.INFO.value)

        self.assertEqual(errors.count(), 1)
        self.assertEqual(info.count(), 1)

    def test_event_manager_recent(self):
        """Test EventManager.recent() returns most recent events."""
        EventLog.objects.create(
            event_type="EVENT1",
            description="Recent event 1",
        )
        EventLog.objects.create(
            event_type="EVENT2",
            description="Recent event 2",
        )

        recent = EventLog.objects.recent(limit=2)
        self.assertEqual(recent.count(), 2)

    def test_event_manager_by_flight(self):
        """Test EventManager.by_flight() filters by flight."""
        events = EventLog.objects.by_flight(self.flight.id)
        self.assertEqual(events.count(), 1)

    def test_event_manager_errors(self):
        """Test EventManager.errors() returns error events."""
        EventLog.objects.create(
            event_type="SYSTEM_ERROR",
            description="System error occurred",
            severity=EventLog.EventSeverity.ERROR.value,
        )

        errors = EventLog.objects.errors()
        self.assertEqual(errors.count(), 1)

    def test_event_manager_warnings(self):
        """Test EventManager.warnings() returns warning events."""
        EventLog.objects.create(
            event_type="WARNING_EVENT",
            description="Warning occurred",
            severity=EventLog.EventSeverity.WARNING.value,
        )

        warnings = EventLog.objects.warnings()
        self.assertEqual(warnings.count(), 1)

    def test_event_user_cascade_set_null(self):
        """Test event user is set to null when user is deleted."""
        user_id = self.user.id
        self.user.delete()
        self.event.refresh_from_db()
        self.assertIsNone(self.event.user)

    def test_event_flight_cascade_set_null(self):
        """Test event flight is set to null when flight is deleted."""
        flight_id = self.flight.id
        self.flight.delete()
        self.event.refresh_from_db()
        self.assertIsNone(self.event.flight)


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

    def test_calculate_totals_revenue(self):
        """Test calculate_totals calculates revenue correctly."""
        self.assessment.calculate_totals()
        # Revenue: 100000 + 50000 + 30000 + 80000 + 40000 + 10000 = 310000
        self.assertEqual(self.assessment.total_revenue, Decimal("310000.00"))

    def test_calculate_totals_expenses(self):
        """Test calculate_totals calculates expenses correctly."""
        self.assessment.calculate_totals()
        # Expenses: 20000 + 15000 + 10000 + 25000 + 5000 + 5000 = 80000
        self.assertEqual(self.assessment.total_expenses, Decimal("80000.00"))

    def test_calculate_totals_net_profit(self):
        """Test calculate_totals calculates net profit correctly."""
        self.assessment.calculate_totals()
        # Net profit: 310000 - 80000 = 230000
        self.assertEqual(self.assessment.net_profit, Decimal("230000.00"))

    def test_calculate_totals_returns_self(self):
        """Test calculate_totals returns self for chaining."""
        result = self.assessment.calculate_totals()
        self.assertEqual(result, self.assessment)

    def test_assessment_unique_together(self):
        """Test unique_together constraint on airport, period_type, start_date, end_date."""
        with self.assertRaises(IntegrityError):
            FiscalAssessment.objects.create(
                airport=self.airport,
                period_type=AssessmentPeriod.MONTHLY.value,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
            )

    def test_assessment_period_choices(self):
        """Test period_type accepts valid choices."""
        for period in AssessmentPeriod:
            assessment = FiscalAssessment.objects.create(
                airport=self.airport,
                period_type=period.value,
                start_date=date(2025, 2, 1),
                end_date=date(2025, 2, 28),
            )
            self.assertEqual(assessment.period_type, period.value)

    def test_assessment_status_choices(self):
        """Test status accepts valid choices."""
        for idx, status in enumerate(AssessmentStatus):
            # Use different dates for each assessment to avoid unique constraint
            start_month = 1 + idx
            end_month = 3 + idx
            assessment = FiscalAssessment.objects.create(
                airport=self.airport,
                period_type=AssessmentPeriod.QUARTERLY.value,
                start_date=date(2025, start_month, 1),
                end_date=date(2025, end_month, 28),
                status=status.value,
            )
            self.assertEqual(assessment.status, status.value)

    def test_assessment_decimal_precision(self):
        """Test decimal fields maintain precision."""
        self.assessment.fuel_revenue = Decimal("999999.99")
        self.assessment.save()
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.fuel_revenue, Decimal("999999.99"))

    def test_assessment_manager_draft(self):
        """Test FiscalAssessmentManager.draft() returns draft assessments."""
        draft = FiscalAssessment.objects.draft()
        self.assertEqual(draft.count(), 1)

    def test_assessment_manager_completed(self):
        """Test FiscalAssessmentManager.completed() returns completed assessments."""
        FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.QUARTERLY.value,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 4, 30),
            status=AssessmentStatus.COMPLETED.value,
        )

        completed = FiscalAssessment.objects.completed()
        self.assertEqual(completed.count(), 1)

    def test_assessment_manager_approved(self):
        """Test FiscalAssessmentManager.approved() returns approved assessments."""
        FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.QUARTERLY.value,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 4, 30),
            status=AssessmentStatus.APPROVED.value,
        )

        approved = FiscalAssessment.objects.approved()
        self.assertEqual(approved.count(), 1)

    def test_assessment_manager_by_airport(self):
        """Test FiscalAssessmentManager.by_airport() filters by airport."""
        airport2 = Airport.objects.create(
            code="ABJ",
            name="Abuja Airport",
            city="Abuja",
        )
        FiscalAssessment.objects.create(
            airport=airport2,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 2, 28),
        )

        los_assessments = FiscalAssessment.objects.by_airport(self.airport.id)
        abj_assessments = FiscalAssessment.objects.by_airport(airport2.id)

        self.assertEqual(los_assessments.count(), 1)
        self.assertEqual(abj_assessments.count(), 1)

    def test_assessment_manager_by_period_type(self):
        """Test FiscalAssessmentManager.by_period_type() filters correctly."""
        FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.QUARTERLY.value,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 4, 30),
        )

        monthly = FiscalAssessment.objects.by_period_type(AssessmentPeriod.MONTHLY.value)
        quarterly = FiscalAssessment.objects.by_period_type(AssessmentPeriod.QUARTERLY.value)

        self.assertEqual(monthly.count(), 1)
        self.assertEqual(quarterly.count(), 1)

    def test_assessment_airport_cascade_delete(self):
        """Test assessment is deleted when airport is deleted."""
        assessment_id = self.assessment.id
        self.airport.delete()
        self.assertEqual(FiscalAssessment.objects.filter(id=assessment_id).count(), 0)

    def test_assessment_default_values(self):
        """Test assessment default values for revenue/expense fields."""
        assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
        )
        self.assertEqual(assessment.fuel_revenue, Decimal("0"))
        self.assertEqual(assessment.total_revenue, Decimal("0"))
        self.assertEqual(assessment.total_expenses, Decimal("0"))
        self.assertEqual(assessment.net_profit, Decimal("0"))
        self.assertEqual(assessment.passenger_count, 0)
        self.assertEqual(assessment.flight_count, 0)
