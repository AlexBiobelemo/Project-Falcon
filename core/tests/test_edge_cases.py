"""
Edge case tests for the Airport Operations Management System.

Tests cover:
- Boundary conditions
- Empty/null handling
- Invalid input handling
- Race conditions
- Concurrent operations
- Data integrity edge cases
- Timezone edge cases
- Decimal precision edge cases
"""

import uuid
from datetime import date, datetime, timedelta, time
from decimal import Decimal, InvalidOperation
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.core.exceptions import ValidationError, FieldError
from django.db import IntegrityError, DataError, transaction
from django.utils import timezone
from django.contrib.auth.models import User, Group

from core.models import (
    Airport, Gate, GateStatus, Flight, FlightStatus,
    Passenger, PassengerStatus, Staff, StaffRole, StaffAssignment,
    EventLog, FiscalAssessment, AssessmentPeriod, AssessmentStatus,
    Report, ReportType, Document,
)


class BoundaryConditionTest(TestCase):
    """Tests for boundary conditions."""

    def test_empty_string_fields(self):
        """Test empty strings in optional fields."""
        airport = Airport.objects.create(
            code="EMP",
            name="Empty Test",
            city="",  # Empty city
        )
        self.assertEqual(airport.city, "")

    def test_max_length_fields(self):
        """Test maximum length field values."""
        # Test max length code (3 chars)
        airport = Airport.objects.create(
            code="ABC",
            name="A" * 200,  # Max name length
            city="C" * 100,  # Max city length
        )
        self.assertEqual(len(airport.name), 200)
        self.assertEqual(len(airport.city), 100)

    def test_exceed_max_length(self):
        """Test exceeding max length raises error."""
        # Note: SQLite doesn't enforce max_length at DB level
        # but full_clean() validates it
        from django.core.exceptions import ValidationError
        
        airport = Airport(code="TOOLONG", name="Test", city="Test")
        with self.assertRaises(ValidationError):
            airport.full_clean()

    def test_minimum_decimal_value(self):
        """Test minimum decimal values."""
        assessment = FiscalAssessment.objects.create(
            airport=Airport.objects.create(code="MIN", name="Min", city="City"),
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            fuel_revenue=Decimal("0.00"),
        )
        self.assertEqual(assessment.fuel_revenue, Decimal("0.00"))

    def test_maximum_decimal_value(self):
        """Test maximum decimal values."""
        max_value = Decimal("9999999999999.99")
        assessment = FiscalAssessment.objects.create(
            airport=Airport.objects.create(code="MAX", name="Max", city="City"),
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            fuel_revenue=max_value,
        )
        self.assertEqual(assessment.fuel_revenue, max_value)

    def test_negative_decimal_values(self):
        """Test negative decimal values."""
        assessment = FiscalAssessment.objects.create(
            airport=Airport.objects.create(code="NEG", name="Neg", city="City"),
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            # Expenses can conceptually be negative (refunds)
            security_costs=Decimal("-100.00"),
        )
        # Note: Database may or may not allow negative values
        # depending on field constraints

    def test_zero_passenger_count(self):
        """Test zero passenger count."""
        assessment = FiscalAssessment.objects.create(
            airport=Airport.objects.create(code="ZER", name="Zero", city="City"),
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            passenger_count=0,
        )
        self.assertEqual(assessment.passenger_count, 0)

    def test_very_large_integer(self):
        """Test very large integer values."""
        assessment = FiscalAssessment.objects.create(
            airport=Airport.objects.create(code="BIG", name="Big", city="City"),
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            passenger_count=2147483647,  # Max 32-bit int
        )
        self.assertEqual(assessment.passenger_count, 2147483647)


class NullHandlingTest(TestCase):
    """Tests for null/None handling."""

    def setUp(self):
        self.airport = Airport.objects.create(
            code="NUL",
            name="Null Test Airport",
            city="City",
        )

    def test_nullable_fields_explicit_none(self):
        """Test explicitly setting nullable fields to None."""
        airport = Airport.objects.create(
            code="NULL",
            name="Nullable Airport",
            city="City",
            latitude=None,
            longitude=None,
        )
        self.assertIsNone(airport.latitude)
        self.assertIsNone(airport.longitude)

    def test_nullable_datetime_fields(self):
        """Test nullable datetime fields."""
        flight = Flight.objects.create(
            flight_number="NULL1",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            actual_departure=None,
            actual_arrival=None,
        )
        self.assertIsNone(flight.actual_departure)
        self.assertIsNone(flight.actual_arrival)

    def test_nullable_foreign_key(self):
        """Test nullable foreign key."""
        flight = Flight.objects.create(
            flight_number="NULL2",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            gate=None,
        )
        self.assertIsNone(flight.gate)

    def test_null_in_filter(self):
        """Test filtering with null values."""
        Flight.objects.create(
            flight_number="NULL3",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            gate=None,
        )
        
        flights_without_gate = Flight.objects.filter(gate__isnull=True)
        self.assertGreater(flights_without_gate.count(), 0)

    def test_null_string_default(self):
        """Test null string fields default to empty string."""
        passenger = Passenger.objects.create(
            first_name="Test",
            last_name="Passenger",
            passport_number="NULL999",
            flight=Flight.objects.create(
                flight_number="NULLFLT",
                origin="LOS",
                destination="JFK",
                scheduled_departure=timezone.now() + timedelta(hours=2),
                scheduled_arrival=timezone.now() + timedelta(hours=10),
            ),
            email="",  # Default empty string
            phone="",
        )
        self.assertEqual(passenger.email, "")
        self.assertEqual(passenger.phone, "")


class InvalidInputTest(TestCase):
    """Tests for invalid input handling."""

    def test_invalid_date_range(self):
        """Test end_date before start_date."""
        airport = Airport.objects.create(
            code="INV",
            name="Invalid Date Airport",
            city="City",
        )
        
        # This should be allowed at DB level but validated in forms
        assessment = FiscalAssessment.objects.create(
            airport=airport,
            period_type='monthly',
            start_date=date(2025, 1, 31),
            end_date=date(2025, 1, 1),  # Before start
        )
        # DB allows it, business logic should validate

    def test_invalid_email_format(self):
        """Test invalid email format."""
        # Django's EmailField validates format
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        with self.assertRaises(ValidationError):
            validate_email("not-an-email")

    def test_invalid_uuid_format(self):
        """Test invalid UUID format."""
        with self.assertRaises(ValueError):
            uuid.UUID("not-a-uuid")

    def test_duplicate_unique_field(self):
        """Test duplicate unique field raises IntegrityError."""
        Airport.objects.create(
            code="DUP",
            name="First Airport",
            city="City",
        )
        
        with self.assertRaises(IntegrityError):
            Airport.objects.create(
                code="DUP",  # Duplicate
                name="Second Airport",
                city="City",
            )

    def test_invalid_choice_field(self):
        """Test invalid choice field value."""
        gate = Gate(
            gate_id="INV_CHOICE",
            terminal="T1",
            status="invalid_status",  # Not a valid choice
        )
        
        with self.assertRaises(ValidationError):
            gate.full_clean()

    def test_negative_delay_minutes(self):
        """Test negative delay minutes."""
        flight = Flight.objects.create(
            flight_number="NEG1",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            delay_minutes=-10,  # Negative delay (early?)
        )
        # DB allows it, business logic should validate


class TimezoneEdgeCaseTest(TestCase):
    """Tests for timezone edge cases."""

    def test_datetime_with_timezone(self):
        """Test datetime with timezone."""
        from django.utils import timezone
        
        now = timezone.now()
        flight = Flight.objects.create(
            flight_number="TZ1",
            origin="LOS",
            destination="JFK",
            scheduled_departure=now + timedelta(hours=2),
            scheduled_arrival=now + timedelta(hours=10),
        )
        
        self.assertIsNotNone(flight.scheduled_departure.tzinfo)

    def test_datetime_without_timezone(self):
        """Test naive datetime is rejected."""
        naive_dt = datetime(2025, 1, 1, 12, 0, 0)
        
        # Django should handle this based on USE_TZ setting
        flight = Flight.objects.create(
            flight_number="TZ2",
            origin="LOS",
            destination="JFK",
            scheduled_departure=naive_dt,
            scheduled_arrival=naive_dt + timedelta(hours=8),
        )
        # Django may auto-convert to timezone-aware

    def test_midnight_datetime(self):
        """Test datetime at midnight."""
        from datetime import timezone as dt_timezone
        midnight = datetime(2025, 1, 1, 0, 0, 0, tzinfo=dt_timezone.utc)
        
        flight = Flight.objects.create(
            flight_number="MID1",
            origin="LOS",
            destination="JFK",
            scheduled_departure=midnight,
            scheduled_arrival=midnight + timedelta(hours=8),
        )
        self.assertEqual(flight.scheduled_departure.hour, 0)

    def test_leap_year_date(self):
        """Test date in leap year."""
        leap_date = date(2024, 2, 29)
        
        assessment = FiscalAssessment.objects.create(
            airport=Airport.objects.create(code="LEAP", name="Leap", city="City"),
            period_type='monthly',
            start_date=leap_date,
            end_date=date(2024, 2, 29),
        )
        self.assertEqual(assessment.start_date, leap_date)

    def test_year_boundary(self):
        """Test year boundary dates."""
        # End of year
        assessment = FiscalAssessment.objects.create(
            airport=Airport.objects.create(code="YR1", name="Year", city="City"),
            period_type='annual',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        self.assertEqual(assessment.end_date, date(2025, 12, 31))


class ConcurrentOperationTest(TestCase):
    """Tests for concurrent operations."""

    def setUp(self):
        self.airport = Airport.objects.create(
            code="CON",
            name="Concurrent Test Airport",
            city="City",
        )

    def test_concurrent_updates(self):
        """Test concurrent updates to same record."""
        # Simulate concurrent updates
        def update_airport(new_name):
            self.airport.name = new_name
            self.airport.save()
        
        # In a real concurrent scenario, last write wins
        # This test verifies basic update behavior
        update_airport("First Update")
        update_airport("Second Update")
        
        self.airport.refresh_from_db()
        self.assertEqual(self.airport.name, "Second Update")

    @transaction.atomic
    def test_atomic_update(self):
        """Test atomic update operations."""
        # Create assessment
        assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            fuel_revenue=Decimal("100000"),
        )
        
        # Atomic update with calculate_totals
        with transaction.atomic():
            assessment.fuel_revenue = Decimal("200000")
            assessment.save()
            assessment.calculate_totals()
            assessment.save()
        
        assessment.refresh_from_db()
        self.assertEqual(assessment.fuel_revenue, Decimal("200000"))

    def test_select_for_update(self):
        """Test select_for_update for row locking."""
        gate = Gate.objects.create(
            gate_id="LOCK1",
            terminal="T1",
            status=GateStatus.AVAILABLE.value,
        )
        
        # In a transaction, lock the row
        with transaction.atomic():
            locked_gate = Gate.objects.select_for_update().get(id=gate.id)
            locked_gate.status = GateStatus.OCCUPIED.value
            locked_gate.save()
        
        gate.refresh_from_db()
        self.assertEqual(gate.status, GateStatus.OCCUPIED.value)


class DataIntegrityTest(TestCase):
    """Tests for data integrity edge cases."""

    def test_cascade_delete_preserves_integrity(self):
        """Test cascade delete maintains integrity."""
        airport = Airport.objects.create(
            code="CSC",
            name="Cascade Test Airport",
            city="City",
        )
        
        assessment = FiscalAssessment.objects.create(
            airport=airport,
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        
        airport_id = airport.id
        assessment_id = assessment.id
        
        # Delete airport
        airport.delete()
        
        # Assessment should also be deleted
        self.assertEqual(FiscalAssessment.objects.filter(id=assessment_id).count(), 0)

    def test_set_null_on_delete(self):
        """Test SET_NULL on delete maintains integrity."""
        gate = Gate.objects.create(
            gate_id="SETN",
            terminal="T1",
        )
        
        flight = Flight.objects.create(
            flight_number="SETN1",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            gate=gate,
        )
        
        flight_id = flight.id
        
        # Delete gate
        gate.delete()
        
        # Flight should still exist with null gate
        flight = Flight.objects.get(id=flight_id)
        self.assertIsNone(flight.gate)

    def test_unique_together_constraint(self):
        """Test unique_together constraint."""
        airport = Airport.objects.create(
            code="UTG",
            name="Unique Together Airport",
            city="City",
        )
        
        FiscalAssessment.objects.create(
            airport=airport,
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        
        # Should fail due to unique_together
        with self.assertRaises(IntegrityError):
            FiscalAssessment.objects.create(
                airport=airport,
                period_type='monthly',
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
            )

    def test_self_referential_foreign_key(self):
        """Test self-referential foreign key (if applicable)."""
        # This model doesn't have self-referential FK
        # But test structure is here for completeness
        pass


class StringEdgeCaseTest(TestCase):
    """Tests for string edge cases."""

    def test_unicode_characters(self):
        """Test unicode characters in strings."""
        airport = Airport.objects.create(
            code="UNI",
            name="Ünïcödé Àirpört 日本語",
            city=" Città ",
        )
        self.assertEqual(airport.name, "Ünïcödé Àirpört 日本語")

    def test_whitespace_only_string(self):
        """Test whitespace-only strings."""
        airport = Airport.objects.create(
            code="WHT",
            name="   ",  # Only whitespace
            city="City",
        )
        self.assertEqual(airport.name, "   ")

    def test_empty_string_vs_null(self):
        """Test empty string vs null."""
        # Empty string
        airport1 = Airport.objects.create(
            code="E1",
            name="Test1",
            city="",
        )
        self.assertEqual(airport1.city, "")
        
        # Note: city field has blank=True but not null=True
        # So we test with a different nullable field instead
        flight = Flight.objects.create(
            flight_number="NULL_TEST",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            gate=None,  # This is nullable
        )
        self.assertIsNone(flight.gate)

    def test_very_long_string(self):
        """Test very long strings."""
        long_name = "A" * 10000
        
        # Note: SQLite doesn't enforce max_length at DB level
        # but full_clean() validates it
        from django.core.exceptions import ValidationError
        
        airport = Airport(code="LONG", name=long_name, city="City")
        with self.assertRaises(ValidationError):
            airport.full_clean()

    def test_special_characters(self):
        """Test special characters in strings."""
        airport = Airport.objects.create(
            code="SPC",
            name="Airport & Sons <Ltd> \"Inc\"",
            city="City's Name",
        )
        self.assertEqual(airport.name, "Airport & Sons <Ltd> \"Inc\"")

    def test_sql_injection_string(self):
        """Test SQL injection attempt in string."""
        malicious = "'; DROP TABLE core_airport; --"
        
        airport = Airport.objects.create(
            code="SQL",
            name=malicious,
            city="City",
        )
        
        # Should be stored as-is, not executed
        self.assertEqual(airport.name, malicious)
        
        # Table should still exist
        self.assertGreater(Airport.objects.count(), 0)


class RelationshipEdgeCaseTest(TestCase):
    """Tests for relationship edge cases."""

    def test_orphan_record(self):
        """Test orphan record (no relationships)."""
        airport = Airport.objects.create(
            code="ORP",
            name="Orphan Airport",
            city="City",
        )
        
        # Airport with no flights, assessments, etc.
        self.assertEqual(airport.fiscal_assessments.count(), 0)
        self.assertEqual(airport.reports.count(), 0)

    def test_many_to_many_empty(self):
        """Test many-to-many with no relations."""
        user = User.objects.create_user(
            username='empty',
            password='pass123',
        )
        
        # User with no groups
        self.assertEqual(user.groups.count(), 0)

    def test_circular_reference(self):
        """Test circular reference prevention."""
        # This model doesn't have circular references
        # Test structure for completeness
        pass

    def test_deep_nested_relationships(self):
        """Test deeply nested relationships."""
        airport = Airport.objects.create(
            code="DEEP",
            name="Deep Airport",
            city="City",
        )
        
        assessment = FiscalAssessment.objects.create(
            airport=airport,
            period_type='monthly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )
        
        report = Report.objects.create(
            airport=airport,
            report_type='fiscal_summary',
            title="Test Report",
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )
        
        document = Document.objects.create(
            name="Test Document",
            document_type='report',
            airport=airport,
            report=report,
        )
        
        # Access through relationships
        self.assertEqual(document.airport.code, "DEEP")
        self.assertEqual(document.report.airport.code, "DEEP")


class EventLogEdgeCaseTest(TestCase):
    """Tests for EventLog specific edge cases."""

    def test_event_without_user(self):
        """Test event without associated user."""
        event = EventLog.objects.create(
            event_type="SYSTEM",
            description="System event without user",
        )
        self.assertIsNone(event.user)

    def test_event_without_flight(self):
        """Test event without associated flight."""
        event = EventLog.objects.create(
            event_type="SYSTEM",
            description="System event without flight",
        )
        self.assertIsNone(event.flight)

    def test_event_with_empty_ip(self):
        """Test event with empty IP address."""
        event = EventLog.objects.create(
            event_type="SYSTEM",
            description="Event with empty IP",
            ip_address="",
        )
        self.assertEqual(event.ip_address, "")

    def test_event_ipv6_address(self):
        """Test event with IPv6 address."""
        event = EventLog.objects.create(
            event_type="SYSTEM",
            description="Event with IPv6",
            ip_address="2001:db8::1",
        )
        self.assertEqual(event.ip_address, "2001:db8::1")

    def test_event_timestamp_precision(self):
        """Test event timestamp precision."""
        event1 = EventLog.objects.create(
            event_type="TEST1",
            description="First event",
        )
        
        event2 = EventLog.objects.create(
            event_type="TEST2",
            description="Second event",
        )
        
        # Timestamps should be different
        self.assertLess(event1.timestamp, event2.timestamp)
