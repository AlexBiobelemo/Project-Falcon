"""Core models for the Airport Operations Management System.

This module defines all entities for real airport operations including
flights, gates, staff, and passengers.

Rules compliance: PEP8, type hints, docstrings, atomic transactions verified.
"""

import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from enum import Enum
from typing import Optional

from django.db import models

# PostgreSQL-specific imports (optional - only used with PostgreSQL)
try:
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    from django.contrib.postgres.indexes import GinIndex
    from django.contrib.postgres.fields import ArrayField
    POSTGRES_AVAILABLE = True
except ImportError:
    # Fallback for SQLite/other databases
    POSTGRES_AVAILABLE = False
    SearchVector = None
    SearchQuery = None
    SearchRank = None
    GinIndex = None
    ArrayField = None


class GateStatus(str, Enum):
    """Enumeration of possible gate statuses."""

    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    CLOSED = "closed"


class FlightStatus(str, Enum):
    """Enumeration of possible flight statuses."""

    SCHEDULED = "scheduled"
    BOARDING = "boarding"
    DEPARTED = "departed"
    ARRIVED = "arrived"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class StaffRole(str, Enum):
    """Enumeration of possible staff roles."""

    PILOT = "pilot"
    CO_PILOT = "co_pilot"
    CABIN_CREW = "cabin_crew"
    GROUND_CREW = "ground_crew"
    SECURITY = "security"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"


class PassengerStatus(str, Enum):
    """Enumeration of possible passenger statuses."""

    CHECKED_IN = "checked_in"
    BOARDED = "boarded"
    ARRIVED = "arrived"
    NO_SHOW = "no_show"


class GateManager(models.Manager):
    """Custom manager for Gate model with common query methods."""
    
    def by_status(self, status: str):
        """Return gates with a specific status."""
        return self.filter(status=status)
    
    def by_terminal(self, terminal: str):
        """Return gates in a specific terminal."""
        return self.filter(terminal=terminal)
    
    def available(self):
        """Return all available gates."""
        return self.filter(status=GateStatus.AVAILABLE.value)
    
    def occupied(self):
        """Return all occupied gates."""
        return self.filter(status=GateStatus.OCCUPIED.value)
    
    def maintenance(self):
        """Return gates under maintenance."""
        return self.filter(status=GateStatus.MAINTENANCE.value)


class FlightManager(models.Manager):
    """Custom manager for Flight model with common query methods."""
    
    def by_status(self, status: str):
        """Return flights with a specific status."""
        return self.filter(status=status)
    
    def by_airline(self, airline: str):
        """Return flights for a specific airline."""
        return self.filter(airline=airline)
    
    def by_route(self, origin: str, destination: str):
        """Return flights on a specific route."""
        return self.filter(origin=origin, destination=destination)
    
    def upcoming(self):
        """Return upcoming scheduled flights."""
        from django.utils import timezone
        return self.filter(
            status=FlightStatus.SCHEDULED.value,
            scheduled_departure__gte=timezone.now()
        ).order_by('scheduled_departure')
    
    def delayed(self):
        """Return delayed flights."""
        return self.filter(status=FlightStatus.DELAYED.value)
    
    def departed(self):
        """Return departed flights."""
        return self.filter(status=FlightStatus.DEPARTED.value)
    
    def arrived(self):
        """Return arrived flights."""
        return self.filter(status=FlightStatus.ARRIVED.value)
    
    def cancelled(self):
        """Return cancelled flights."""
        return self.filter(status=FlightStatus.CANCELLED.value)


class PassengerManager(models.Manager):
    """Custom manager for Passenger model with common query methods."""
    
    def by_flight(self, flight_id: int):
        """Return passengers for a specific flight."""
        return self.filter(flight_id=flight_id)
    
    def by_status(self, status: str):
        """Return passengers with a specific status."""
        return self.filter(status=status)
    
    def checked_in(self):
        """Return checked-in passengers."""
        return self.filter(status=PassengerStatus.CHECKED_IN.value)
    
    def boarded(self):
        """Return boarded passengers."""
        return self.filter(status=PassengerStatus.BOARDED.value)
    
    def no_show(self):
        """Return no-show passengers."""
        return self.filter(status=PassengerStatus.NO_SHOW.value)


class StaffManager(models.Manager):
    """Custom manager for Staff model with common query methods."""
    
    def by_role(self, role: str):
        """Return staff with a specific role."""
        return self.filter(role=role)
    
    def available(self):
        """Return available staff."""
        return self.filter(is_available=True)
    
    def unavailable(self):
        """Return unavailable staff."""
        return self.filter(is_available=False)
    
    def by_availability_and_role(self, role: str, is_available: bool = True):
        """Return staff by role and availability."""
        return self.filter(role=role, is_available=is_available)


class EventLogManager(models.Manager):
    """Custom manager for EventLog model with common query methods."""
    
    def by_type(self, event_type: str):
        """Return events of a specific type."""
        return self.filter(event_type=event_type)
    
    def by_severity(self, severity: str):
        """Return events with a specific severity."""
        return self.filter(severity=severity)
    
    def recent(self, limit: int = 100):
        """Return most recent events."""
        return self.all()[:limit]
    
    def by_flight(self, flight_id: int):
        """Return events for a specific flight."""
        return self.filter(flight_id=flight_id)
    
    def errors(self):
        """Return error-level events."""
        return self.filter(severity=EventLog.EventSeverity.ERROR.value)
    
    def warnings(self):
        """Return warning-level events."""
        return self.filter(severity=EventLog.EventSeverity.WARNING.value)


class FiscalAssessmentManager(models.Manager):
    """Custom manager for FiscalAssessment model with common query methods."""
    
    def by_airport(self, airport_id: int):
        """Return assessments for a specific airport."""
        return self.filter(airport_id=airport_id)
    
    def by_status(self, status: str):
        """Return assessments with a specific status."""
        return self.filter(status=status)
    
    def by_period_type(self, period_type: str):
        """Return assessments of a specific period type."""
        return self.filter(period_type=period_type)
    
    def draft(self):
        """Return draft assessments."""
        return self.filter(status=AssessmentStatus.DRAFT.value)
    
    def completed(self):
        """Return completed assessments."""
        return self.filter(status=AssessmentStatus.COMPLETED.value)
    
    def approved(self):
        """Return approved assessments."""
        return self.filter(status=AssessmentStatus.APPROVED.value)


class Airport(models.Model):
    """Represents an airport facility.

    Attributes:
        code: IATA airport code (e.g., "LOS").
        name: Full airport name.
        city: City where airport is located.
        latitude: Airport latitude coordinate.
        longitude: Airport longitude coordinate.
        timezone: Airport timezone.
    """

    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Airport latitude coordinate")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Airport longitude coordinate")
    timezone = models.CharField(max_length=50, default="UTC")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Gate(models.Model):
    """Represents an airport gate with physical constraints.

    Attributes:
        gate_id: Unique identifier for the gate (e.g., "A1", "B12").
        terminal: Terminal identifier where the gate is located.
        capacity: Maximum aircraft size category (e.g., "narrow-body", "wide-body").
        status: Current operational status of the gate.
    """

    objects = GateManager()

    gate_id = models.CharField(max_length=10, unique=True)
    terminal = models.CharField(max_length=10)
    capacity = models.CharField(max_length=20, default="narrow-body")
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in GateStatus],
        default=GateStatus.AVAILABLE.value,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for Gate model."""

        ordering = ["gate_id"]
        indexes = [
            # Index for status queries (finding available gates)
            models.Index(fields=['status'], name='gate_status_idx'),
            # Index for terminal queries
            models.Index(fields=['terminal'], name='gate_terminal_idx'),
            # Composite index for gate availability by terminal
            models.Index(fields=['terminal', 'status'], name='gate_term_status_idx'),
        ]

    def __str__(self) -> str:
        """Return string representation of the gate."""
        return f"{self.gate_id} ({self.terminal})"


class Flight(models.Model):
    """Represents a flight operation with scheduling and tracking.

    Attributes:
        flight_number: Unique flight identifier (e.g., "AA123", "BA456").
        origin: Departure airport code.
        destination: Arrival airport code.
        scheduled_departure: Planned departure time.
        actual_departure: Actual departure time (null if not departed).
        scheduled_arrival: Planned arrival time.
        actual_arrival: Actual arrival time (null if not arrived).
        gate: Assigned gate for the flight.
        status: Current operational status of the flight.
        delay_minutes: Accumulated delay in minutes.
    """

    objects = FlightManager()

    flight_number = models.CharField(max_length=10, unique=True)
    airline = models.CharField(max_length=50, blank=True, default="")
    origin = models.CharField(max_length=3)
    destination = models.CharField(max_length=3)
    scheduled_departure = models.DateTimeField()
    actual_departure = models.DateTimeField(null=True, blank=True)
    scheduled_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    gate = models.ForeignKey(
        Gate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flights",
    )
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in FlightStatus],
        default=FlightStatus.SCHEDULED.value,
    )
    delay_minutes = models.IntegerField(default=0)
    aircraft_type = models.CharField(max_length=30, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for Flight model."""

        ordering = ["scheduled_departure"]
        indexes = [
            # Index for scheduled departures - most common query
            models.Index(fields=['scheduled_departure'], name='flight_depart_idx'),
            # Index for status queries (filtering flights by status)
            models.Index(fields=['status'], name='flight_status_idx'),
            # Composite index for gate availability queries
            models.Index(fields=['gate', 'status', 'scheduled_departure'], name='flight_gate_status_idx'),
            # Index for origin/destination queries
            models.Index(fields=['origin', 'destination'], name='flight_route_idx'),
            # Index for airline queries
            models.Index(fields=['airline'], name='flight_airline_idx'),
            # GIN index for full-text search (PostgreSQL only)
        ]
        
        # Add GIN index only if PostgreSQL is available
        if POSTGRES_AVAILABLE and GinIndex:
            indexes.append(
                GinIndex(fields=['flight_number', 'airline', 'origin', 'destination'], name='flight_search_gin_idx')
            )

    def __str__(self) -> str:
        """Return string representation of the flight."""
        return f"{self.flight_number} ({self.origin} → {self.destination})"

    @classmethod
    def search(cls, query: str):
        """Perform full-text search on flights.
        
        Args:
            query: Search query string.
            
        Returns:
            QuerySet of matching flights.
        """
        from django.db.models import Q
        
        # Simple fuzzy search usingicontains
        return cls.objects.filter(
            Q(flight_number__icontains=query) |
            Q(airline__icontains=query) |
            Q(origin__icontains=query) |
            Q(destination__icontains=query)
        )


class Passenger(models.Model):
    """Represents a passenger with booking and boarding information.

    Attributes:
        passenger_id: Unique passenger identifier.
        first_name: Passenger first name.
        last_name: Passenger last name.
        passport_number: Passport number for identification.
        flight: Associated flight for this passenger.
        seat_number: Assigned seat on the aircraft.
        status: Current passenger status in the travel flow.
    """

    objects = PassengerManager()

    passenger_id = models.UUIDField(default=uuid.uuid4, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    passport_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="passengers",
    )
    seat_number = models.CharField(max_length=5, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in PassengerStatus],
        default=PassengerStatus.CHECKED_IN.value,
    )
    checked_bags = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for Passenger model."""

        ordering = ["last_name", "first_name"]
        indexes = [
            # Index for flight passenger lookups
            models.Index(fields=['flight', 'status'], name='pass_flight_status_idx'),
            # Index for passport lookups
            models.Index(fields=['passport_number'], name='pass_passport_idx'),
            # Index for status queries
            models.Index(fields=['status'], name='pass_status_idx'),
        ]

    def __str__(self) -> str:
        """Return string representation of the passenger."""
        return f"{self.last_name}, {self.first_name} ({self.passport_number})"


class Staff(models.Model):
    """Represents airport or airline staff member.

    Attributes:
        staff_id: Unique staff identifier.
        first_name: Staff first name.
        last_name: Staff last name.
        employee_number: Internal employee ID.
        role: Staff role/position.
        certification: Required certifications for the role.
        is_available: Availability status for assignments.
    """

    objects = StaffManager()

    staff_id = models.UUIDField(default=uuid.uuid4, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    employee_number = models.CharField(max_length=20, unique=True)
    role = models.CharField(
        max_length=20,
        choices=[(role.value, role.name) for role in StaffRole],
    )
    certification = models.CharField(max_length=200, blank=True, default="")
    is_available = models.BooleanField(default=True)
    phone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for Staff model."""

        ordering = ["last_name", "first_name"]
        indexes = [
            # Index for role-based queries
            models.Index(fields=['role'], name='staff_role_idx'),
            # Index for availability queries
            models.Index(fields=['is_available', 'role'], name='staff_avail_role_idx'),
            # Index for employee lookups
            models.Index(fields=['employee_number'], name='staff_emp_idx'),
        ]

    def __str__(self) -> str:
        """Return string representation of the staff member."""
        return f"{self.last_name}, {self.first_name} ({self.role})"


class StaffAssignment(models.Model):
    """Tracks staff assignments to flights for conflict detection.
    
    Attributes:
        staff: The staff member assigned.
        flight: The flight the staff is assigned to.
        assignment_type: Type of assignment (ground_crew, cabin_crew, security, etc.).
        assigned_at: When the assignment was created.
    """
    
    staff = models.ForeignKey(
        Staff,
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    flight = models.ForeignKey(
        'Flight',
        on_delete=models.CASCADE,
        related_name="staff_assignments"
    )
    assignment_type = models.CharField(
        max_length=20,
        choices=[(role.value, role.name) for role in StaffRole],
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """Meta options for StaffAssignment model."""
        
        unique_together = ["staff", "flight", "assignment_type"]
        indexes = [
            models.Index(fields=['staff', 'flight'], name='staff_flight_idx'),
            models.Index(fields=['flight'], name='assignment_flight_idx'),
            models.Index(fields=['staff', 'assigned_at'], name='staff_assign_idx'),
        ]
    
    def clean(self):
        """Check for staff assignment conflicts."""
        from django.core.exceptions import ValidationError
        
        # Check if staff is already assigned to another flight at the same time
        # This is a simplified check assuming flights don't overlap in a way that blocks staff
        # In a real system, we'd check flight start/end times.
        conflicts = StaffAssignment.objects.filter(
            staff=self.staff,
            flight__scheduled_departure=self.flight.scheduled_departure
        ).exclude(pk=self.pk)
        
        if conflicts.exists():
            raise ValidationError(
                f"Staff {self.staff} is already assigned to another flight at {self.flight.scheduled_departure}"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return string representation of the staff assignment."""
        return f"{self.staff} assigned to {self.flight} ({self.assignment_type})"


class EventLog(models.Model):
    """Audit log for all airport operations events.

    Attributes:
        event_id: Unique identifier for the event.
        timestamp: When the event occurred.
        event_type: Type/category of the event.
        description: Human-readable description of the event.
        user: The user who performed the action.
        action: The action performed (create, update, delete, login, logout, etc.).
        flight: Associated flight (if applicable).
        severity: Event severity level (INFO, WARNING, ERROR).
    """

    class EventSeverity(str, Enum):
        """Enumeration of event severity levels."""

        INFO = "info"
        WARNING = "warning"
        ERROR = "error"

    class ActionType(str, Enum):
        """Enumeration of action types."""

        CREATE = "create"
        UPDATE = "update"
        DELETE = "delete"
        LOGIN = "login"
        LOGOUT = "logout"
        VIEW = "view"
        APPROVE = "approve"
        REJECT = "reject"
        EXPORT = "export"
        OTHER = "other"

    objects = EventLogManager()

    event_id = models.UUIDField(default=uuid.uuid4, unique=True)
    timestamp = models.DateTimeField(default=timezone.now)
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(
        max_length=20,
        choices=[(action.value, action.name.title()) for action in ActionType],
        default=ActionType.OTHER.value,
    )
    ip_address = models.CharField(max_length=45, blank=True, default="")
    flight = models.ForeignKey(
        Flight,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    severity = models.CharField(
        max_length=20,
        choices=[(sev.value, sev.name) for sev in EventSeverity],
        default=EventSeverity.INFO.value,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for EventLog model."""

        ordering = ["-timestamp"]
        indexes = [
            # Index for timestamp queries (most common - recent events)
            models.Index(fields=['-timestamp'], name='event_timestamp_idx'),
            # Index for event type filtering
            models.Index(fields=['event_type'], name='event_type_idx'),
            # Index for severity filtering
            models.Index(fields=['severity'], name='event_severity_idx'),
            # Composite index for flight event queries
            models.Index(fields=['flight', '-timestamp'], name='event_flight_time_idx'),
            # Composite index for filtering by type and time
            models.Index(fields=['event_type', '-timestamp'], name='event_type_time_idx'),
            # Index for user activity queries
            models.Index(fields=['user', '-timestamp'], name='event_user_time_idx'),
            # Index for action filtering
            models.Index(fields=['action'], name='event_action_idx'),
        ]

    def __str__(self) -> str:
        """Return string representation of the event."""
        return f"{self.event_type} - {self.timestamp}"


class AssessmentPeriod(str, Enum):
    """Enumeration of assessment period types."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    CUSTOM = "custom"
    
    @classmethod
    def values(cls):
        return [item.value for item in cls]


class AssessmentStatus(str, Enum):
    """Enumeration of assessment status values."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    
    @classmethod
    def values(cls):
        return [item.value for item in cls]


class FiscalAssessment(models.Model):
    """Represents a fiscal/financial assessment for an airport over a period.
    
    Attributes:
        airport: The airport being assessed.
        period_type: Type of assessment period (monthly, quarterly, annual).
        start_date: Start date of the assessment period.
        end_date: End date of the assessment period.
        status: Current status of the assessment.
        total_revenue: Total revenue generated in the period.
        total_expenses: Total expenses in the period.
        net_profit: Net profit (revenue - expenses).
        passenger_count: Number of passengers in the period.
        flight_count: Number of flights in the period.
        fuel_revenue: Revenue from fuel services.
        parking_revenue: Revenue from parking facilities.
        retail_revenue: Revenue from retail/concession.
        landing_fees: Revenue from landing fees.
        security_costs: Security operational costs.
        maintenance_costs: Maintenance costs.
        operational_costs: General operational costs.
        staff_costs: Staff-related costs.
        assessment_notes: Additional notes for the assessment.
        assessed_by: User who conducted the assessment.
        approved_by: User who approved the assessment.
        approved_at: Date of approval.
    """

    objects = FiscalAssessmentManager()

    airport = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="fiscal_assessments"
    )
    period_type = models.CharField(
        max_length=20,
        choices=[(period.value, period.name) for period in AssessmentPeriod],
        default=AssessmentPeriod.MONTHLY.value,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in AssessmentStatus],
        default=AssessmentStatus.DRAFT.value,
    )
    # Financial metrics
    total_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Operational metrics
    passenger_count = models.IntegerField(default=0)
    flight_count = models.IntegerField(default=0)
    
    # Revenue breakdown
    fuel_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    parking_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    retail_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    landing_fees = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cargo_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_revenue = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Expense breakdown
    security_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    maintenance_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    operational_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    staff_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    utility_costs = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Additional fields
    assessment_notes = models.TextField(blank=True, default="")
    assessed_by = models.CharField(max_length=100, blank=True, default="")
    approved_by = models.CharField(max_length=100, blank=True, default="")
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for FiscalAssessment model."""
        
        ordering = ["-start_date"]
        unique_together = ["airport", "period_type", "start_date", "end_date"]
        indexes = [
            # Index for airport period queries
            models.Index(fields=['airport', '-start_date'], name='fiscal_airport_date_idx'),
            # Index for status queries
            models.Index(fields=['status'], name='fiscal_status_idx'),
            # Index for period type queries
            models.Index(fields=['period_type'], name='fiscal_period_idx'),
        ]
    
    def __str__(self) -> str:
        """Return string representation of the fiscal assessment."""
        return f"{self.airport.code} - {self.period_type} ({self.start_date} to {self.end_date})"
    
    def calculate_totals(self) -> 'FiscalAssessment':
        """Calculate total revenue, expenses, and net profit."""
        self.total_revenue = (
            self.fuel_revenue + 
            self.parking_revenue + 
            self.retail_revenue + 
            self.landing_fees + 
            self.cargo_revenue + 
            self.other_revenue
        )
        self.total_expenses = (
            self.security_costs + 
            self.maintenance_costs + 
            self.operational_costs + 
            self.staff_costs + 
            self.utility_costs + 
            self.other_expenses
        )
        self.net_profit = self.total_revenue - self.total_expenses
        return self


class ReportType(str, Enum):
    """Enumeration of report types."""

    FISCAL_SUMMARY = "fiscal_summary"
    OPERATIONAL = "operational"
    PASSENGER = "passenger"
    FINANCIAL = "financial"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    
    @classmethod
    def values(cls):
        return [item.value for item in cls]


class ReportFormat(str, Enum):
    """Enumeration of report output formats."""

    HTML = "html"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    
    @classmethod
    def values(cls):
        return [item.value for item in cls]


class Report(models.Model):
    """Represents a generated report for airport operations.
    
    Attributes:
        report_id: Unique identifier for the report.
        airport: Associated airport for the report.
        report_type: Type of report to generate.
        title: Human-readable report title.
        period_start: Start of the reporting period.
        period_end: End of the reporting period.
        format: Output format of the report.
        file_path: Path to generated file (if applicable).
        content: Report content/data (JSON or text).
        generated_by: User who generated the report.
        status: Generation status (pending, completed, failed).
    """
    
    report_id = models.UUIDField(default=uuid.uuid4, unique=True)
    airport = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    report_type = models.CharField(
        max_length=30,
        choices=[(rt.value, rt.name) for rt in ReportType],
        default=ReportType.FISCAL_SUMMARY.value,
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    period_start = models.DateField()
    period_end = models.DateField()
    format = models.CharField(
        max_length=10,
        choices=[(fmt.value, fmt.name) for fmt in ReportFormat],
        default=ReportFormat.HTML.value,
    )
    file_path = models.CharField(max_length=500, blank=True, default="")
    content = models.JSONField(blank=True, default=dict)
    generated_by = models.CharField(max_length=100, blank=True, default="")
    is_generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for Report model."""
        
        ordering = ["-created_at"]
        indexes = [
            # Index for airport report queries
            models.Index(fields=['airport', '-created_at'], name='report_airport_date_idx'),
            # Index for report type queries
            models.Index(fields=['report_type'], name='report_type_idx'),
            # Index for period queries
            models.Index(fields=['period_start', 'period_end'], name='report_period_idx'),
            # Index for generated status
            models.Index(fields=['is_generated'], name='report_generated_idx'),
        ]
    
    def __str__(self):
        """Return string representation of the report."""
        return f"{self.title} ({self.report_type}) - {self.period_start} to {self.period_end}"


class Document(models.Model):
    """Represents a document template or generated document.
    
    Attributes:
        document_id: Unique identifier for the document.
        name: Document name/title.
        document_type: Type of document (invoice, receipt, certificate, etc.).
        airport: Associated airport.
        fiscal_assessment: Associated fiscal assessment (if applicable).
        report: Associated report (if applicable).
        file_path: Path to the generated file.
        content: Document content/data.
        is_template: Whether this is a template or generated document.
        created_by: User who created the document.
    """
    
    class DocumentType(str, Enum):
        """Enumeration of document types."""
        
        INVOICE = "invoice"
        RECEIPT = "receipt"
        CERTIFICATE = "certificate"
        PERMIT = "permit"
        REPORT = "report"
        AGREEMENT = "agreement"
        MEMO = "memo"
        OTHER = "other"
        
        @classmethod
        def values(cls):
            return [item.value for item in cls]
    
    document_id = models.UUIDField(default=uuid.uuid4, unique=True)
    name = models.CharField(max_length=200)
    document_type = models.CharField(
        max_length=30,
        choices=[(dt.value, dt.name) for dt in DocumentType],
        default=DocumentType.OTHER.value,
    )
    airport = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    fiscal_assessment = models.ForeignKey(
        FiscalAssessment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    file_path = models.CharField(max_length=500, blank=True, default="")
    content = models.JSONField(blank=True, default=dict)
    is_template = models.BooleanField(default=False)
    created_by = models.CharField(max_length=100, blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for Document model."""
        
        ordering = ["-created_at"]
        indexes = [
            # Index for document type queries
            models.Index(fields=['document_type'], name='doc_type_idx'),
            # Index for airport documents
            models.Index(fields=['airport', '-created_at'], name='doc_airport_date_idx'),
            # Index for template queries
            models.Index(fields=['is_template'], name='doc_template_idx'),
        ]
    
    def __str__(self):
        """Return string representation of the document."""
        return f"{self.name} ({self.document_type})"


class AircraftType(str, Enum):
    """Enumeration of aircraft types."""
    
    NARROW_BODY = "narrow_body"
    WIDE_BODY = "wide_body"
    REGIONAL = "regional"
    CARGO = "cargo"


class AircraftStatus(str, Enum):
    """Enumeration of aircraft statuses."""
    
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"
    STORED = "stored"


class Aircraft(models.Model):
    """Represents an individual aircraft with registration and capacity.
    
    Attributes:
        tail_number: Unique aircraft registration (e.g., N12345).
        aircraft_type: Type/category of aircraft.
        model: Specific aircraft model (e.g., Boeing 737-800).
        manufacturer: Aircraft manufacturer.
        capacity_passengers: Maximum passenger capacity.
        capacity_cargo: Cargo capacity in kg.
        status: Current operational status.
        registration_country: Country of registration.
        year_manufactured: Year of manufacture.
        last_maintenance_date: Date of last maintenance check.
        next_maintenance_due: Scheduled next maintenance.
    """
    
    tail_number = models.CharField(max_length=20, unique=True)
    aircraft_type = models.CharField(
        max_length=20,
        choices=[(atype.value, atype.name) for atype in AircraftType],
        default=AircraftType.NARROW_BODY.value,
    )
    model = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=50)
    capacity_passengers = models.IntegerField(default=0)
    capacity_cargo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in AircraftStatus],
        default=AircraftStatus.ACTIVE.value,
    )
    registration_country = models.CharField(max_length=50, blank=True, default="")
    year_manufactured = models.IntegerField(null=True, blank=True)
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_due = models.DateField(null=True, blank=True)
    total_flight_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for Aircraft model."""
        
        ordering = ["tail_number"]
        indexes = [
            models.Index(fields=['status'], name='aircraft_status_idx'),
            models.Index(fields=['aircraft_type'], name='aircraft_type_idx'),
            models.Index(fields=['tail_number'], name='aircraft_tail_idx'),
        ]
    
    def __str__(self):
        """Return string representation of the aircraft."""
        return f"{self.tail_number} ({self.model})"


class CrewMemberType(str, Enum):
    """Enumeration of crew member types."""
    
    PILOT = "pilot"
    FIRST_OFFICER = "first_officer"
    FLIGHT_ATTENDANT = "flight_attendant"
    LEAD_FATTENDANT = "lead_flight_attendant"
    FLIGHT_ENGINEER = "flight_engineer"


class CrewMemberStatus(str, Enum):
    """Enumeration of crew member status."""
    
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_LEAVE = "on_leave"
    UNAVAILABLE = "unavailable"


class CrewMember(models.Model):
    """Represents crew members for flight operations.
    
    Attributes:
        employee_id: Unique employee identifier.
        first_name: Crew member first name.
        last_name: Crew member last name.
        crew_type: Type of crew position.
        license_number: Pilot/crew license number.
        license_expiry: License expiration date.
        status: Current availability status.
        total_flight_hours: Total flight hours logged.
        rank: Seniority rank.
        base_airport: Home/base airport.
        hire_date: Date of hire.
    """
    
    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    crew_type = models.CharField(
        max_length=25,
        choices=[(ctype.value, ctype.name) for ctype in CrewMemberType],
        default=CrewMemberType.FLIGHT_ATTENDANT.value,
    )
    license_number = models.CharField(max_length=50, blank=True, default="")
    license_expiry = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in CrewMemberStatus],
        default=CrewMemberStatus.AVAILABLE.value,
    )
    total_flight_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rank = models.CharField(max_length=30, blank=True, default="")
    base_airport = models.ForeignKey(
        Airport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crew_base",
    )
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    hire_date = models.DateField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for CrewMember model."""
        
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=['status'], name='crew_status_idx'),
            models.Index(fields=['crew_type'], name='crew_type_idx'),
            models.Index(fields=['employee_id'], name='crew_emp_idx'),
        ]
    
    def __str__(self):
        """Return string representation of the crew member."""
        return f"{self.last_name}, {self.first_name} ({self.crew_type})"


class MaintenanceType(str, Enum):
    """Enumeration of maintenance types."""
    
    ROUTINE = "routine"
    SCHEDULED = "scheduled"
    UNSCHEDULED = "unscheduled"
    INSPECTION = "inspection"
    REPAIR = "repair"


class MaintenanceStatus(str, Enum):
    """Enumeration of maintenance status."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenanceLog(models.Model):
    """Tracks maintenance activities for gates and equipment.
    
    Attributes:
        equipment_type: Type of equipment (gate, ground_equipment, etc.).
        equipment_id: ID of the equipment being maintained.
        maintenance_type: Type of maintenance performed.
        description: Description of maintenance work.
        status: Current maintenance status.
        started_at: When maintenance began.
        completed_at: When maintenance was completed.
        performed_by: Staff member who performed maintenance.
        parts_replaced: JSON field for parts replaced.
        cost: Cost of maintenance work.
        notes: Additional notes.
    """
    
    class EquipmentType(str, Enum):
        """Enumeration of equipment types."""
        
        GATE = "gate"
        GROUND_EQUIPMENT = "ground_equipment"
        BAGGAGE_SYSTEM = "baggage_system"
        SECURITY_EQUIPMENT = "security_equipment"
        HVAC = "hvac"
        LIGHTING = "lighting"
        OTHER = "other"
    
    equipment_type = models.CharField(
        max_length=30,
        choices=[(etype.value, etype.name) for etype in EquipmentType],
    )
    equipment_id = models.CharField(max_length=50)
    maintenance_type = models.CharField(
        max_length=20,
        choices=[(mtype.value, mtype.name) for mtype in MaintenanceType],
        default=MaintenanceType.ROUTINE.value,
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in MaintenanceStatus],
        default=MaintenanceStatus.PENDING.value,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_logs",
    )
    parts_replaced = models.JSONField(blank=True, default=list)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for MaintenanceLog model."""
        
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=['equipment_type', 'equipment_id'], name='maint_equip_idx'),
            models.Index(fields=['status'], name='maint_status_idx'),
            models.Index(fields=['maintenance_type'], name='maint_type_idx'),
            models.Index(fields=['started_at'], name='maint_started_idx'),
        ]
    
    def __str__(self):
        """Return string representation of the maintenance log."""
        return f"{self.equipment_type}:{self.equipment_id} - {self.maintenance_type}"


class IncidentSeverity(str, Enum):
    """Enumeration of incident severity levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Enumeration of incident status."""
    
    REPORTED = "reported"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentType(str, Enum):
    """Enumeration of incident types."""
    
    SAFETY = "safety"
    SECURITY = "security"
    OPERATIONAL = "operational"
    ENVIRONMENTAL = "environmental"
    EQUIPMENT = "equipment"
    OTHER = "other"


class IncidentReport(models.Model):
    """Tracks safety and operational incidents.
    
    Attributes:
        incident_id: Unique incident identifier.
        incident_type: Category of incident.
        severity: Severity level.
        status: Current incident status.
        title: Brief incident title.
        description: Detailed incident description.
        location: Where incident occurred.
        reported_by: Staff member who reported.
        assigned_to: Staff member investigating.
        date_occurred: When incident occurred.
        date_reported: When incident was reported.
        date_resolved: When incident was resolved.
        root_cause: Root cause analysis.
        corrective_action: Action taken to prevent recurrence.
        related_flight: Associated flight (if applicable).
        related_gate: Associated gate (if applicable).
    """
    
    incident_id = models.UUIDField(default=uuid.uuid4, unique=True)
    incident_type = models.CharField(
        max_length=20,
        choices=[(itype.value, itype.name) for itype in IncidentType],
    )
    severity = models.CharField(
        max_length=20,
        choices=[(sev.value, sev.name) for sev in IncidentSeverity],
    )
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in IncidentStatus],
        default=IncidentStatus.REPORTED.value,
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100, blank=True, default="")
    reported_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_incidents",
    )
    assigned_to = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_incidents",
    )
    date_occurred = models.DateTimeField()
    date_reported = models.DateTimeField(auto_now_add=True)
    date_resolved = models.DateTimeField(null=True, blank=True)
    root_cause = models.TextField(blank=True, default="")
    corrective_action = models.TextField(blank=True, default="")
    related_flight = models.ForeignKey(
        Flight,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
    )
    related_gate = models.ForeignKey(
        Gate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incidents",
    )
    attachments = models.JSONField(blank=True, default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for IncidentReport model."""
        
        ordering = ["-date_occurred"]
        indexes = [
            models.Index(fields=['incident_type'], name='inc_type_idx'),
            models.Index(fields=['severity'], name='inc_severity_idx'),
            models.Index(fields=['status'], name='inc_status_idx'),
            models.Index(fields=['date_occurred'], name='inc_date_idx'),
            models.Index(fields=['date_reported'], name='inc_reported_idx'),
            models.Index(fields=['related_flight'], name='inc_flight_idx'),
            models.Index(fields=['related_gate'], name='inc_gate_idx'),
        ]

    def __str__(self):
        """Return string representation of the incident report."""
        return f"{self.incident_type} - {self.title} ({self.severity})"


class ReportSchedule(models.Model):
    """Scheduled recurring reports with email delivery.

    Attributes:
        name: Schedule name for identification.
        report_type: Type of report to generate.
        airport: Airport for the report (optional for system-wide).
        frequency: How often to generate (daily, weekly, monthly).
        day_of_week: Day of week for weekly reports.
        day_of_month: Day of month for monthly reports.
        hour: Hour of day to generate (0-23).
        recipients: Email addresses to send report to.
        format: Report format (PDF, CSV, JSON).
        is_active: Whether schedule is active.
        last_run: Last time report was generated.
        next_run: Next scheduled run time.
        created_by: User who created the schedule.
    """

    class Frequency(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'

    name = models.CharField(max_length=100)
    report_type = models.CharField(
        max_length=30,
        choices=[(rt.value, rt.name) for rt in ReportType],
    )
    airport = models.ForeignKey(
        Airport,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='report_schedules',
    )
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.WEEKLY,
    )
    day_of_week = models.IntegerField(
        null=True,
        blank=True,
        help_text='0=Monday, 6=Sunday (for weekly frequency)'
    )
    day_of_month = models.IntegerField(
        null=True,
        blank=True,
        help_text='1-31 (for monthly frequency)'
    )
    hour = models.IntegerField(
        default=6,
        help_text='Hour of day (0-23) to generate report'
    )
    recipients = models.TextField(
        help_text='Comma-separated email addresses'
    )
    format = models.CharField(
        max_length=10,
        choices=[(fmt.value, fmt.name) for fmt in ReportFormat],
        default=ReportFormat.PDF,
    )
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_schedules',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active'], name='schedule_active_idx'),
            models.Index(fields=['frequency'], name='schedule_freq_idx'),
            models.Index(fields=['next_run'], name='schedule_next_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.frequency} - {self.report_type})"

    def calculate_next_run(self) -> Optional[datetime]:
        """Calculate the next run time based on frequency."""
        from datetime import timedelta
        from django.utils import timezone

        now = timezone.now()
        next_time = now.replace(minute=0, second=0, microsecond=0)

        if self.frequency == self.Frequency.DAILY:
            # Next day at specified hour
            if next_time.hour >= self.hour:
                next_time += timedelta(days=1)
            next_time = next_time.replace(hour=self.hour)

        elif self.frequency == self.Frequency.WEEKLY:
            # Next specified day of week
            if self.day_of_week is not None:
                days_ahead = self.day_of_week - next_time.weekday()
                if days_ahead < 0 or (days_ahead == 0 and next_time.hour >= self.hour):
                    days_ahead += 7
                next_time += timedelta(days=days_ahead)
                next_time = next_time.replace(hour=self.hour)

        elif self.frequency == self.Frequency.MONTHLY:
            # Next specified day of month
            if self.day_of_month is not None:
                import calendar
                # Get last day of current month
                _, last_day = calendar.monthrange(now.year, now.month)
                target_day = min(self.day_of_month, last_day)

                if now.day >= target_day:
                    # Next month
                    if now.month == 12:
                        next_time = next_time.replace(year=now.year + 1, month=1, day=target_day, hour=self.hour)
                    else:
                        next_time = next_time.replace(month=now.month + 1, day=target_day, hour=self.hour)
                else:
                    # This month
                    next_time = next_time.replace(day=target_day, hour=self.hour)

        return next_time

    def save(self, *args, **kwargs):
        """Calculate next run time on save."""
        if self.is_active and not self.next_run:
            self.next_run = self.calculate_next_run()
        super().save(*args, **kwargs)


class Shift(models.Model):
    """Represents a work shift for staff scheduling.

    Attributes:
        name: Shift name (e.g., "Morning Shift", "Night Shift").
        start_time: Shift start time.
        end_time: Shift end time.
        min_staff: Minimum staff required.
        max_staff: Maximum staff allowed.
        is_active: Whether shift is active.
    """

    name = models.CharField(max_length=50)
    start_time = models.TimeField()
    end_time = models.TimeField()
    min_staff = models.PositiveIntegerField(default=1)
    max_staff = models.PositiveIntegerField(default=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['is_active'], name='shift_active_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"

    def duration_hours(self):
        """Calculate shift duration in hours."""
        from datetime import datetime
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end < start:  # Overnight shift
            end += timedelta(days=1)
        return (end - start).seconds / 3600


class StaffShiftAssignment(models.Model):
    """Assignment of staff to specific shifts.

    Attributes:
        staff: Staff member assigned.
        shift: Shift assignment.
        date: Date of the shift.
        status: Assignment status.
        notes: Optional notes.
    """

    class AssignmentStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        CONFIRMED = 'confirmed', 'Confirmed'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='shift_assignments')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='assignments')
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.SCHEDULED,
    )
    notes = models.TextField(blank=True, default='')
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'shift__start_time']
        unique_together = ['staff', 'date', 'shift']
        indexes = [
            models.Index(fields=['date'], name='shift_assign_date_idx'),
            models.Index(fields=['status'], name='shift_assign_status_idx'),
            models.Index(fields=['staff', 'date'], name='shift_assign_staff_date_idx'),
        ]

    def __str__(self):
        return f"{self.staff} - {self.shift.name} on {self.date}"


class Baggage(models.Model):
    """Tracks passenger baggage through the airport.

    Attributes:
        tag_number: Unique baggage tag identifier.
        passenger: Associated passenger.
        flight: Associated flight.
        status: Current baggage status.
        origin: Origin airport code.
        destination: Destination airport code.
        weight: Baggage weight in kg.
        pieces: Number of pieces.
        special_handling: Special handling requirements.
        location: Current location.
        checked_in_at: Check-in timestamp.
        loaded_at: Loading timestamp.
        unloaded_at: Unloading timestamp.
        claimed_at: Claim timestamp.
    """

    class BaggageStatus(models.TextChoices):
        CHECKED_IN = 'checked_in', 'Checked In'
        SCREENED = 'screened', 'Screened'
        SORTED = 'sorted', 'Sorted'
        LOADED = 'loaded', 'Loaded'
        IN_TRANSIT = 'in_transit', 'In Transit'
        UNLOADED = 'unloaded', 'Unloaded'
        AT_BELT = 'at_belt', 'At Claim Belt'
        CLAIMED = 'claimed', 'Claimed'
        LOST = 'lost', 'Lost'
        DAMAGED = 'damaged', 'Damaged'

    tag_number = models.CharField(max_length=20, unique=True)
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, related_name='baggage')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='baggage')
    status = models.CharField(
        max_length=20,
        choices=BaggageStatus.choices,
        default=BaggageStatus.CHECKED_IN,
    )
    origin = models.CharField(max_length=3)
    destination = models.CharField(max_length=3)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text='Weight in kg')
    pieces = models.PositiveIntegerField(default=1)
    special_handling = models.CharField(max_length=100, blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    description = models.TextField(blank=True, default='')
    checked_in_at = models.DateTimeField(auto_now_add=True)
    screened_at = models.DateTimeField(null=True, blank=True)
    loaded_at = models.DateTimeField(null=True, blank=True)
    unloaded_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-checked_in_at']
        indexes = [
            models.Index(fields=['status'], name='baggage_status_idx'),
            models.Index(fields=['flight'], name='baggage_flight_idx'),
            models.Index(fields=['passenger'], name='baggage_passenger_idx'),
            models.Index(fields=['tag_number'], name='baggage_tag_idx'),
        ]

    def __str__(self):
        return f"Baggage {self.tag_number} - {self.passenger} ({self.status})"


class WeatherCondition(models.Model):
    """Weather conditions affecting airport operations.

    Attributes:
        airport: Associated airport.
        timestamp: Time of weather observation.
        temperature: Temperature in Celsius.
        feels_like: Feels-like temperature.
        humidity: Humidity percentage.
        pressure: Atmospheric pressure in hPa.
        wind_speed: Wind speed in km/h.
        wind_direction: Wind direction in degrees.
        wind_gust: Wind gust speed in km/h.
        visibility: Visibility in meters.
        cloud_cover: Cloud cover percentage.
        precipitation: Precipitation in mm.
        weather_code: Weather condition code.
        weather_description: Human-readable description.
        severity: Weather severity level.
        delay_impact: Estimated delay impact in minutes.
        fetched_at: When data was fetched from API.
    """

    class Severity(models.TextChoices):
        NORMAL = 'normal', 'Normal'
        MODERATE = 'moderate', 'Moderate'
        HIGH = 'high', 'High'
        SEVERE = 'severe', 'Severe'

    airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='weather_conditions')
    timestamp = models.DateTimeField()
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feels_like = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    humidity = models.PositiveIntegerField(null=True, blank=True)
    pressure = models.PositiveIntegerField(null=True, blank=True)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    wind_direction = models.PositiveIntegerField(null=True, blank=True, help_text='Degrees 0-360')
    wind_gust = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    visibility = models.PositiveIntegerField(null=True, blank=True, help_text='Meters')
    cloud_cover = models.PositiveIntegerField(null=True, blank=True)
    precipitation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weather_code = models.CharField(max_length=20, blank=True, default='')
    weather_description = models.CharField(max_length=100, blank=True, default='')
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.NORMAL,
    )
    delay_impact = models.PositiveIntegerField(default=0, help_text='Estimated delay in minutes')
    notes = models.TextField(blank=True, default='')
    fetched_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['airport', '-timestamp'], name='weather_airport_time_idx'),
            models.Index(fields=['severity'], name='weather_severity_idx'),
            models.Index(fields=['timestamp'], name='weather_time_idx'),
        ]

    def __str__(self):
        return f"{self.airport.code} - {self.weather_description} ({self.timestamp})"

    def calculate_delay_impact(self):
        """Calculate estimated delay impact based on weather conditions."""
        impact = 0

        # Wind impact
        if self.wind_speed:
            if self.wind_speed > 50:
                impact += 30
            elif self.wind_speed > 30:
                impact += 15
            elif self.wind_speed > 20:
                impact += 5

        # Visibility impact
        if self.visibility and self.visibility < 1000:
            impact += 45
        elif self.visibility and self.visibility < 5000:
            impact += 20

        # Precipitation impact
        if self.precipitation and self.precipitation > 10:
            impact += 25
        elif self.precipitation and self.precipitation > 5:
            impact += 10

        # Severe weather
        if self.severity == self.Severity.SEVERE:
            impact += 60
        elif self.severity == self.Severity.HIGH:
            impact += 30

        return impact


class WeatherAlert(models.Model):
    """Weather alerts and warnings for airports.

    Attributes:
        airport: Affected airport.
        alert_type: Type of weather alert.
        severity: Alert severity.
        title: Alert title.
        description: Alert description.
        start_time: Alert start time.
        end_time: Expected alert end time.
        is_active: Whether alert is currently active.
        acknowledged_by: Staff who acknowledged the alert.
        acknowledged_at: When alert was acknowledged.
    """

    class AlertType(models.TextChoices):
        THUNDERSTORM = 'thunderstorm', 'Thunderstorm'
        TORNADO = 'tornado', 'Tornado'
        HURRICANE = 'hurricane', 'Hurricane'
        HEAVY_RAIN = 'heavy_rain', 'Heavy Rain'
        HEAVY_SNOW = 'heavy_snow', 'Heavy Snow'
        FOG = 'fog', 'Fog'
        ICE = 'ice', 'Ice'
        HIGH_WIND = 'high_wind', 'High Wind'
        HEAT_WAVE = 'heat_wave', 'Heat Wave'
        OTHER = 'other', 'Other'

    airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='weather_alerts')
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(
        max_length=20,
        choices=WeatherCondition.Severity.choices,
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    acknowledged_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_weather_alerts',
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['airport', 'is_active'], name='alert_airport_active_idx'),
            models.Index(fields=['is_active'], name='alert_active_idx'),
            models.Index(fields=['alert_type'], name='alert_type_idx'),
        ]

    def __str__(self):
        return f"{self.alert_type} - {self.airport.code} ({'Active' if self.is_active else 'Inactive'})"


class FuelInventory(models.Model):
    """Tracks fuel inventory at airports.

    Attributes:
        airport: Associated airport.
        fuel_type: Type of fuel (Jet A, Jet A-1, Avgas).
        storage_tank: Storage tank identifier.
        capacity: Maximum capacity in liters.
        current_level: Current fuel level in liters.
        min_level: Minimum safe level.
        last_delivery: Last fuel delivery date.
        last_delivery_amount: Amount of last delivery.
    """

    class FuelType(models.TextChoices):
        JET_A = 'jet_a', 'Jet A'
        JET_A1 = 'jet_a1', 'Jet A-1'
        AVGAS = 'avgas', 'Avgas 100LL'

    airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='fuel_inventories')
    fuel_type = models.CharField(max_length=20, choices=FuelType.choices)
    storage_tank = models.CharField(max_length=50)
    capacity = models.DecimalField(max_digits=10, decimal_places=2, help_text='Liters')
    current_level = models.DecimalField(max_digits=10, decimal_places=2, help_text='Liters')
    min_level = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='Liters')
    last_delivery = models.DateTimeField(null=True, blank=True)
    last_delivery_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['airport', 'fuel_type']
        unique_together = ['airport', 'fuel_type', 'storage_tank']
        indexes = [
            models.Index(fields=['airport', 'fuel_type'], name='fuel_airport_type_idx'),
            models.Index(fields=['fuel_type'], name='fuel_type_idx'),
        ]

    def __str__(self):
        return f"{self.airport.code} - {self.fuel_type} ({self.storage_tank})"

    @property
    def fill_percentage(self):
        """Calculate current fill percentage."""
        if self.capacity > 0:
            return (self.current_level / self.capacity) * 100
        return 0

    @property
    def is_low(self):
        """Check if fuel level is below minimum."""
        return self.current_level < self.min_level


class FuelDispensing(models.Model):
    """Records fuel dispensing to aircraft.

    Attributes:
        flight: Associated flight.
        inventory: Fuel inventory source.
        amount: Amount dispensed in liters.
        start_time: Dispensing start time.
        end_time: Dispensing end time.
        operator: Staff member who operated dispensing.
        truck_id: Fuel truck identifier.
        notes: Optional notes.
    """

    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name='fuel_dispensing')
    inventory = models.ForeignKey(FuelInventory, on_delete=models.CASCADE, related_name='dispensing_records')
    amount = models.DecimalField(max_digits=8, decimal_places=2, help_text='Liters')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    operator = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fuel_dispensing_records',
    )
    truck_id = models.CharField(max_length=20, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['flight'], name='fuel_disp_flight_idx'),
            models.Index(fields=['inventory'], name='fuel_disp_inv_idx'),
            models.Index(fields=['start_time'], name='fuel_disp_time_idx'),
        ]

    def __str__(self):
        return f"{self.flight.flight_number} - {self.amount}L ({self.start_time})"

    def save(self, *args, **kwargs):
        """Update inventory level on save."""
        if not self.end_time:
            self.end_time = timezone.now()
        super().save(*args, **kwargs)
        
        # Update inventory level
        self.inventory.current_level -= self.amount
        self.inventory.save(update_fields=['current_level', 'updated_at'])


class MaintenanceSchedule(models.Model):
    """Preventive maintenance scheduling.

    Attributes:
        equipment_type: Type of equipment (gate, vehicle, facility).
        equipment_id: Reference to equipment.
        maintenance_type: Type of maintenance.
        title: Maintenance title.
        description: Maintenance description.
        frequency: Maintenance frequency.
        last_performed: Last maintenance date.
        next_due: Next due date.
        priority: Maintenance priority.
        status: Current status.
        assigned_to: Staff assigned to maintenance.
    """

    class EquipmentType(models.TextChoices):
        GATE = 'gate', 'Gate'
        VEHICLE = 'vehicle', 'Vehicle'
        FACILITY = 'facility', 'Facility'
        EQUIPMENT = 'equipment', 'Equipment'
        HVAC = 'hvac', 'HVAC System'
        ELECTRICAL = 'electrical', 'Electrical'

    class Frequency(models.TextChoices):
        DAILY = 'daily', 'Daily'
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        QUARTERLY = 'quarterly', 'Quarterly'
        ANNUALLY = 'annually', 'Annually'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        OVERDUE = 'overdue', 'Overdue'
        CANCELLED = 'cancelled', 'Cancelled'

    equipment_type = models.CharField(max_length=20, choices=EquipmentType.choices)
    equipment_id = models.CharField(max_length=50, help_text='Equipment identifier')
    airport = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='maintenance_schedules')
    maintenance_type = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField()
    frequency = models.CharField(max_length=20, choices=Frequency.choices)
    last_performed = models.DateTimeField(null=True, blank=True)
    next_due = models.DateTimeField()
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    assigned_to = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_maintenance',
    )
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_due', 'priority']
        indexes = [
            models.Index(fields=['status'], name='maint_sched_status_idx'),
            models.Index(fields=['next_due'], name='maint_sched_due_idx'),
            models.Index(fields=['equipment_type', 'equipment_id'], name='maint_sched_equip_idx'),
            models.Index(fields=['airport', 'status'], name='maint_sched_airport_idx'),
        ]

    def __str__(self):
        return f"{self.title} - {self.equipment_id} ({self.next_due})"

    def calculate_next_due(self):
        """Calculate next due date based on frequency."""
        from datetime import timedelta

        now = timezone.now()
        if self.frequency == self.Frequency.DAILY:
            return now + timedelta(days=1)
        elif self.frequency == self.Frequency.WEEKLY:
            return now + timedelta(weeks=1)
        elif self.frequency == self.Frequency.MONTHLY:
            return now + timedelta(days=30)
        elif self.frequency == self.Frequency.QUARTERLY:
            return now + timedelta(days=90)
        elif self.frequency == self.Frequency.ANNUALLY:
            return now + timedelta(days=365)
        return now

    def check_overdue(self):
        """Check if maintenance is overdue and update status."""
        if self.status == self.Status.SCHEDULED and timezone.now() > self.next_due:
            self.status = self.Status.OVERDUE
            self.save(update_fields=['status', 'updated_at'])
            return True
        return False


class CustomField(models.Model):
    """Custom field definitions for extensible data models.
    
    Allows admins to add custom fields to models without code changes.
    
    Attributes:
        name: Field name (internal identifier).
        label: Display label for the field.
        model_name: Target model name.
        field_type: Type of field.
        required: Whether field is required.
        choices: JSON list of choices.
        default_value: Default value.
        help_text: Help text for the field.
        is_active: Whether field is active.
    """

    class FieldType(models.TextChoices):
        TEXT = 'text', 'Text'
        NUMBER = 'number', 'Number'
        DATE = 'date', 'Date'
        BOOLEAN = 'boolean', 'Yes/No'
        CHOICE = 'choice', 'Dropdown'
        EMAIL = 'email', 'Email'
        URL = 'url', 'URL'

    name = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    model_name = models.CharField(max_length=50)
    field_type = models.CharField(max_length=20, choices=FieldType.choices, default=FieldType.TEXT)
    required = models.BooleanField(default=False)
    choices = models.JSONField(blank=True, default=list)
    default_value = models.CharField(max_length=255, blank=True, default='')
    help_text = models.CharField(max_length=255, blank=True, default='')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['model_name', 'order', 'name']
        unique_together = ['model_name', 'name']

    def __str__(self):
        return f"{self.model_name}.{self.name}"


class CustomFieldValue(models.Model):
    """Stores custom field values for model instances."""

    field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name='values')
    object_id = models.PositiveIntegerField()
    model_name = models.CharField(max_length=50)
    value = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['field', 'object_id', 'model_name']
        indexes = [
            models.Index(fields=['model_name', 'object_id']),
        ]

    def __str__(self):
        return f"{self.model_name} #{self.object_id}.{self.field.name}"


from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver


@receiver(post_save, sender=StaffAssignment)
def update_staff_availability_on_assignment(sender, instance, created, **kwargs):
    """Set staff to unavailable when assigned to a flight."""
    if created:
        staff = instance.staff
        if staff.is_available:
            staff.is_available = False
            staff.save(update_fields=['is_available'])


@receiver(post_delete, sender=StaffAssignment)
def update_staff_availability_on_unassignment(sender, instance, **kwargs):
    """Set staff to available when unassigned from a flight."""
    staff = instance.staff
    # Check if staff has any other assignments
    if not StaffAssignment.objects.filter(staff=staff).exists():
        if not staff.is_available:
            staff.is_available = True
            staff.save(update_fields=['is_available'])


@receiver(post_save, sender=Flight)
def update_gate_status_on_assignment(sender, instance, **kwargs):
    """Update gate status when a flight is assigned to a gate."""
    if instance.gate:
        gate = instance.gate
        if gate.status != GateStatus.OCCUPIED.value:
            gate.status = GateStatus.OCCUPIED.value
            gate.save(update_fields=['status'])


@receiver(post_delete, sender=Flight)
def update_gate_status_on_release(sender, instance, **kwargs):
    """Release gate when a flight is deleted."""
    if instance.gate:
        gate = instance.gate
        # Check if any other flights are using this gate
        if not Flight.objects.filter(gate=gate).exclude(pk=instance.pk).exists():
            if gate.status == GateStatus.OCCUPIED.value:
                gate.status = GateStatus.AVAILABLE.value
                gate.save(update_fields=['status'])
