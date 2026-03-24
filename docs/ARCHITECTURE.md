# Architecture Documentation

> **Project:** Project Falcon - Airport Operations Management System
> **Version:** 1.0
> **Last Updated:** March 24, 2026

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architectural Patterns](#architectural-patterns)
3. [Component Architecture](#component-architecture)
4. [Data Architecture](#data-architecture)
5. [Integration Architecture](#integration-architecture)
6. [Security Architecture](#security-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Performance Architecture](#performance-architecture)

---

## System Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                         External Systems                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Weather │  │  Email   │  │  Users   │  │  API Consumers   │   │
│  │  Service │  │  Server  │  │(Browser) │  │  (Mobile/Web)    │   │
│  │(Open-Meteo)│ │ (SMTP)  │  │          │  │                  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
└───────┼─────────────┼─────────────┼─────────────────┼──────────────┘
        │             │             │                 │
        │ HTTPS       │ SMTP        │ HTTPS/WSS       │ HTTPS
        ▼             ▼             ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Project Falcon System                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                 Application Layer                             │  │
│  │  Django + DRF + Channels + Django-Q2                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                 Data Layer                                    │  │
│  │  PostgreSQL + Redis + File System                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### System Goals

| Goal | Description |
|------|-------------|
| **Real-time Operations** | Live updates for flight status, gate availability, and events |
| **Data Integrity** | ACID-compliant transactions with comprehensive audit logging |
| **Scalability** | Support multiple airports with growing data volumes |
| **Security** | Role-based access control with comprehensive protection |
| **Accessibility** | WCAG 2.1 AA compliance for all user interfaces |
| **Maintainability** | Clean architecture with separation of concerns |

---

## Architectural Patterns

### Layered Architecture

The system follows a layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                   Presentation Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Templates  │  │   Static    │  │   WebSocket UI      │ │
│  │  (HTML/CSS) │  │   Assets    │  │   (JavaScript)      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTP/WSS
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Views     │  │    API      │  │    Consumers        │ │
│  │  (Django)   │  │  (DRF)      │  │  (Channels)         │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                     │            │
│  ┌──────▼────────────────▼─────────────────────▼──────────┐ │
│  │              Business Logic Layer                       │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │ │
│  │  │  Models  │  │ Services │  │   Background Tasks   │ │ │
│  │  │          │  │          │  │   (Django-Q2)        │ │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ ORM/Cache
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ PostgreSQL  │  │   Redis     │  │   File System       │ │
│  │ (Database)  │  │  (Cache)    │  │   (Static/Media)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Model-View-Template (MVT)

Django's MVT pattern is used for web views:

```
User Request
    │
    ▼
URL Router → View (Business Logic)
                 │
                 ├─────→ Model (Database)
                 │            │
                 │            ▼
                 │         Data Return
                 │
                 ├─────→ Form (Validation)
                 │
                 ▼
Template (HTML Rendering)
    │
    ▼
HTML Response
```

### Repository Pattern (via Managers)

Custom model managers provide repository-like functionality:

```python
class FlightManager(models.Manager):
    """Repository-style query interface."""
    
    def by_status(self, status: str) -> QuerySet:
        """Filter flights by status."""
        return self.filter(status=status)
    
    def delayed(self) -> QuerySet:
        """Get all delayed flights."""
        return self.filter(status=FlightStatus.DELAYED.value)
    
    def upcoming(self) -> QuerySet:
        """Get upcoming scheduled flights."""
        return self.filter(
            status=FlightStatus.SCHEDULED.value,
            scheduled_departure__gte=timezone.now()
        ).order_by('scheduled_departure')


# Usage
delayed_flights = Flight.objects.delayed()
upcoming = Flight.objects.upcoming()
```

### Observer Pattern (via Signals)

Django signals implement the observer pattern for automatic event logging:

```python
# Subject: Model save operation
@receiver(post_save, sender=FiscalAssessment)
def log_fiscal_assessment_change(sender, instance, created, **kwargs):
    """Observer: Automatically log fiscal assessment changes."""
    if created:
        EventLog.objects.create(
            event_type='fiscal_assessment',
            action='create',
            description=f'Fiscal assessment created for {instance.airport}',
            severity='info'
        )
```

### Publisher-Subscriber Pattern (via Channels)

WebSocket consumers implement pub/sub for real-time updates:

```
┌─────────────┐
│   Model     │ ──save()──> Signal ──> broadcast_flight_update()
└─────────────┘                                  │
                                                 ▼
                                          Channel Layer
                                          (Room Group)
                                                 │
                    ┌────────────────────────────┼────────────────┐
                    │                            │                │
                    ▼                            ▼                ▼
             ┌──────────┐                 ┌──────────┐    ┌──────────┐
             │ Consumer │                 │ Consumer │    │ Consumer │
             │ Client 1 │                 │ Client 2 │    │ Client 3 │
             └──────────┘                 └──────────┘    └──────────┘
```

---

## Component Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Project Falcon System                          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Web Layer                                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐ │ │
│  │  │   Django    │  │    DRF      │  │   Django Channels     │ │ │
│  │  │   Views     │  │  ViewSets   │  │    Consumers          │ │ │
│  │  └──────┬──────┘  └──────┬──────┘  └───────────┬───────────┘ │ │
│  └─────────┼────────────────┼─────────────────────┼─────────────┘ │
│            │                │                     │               │
│  ┌─────────▼────────────────▼─────────────────────▼─────────────┐ │
│  │                   Business Logic Layer                        │ │
│  │  ┌─────────────────────────────────────────────────────────┐ │ │
│  │  │  Models (core/models.py - 2117 lines)                   │ │ │
│  │  │  - Airport, Gate, Flight, Passenger, Staff              │ │ │
│  │  │  - FiscalAssessment, Report, Document                   │ │ │
│  │  │  - Aircraft, CrewMember, MaintenanceLog, IncidentReport │ │ │
│  │  └─────────────────────────────────────────────────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │ │
│  │  │   Forms      │  │ Serializers  │  │   Permissions      │ │ │
│  │  │  (forms.py)  │  │(serializers) │  │  (permissions.py)  │ │ │
│  │  └──────────────┘  └──────────────┘  └────────────────────┘ │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │ │
│  │  │   Signals    │  │    Tasks     │  │   Services         │ │ │
│  │  │ (signals.py) │  │  (tasks.py)  │  │ (weather, map)     │ │ │
│  │  └──────────────┘  └──────────────┘  └────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Cross-Cutting Concerns                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐ │ │
│  │  │ Middleware  │  │  Honeypot   │  │    Logging            │ │ │
│  │  │             │  │  Protection │  │   (EventLog)          │ │ │
│  │  └─────────────┘  └─────────────┘  └───────────────────────┘ │ │
│  │  ┌─────────────┐  ┌─────────────┐                            │ │
│  │  │   Cache     │  │   Rate      │                            │ │
│  │  │             │  │  Limiting   │                            │ │
│  │  └─────────────┘  └─────────────┘                            │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Module Dependencies

```
┌──────────────────────────────────────────────────────────────┐
│                     Module Dependency Graph                  │
│                                                              │
│  ┌─────────┐                                                 │
│  │ models  │◄────────────────────────────────────────┐       │
│  └────┬────┘                                        │       │
│       │                                             │       │
│       ▼                                             │       │
│  ┌─────────┐   ┌──────────┐   ┌───────────┐        │       │
│  │ forms   │   │serializers│   │permissions│        │       │
│  └────┬────┘   └─────┬────┘   └─────┬─────┘        │       │
│       │              │              │               │       │
│       ▼              ▼              ▼               │       │
│  ┌──────────────────────────────────────────┐       │       │
│  │              views.py / api.py           │───────┘       │
│  └──────────────────────────────────────────┘               │
│       │                                                     │
│       ▼                                                     │
│  ┌──────────────────────────────────────────┐               │
│  │              urls.py                     │               │
│  └──────────────────────────────────────────┘               │
│                                                              │
│  ┌─────────┐   ┌──────────┐   ┌───────────┐                │
│  │signals  │   │  tasks   │   │ consumers │                │
│  └────┬────┘   └────┬─────┘   └─────┬─────┘                │
│       │             │               │                       │
│       └─────────────┴───────────────┘                       │
│                     │                                       │
│                     ▼                                       │
│              ┌─────────────┐                                │
│              │    models   │                                │
│              └─────────────┘                                │
└──────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### Models (`core/models.py`)

**Responsibility:** Data structure definition, business rules, and query logic

**Components:**
- **Entity Models:** Airport, Gate, Flight, Passenger, Staff, etc.
- **Financial Models:** FiscalAssessment, Report, Document
- **Operational Models:** Aircraft, CrewMember, MaintenanceLog, IncidentReport
- **Audit Models:** EventLog

**Key Features:**
- Custom managers for common queries
- Enum-based status fields
- Database indexes for performance
- Automatic timestamp tracking

#### Views (`core/views.py`)

**Responsibility:** HTTP request handling, business logic orchestration, template rendering

**View Classes:**
```
BaseListView ──┬── FiscalAssessmentListView
               ├── ReportListView
               ├── DocumentListView
               └── EventLogListView

BaseCreateView ──┬── FiscalAssessmentCreateView
                 ├── ReportCreateView
                 └── DocumentCreateView

BaseDetailView ──┬── FiscalAssessmentDetailView
                 ├── ReportDetailView
                 └── DocumentDetailView

BaseUpdateView ──┬── FiscalAssessmentUpdateView
                 ├── ReportUpdateView
                 └── DocumentUpdateView

Special Views:
- DashboardView
- AnalyticsDashboardView
- AirportComparisonView
- FlightStatusPortalView (public)
- BaggageTrackingView (public)
- DataImportWizardView
```

#### API (`core/api.py`)

**Responsibility:** RESTful API endpoints with DRF

**ViewSets:**
```
AirportViewSet
GateViewSet
FlightViewSet
PassengerViewSet
StaffViewSet
StaffAssignmentViewSet
EventLogViewSet
FiscalAssessmentViewSet
AircraftViewSet
CrewMemberViewSet
MaintenanceLogViewSet
IncidentReportViewSet
ReportViewSet
DocumentViewSet

Special Views:
- DashboardSummaryView (cached)
- AnalyticsDashboardView
- TrendDataAPIView
```

#### Forms (`core/forms.py`)

**Responsibility:** Input validation, CSRF protection, honeypot integration

**Form Classes:**
```
FiscalAssessmentCreateForm
FiscalAssessmentUpdateForm
FiscalAssessmentApprovalForm
ReportCreateForm
DocumentCreateForm
ReportScheduleForm
```

**Security Features:**
- HoneypotFieldMixin for bot protection
- Explicit field allowlists
- Type validation (Decimal, Integer, Date)
- Cross-field validation

#### Permissions (`core/permissions.py`)

**Responsibility:** Role-based access control

**Roles:**
```
UserRole.VIEWER     → Read-only access
UserRole.EDITOR     → Create/edit operations
UserRole.APPROVER   → Approval workflows
UserRole.ADMIN      → Full access (superuser only)
```

**Permission Classes:**
```
AirportPermissions
GatePermissions
FlightPermissions
StaffPermissions
FiscalAssessmentPermissions
ReportPermissions
DocumentPermissions
MaintenanceLogPermissions
IncidentReportPermissions
```

#### Consumers (`core/consumers.py`)

**Responsibility:** Real-time WebSocket communication

**Consumers:**
```
DashboardConsumer      → /ws/dashboard/
FlightUpdatesConsumer  → /ws/flights/
GateStatusConsumer     → /ws/gates/
EventLogConsumer       → /ws/events/
NotificationConsumer   → /ws/notifications/
```

**Features:**
- Connection limiting (10 per user)
- Rate limiting (100 msg/s)
- Group messaging
- Authentication required

#### Tasks (`core/tasks.py`)

**Responsibility:** Background job processing

**Tasks:**
```
generate_report_task()         → Generate report content
generate_scheduled_report()    → Process scheduled reports
send_report_email()            → Email report delivery
check_scheduled_reports()      → Queue due reports
warm_cache()                   → Pre-populate cache
backup_database()              → Database backup
```

**Scheduling (Django-Q2):**
```python
'schedules': {
    'check_scheduled_reports': {'func': '...', 'schedule': 3600},
    'fetch_weather_data': {'func': '...', 'schedule': 900},
    'warm_cache': {'func': '...', 'schedule': 1800},
}
```

---

## Data Architecture

### Database Schema

#### Entity Relationship Model

```
┌─────────────────┐
│    Airport      │
├─────────────────┤
│ PK id           │
│    code (UK)    │
│    name         │
│    city         │
│    timezone     │
│    is_active    │
│    created_at   │
│    updated_at   │
└────────┬────────┘
         │ 1:N
         │
    ┌────▼────────┐         ┌─────────────────┐
    │    Gate     │         │    Flight       │
    ├─────────────┤         ├─────────────────┤
    │ PK id       │         │ PK id           │
    │    gate_id  │         │    flight_number│
    │    terminal │         │    airline      │
    │    capacity │         │    origin       │
    │    status   │         │    destination  │
    │ FK airport  │         │    scheduled_*  │
    └─────────────┘         │    actual_*     │
                            │ FK gate         │
                            │    status       │
                            │    delay_minutes│
                            └────────┬────────┘
                                     │ 1:N
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼──────┐  ┌─────▼──────┐  ┌─────▼──────────┐
              │ Passenger  │  │StaffAssign │  │MaintenanceLog  │
              ├────────────┤  ├────────────┤  ├────────────────┤
              │ PK id      │  │ PK id      │  │ PK id          │
              │ UUID p_id  │  │ FK staff   │  │    equipment   │
              │    name    │  │ FK flight  │  │    type        │
              │ FK flight  │  │    type    │  │    status      │
              │    seat    │  └─────┬──────┘  │ FK performed_by│
              │    status  │        │         └────────────────┘
              └────────────┘        │
                          ┌────────▼────────┐
                          │     Staff       │
                          ├─────────────────┤
                          │ PK id           │
                          │ UUID staff_id   │
                          │    employee_num │
                          │    role         │
                          │    is_available │
                          └─────────────────┘

┌─────────────────┐
│FiscalAssessment │
├─────────────────┤
│ PK id           │
│ FK airport      │
│    period_type  │
│    start_date   │
│    end_date     │
│    status       │
│    revenues...  │
│    expenses...  │
│    passenger_*  │
│    flight_*     │
└────────┬────────┘
         │ 1:N
         │
    ┌────▼────────┐         ┌─────────────────┐
    │   Report    │         │   Document      │
    ├─────────────┤         ├─────────────────┤
    │ PK id       │         │ PK id           │
    │ UUID r_id   │         │ UUID d_id       │
    │ FK airport  │         │ FK airport      │
    │    type     │         │ FK assessment   │
    │    format   │         │ FK report       │
    │    content  │         │    content      │
    │ FK generated│         │    is_template  │
    └─────────────┘         └─────────────────┘
```

### Indexing Strategy

#### Primary Indexes

```python
# Airport
indexes = [
    models.Index(fields=['code']),  # Unique lookup
    models.Index(fields=['is_active', 'city']),  # Active airports by city
]

# Gate
indexes = [
    models.Index(fields=['status']),  # Status filtering
    models.Index(fields=['terminal']),  # Terminal queries
    models.Index(fields=['terminal', 'status']),  # Composite
]

# Flight
indexes = [
    models.Index(fields=['scheduled_departure']),  # Time-based queries
    models.Index(fields=['status']),  # Status filtering
    models.Index(fields=['origin', 'destination']),  # Route queries
    models.Index(fields=['airline']),  # Airline filtering
    models.Index(fields=['gate', 'status']),  # Gate utilization
]

# EventLog
indexes = [
    models.Index(fields=['timestamp']),  # Recent events
    models.Index(fields=['event_type']),  # Type filtering
    models.Index(fields=['severity']),  # Severity filtering
    models.Index(fields=['airport', 'timestamp']),  # Airport timeline
]

# FiscalAssessment
indexes = [
    models.Index(fields=['airport', 'period_type']),  # Airport periods
    models.Index(fields=['status']),  # Status filtering
    models.Index(fields=['start_date', 'end_date']),  # Date range
]
```

### Data Access Patterns

#### Optimized Queries

```python
# Use select_related for ForeignKey (SQL JOIN)
assessments = FiscalAssessment.objects.select_related('airport').all()

# Use prefetch_related for ManyToMany/Reverse FK (separate query)
flights = Flight.objects.prefetch_related('passengers', 'staff_assignments').all()

# Combine both for complex queries
flights = Flight.objects.select_related('gate').prefetch_related(
    'passengers',
    'staff_assignments__staff'
).filter(status='scheduled')

# Use annotate for aggregations
from django.db.models import Count, Sum, Avg

airport_stats = Airport.objects.annotate(
    total_gates=Count('gate'),
    available_gates=Count('gate', filter=Q(gate__status='available')),
    total_flights=Count('gate__flight'),
    avg_delay=Avg('gate__flight__delay_minutes')
)

# Use Q objects for complex filtering
from django.db.models import Q

flights = Flight.objects.filter(
    Q(status='delayed') | Q(status='cancelled'),
    scheduled_departure__date=today
)
```

### Caching Strategy

#### Cache Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Cache Hierarchy                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Per-Request Cache (Django ORM)                     │   │
│  │  - QuerySet caching within request lifecycle        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  View Cache (@cache_page)                           │   │
│  │  - Dashboard API: 5 minutes                         │   │
│  │  - Trend data: 10 minutes                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Application Cache (cache.set/get)                  │   │
│  │  - Dashboard summary: 5 minutes                     │   │
│  │  - Flight status counts: 5 minutes                  │   │
│  │  - Financial summary: 5 minutes                     │   │
│  │  - Gate utilization: 5 minutes                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Background Cache Warming (Q2 Task)                 │   │
│  │  - Runs every 30 minutes                            │   │
│  │  - Pre-populates frequently accessed data           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### Cache Keys

```python
# Dashboard summary
cache_key = f'dashboard_summary:{airport_id}'
cache.set(cache_key, data, timeout=300)

# Flight status counts
cache_key = f'flight_status_counts:{airport_id}:{date}'
cache.set(cache_key, data, timeout=300)

# Financial summary
cache_key = f'financial_summary:{airport_id}:{period}'
cache.set(cache_key, data, timeout=300)

# Invalidate on update
def invalidate_cache(model_instance):
    cache.delete_many([
        f'dashboard_summary:{model_instance.airport_id}',
        f'flight_status_counts:{model_instance.airport_id}',
        f'financial_summary:{model_instance.airport_id}',
    ])
```

---

## Integration Architecture

### External Integrations

#### Weather Service (Open-Meteo)

```
┌─────────────────┐       HTTPS        ┌─────────────────┐
│  Project Falcon   │───────────────────>│  Open-Meteo API │
│  WeatherService │<───────────────────│  (Free Tier)    │
└─────────────────┘    JSON Response   └─────────────────┘

Integration Flow:
1. Scheduled task runs every 15 minutes
2. Fetches weather for all active airports
3. Stores in WeatherCondition model
4. Triggers WeatherAlert if thresholds exceeded
```

**Implementation:**
```python
# core/weather_service.py
def fetch_weather_for_airport(airport: Airport) -> dict:
    """Fetch current weather for an airport."""
    coords = get_airport_coordinates(airport.code)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}"
    response = requests.get(url)
    return response.json()
```

#### Email Service (SMTP)

```
┌─────────────────┐       SMTP         ┌─────────────────┐
│  Project Falcon   │───────────────────>│  Email Server   │
│  (Django Email) │                    │  (SendGrid/SES) │
└─────────────────┘                    └─────────────────┘

Use Cases:
- Scheduled report delivery
- User notifications
- Password reset
- Two-factor authentication
```

**Configuration:**
```python
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
```

### Internal Integration Points

#### Signal-Based Integration

```python
# Automatic event logging
@receiver(post_save, sender=Flight)
def log_flight_change(sender, instance, **kwargs):
    """Log all flight changes to EventLog."""
    EventLog.objects.create(
        event_type='flight',
        action='update',
        description=f'Flight {instance.flight_number} status changed',
        flight=instance,
        severity='info'
    )

# Broadcast WebSocket updates
@receiver(post_save, sender=Flight)
def notify_flight_update(sender, instance, **kwargs):
    """Broadcast flight updates via WebSocket."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'flight_updates',
        {
            'type': 'flight_update',
            'data': FlightSerializer(instance).data
        }
    )
```

#### API Integration

```python
# Internal API calls (for background tasks)
from rest_framework.test import APIRequestFactory

def generate_report_internal(airport_id: int):
    """Generate report using internal API."""
    factory = APIRequestFactory()
    request = factory.get(f'/api/v1/assessments/?airport={airport_id}')
    response = FiscalAssessmentViewSet.as_view({'get': 'list'})(request)
    return response.data
```

---

## Security Architecture

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Authentication Architecture                      │
│                                                                     │
│  Browser Client                    Server                           │
│       │                              │                              │
│       │  1. POST /accounts/login/    │                              │
│       │─────────────────────────────>│                              │
│       │                              │                              │
│       │  2. Verify credentials       │                              │
│       │     - Check password hash    │                              │
│       │     - Verify 2FA (if enabled)│                              │
│       │                              │                              │
│       │  3. Create session           │                              │
│       │     - Set session cookie     │                              │
│       │     - Set CSRF token         │                              │
│       │<─────────────────────────────│                              │
│       │                              │                              │
│       │  4. Subsequent requests      │                              │
│       │     - Session cookie         │                              │
│       │     - CSRF token header      │                              │
│       │─────────────────────────────>│                              │
│       │                              │                              │
│       │  5. API requests (Token)     │                              │
│       │     - Authorization: Bearer  │                              │
│       │─────────────────────────────>│                              │
│       │                              │                              │
└─────────────────────────────────────────────────────────────────────┘
```

### Authorization Model

```
┌─────────────────────────────────────────────────────────────┐
│                  Role-Based Access Control                  │
│                                                             │
│  ┌──────────┐                                              │
│  │  Viewer  │──> Read-only access                          │
│  └──────────┘     - View dashboards                        │
│                   - View reports                           │
│                   - View flight/gate status                │
│                                                             │
│  ┌──────────┐                                              │
│  │  Editor  │──> Viewer + Create/Edit                      │
│  └──────────┘     - Create flights, gates, staff           │
│                   - Update operational data                │
│                   - Import data                            │
│                                                             │
│  ┌───────────┐                                             │
│  │ Approver  │──> Editor + Approve                         │
│  └───────────┘     - Approve fiscal assessments            │
│                   - Generate reports                       │
│                   - Export data                            │
│                                                             │
│  ┌───────────┐                                             │
│  │   Admin   │──> Approver + Full Access                  │
│  └───────────┘     - User management                       │
│                   - System configuration                   │
│                   - Delete operations                      │
│                   (Superuser only)                         │
└─────────────────────────────────────────────────────────────┘
```

### Security Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Security Defense in Depth                       │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 1: Network Security                                    │ │
│  │  - HTTPS/TLS encryption                                       │ │
│  │  - CORS configuration                                         │ │
│  │  - Allowed hosts validation                                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 2: Application Security                                │ │
│  │  - Authentication (Session + Token)                           │ │
│  │  - Authorization (RBAC)                                       │ │
│  │  - CSRF protection                                            │ │
│  │  - Rate limiting                                              │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 3: Input Security                                      │ │
│  │  - Form validation                                            │ │
│  │  - Serializer validation                                      │ │
│  │  - SQL injection prevention (ORM)                             │ │
│  │  - XSS prevention (auto-escaping)                             │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 4: Bot Protection                                      │ │
│  │  - Honeypot fields                                            │ │
│  │  - Time-based validation                                      │ │
│  │  - Decoy endpoints                                            │ │
│  │  - Pattern detection                                          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 5: Audit & Monitoring                                  │ │
│  │  - EventLog for all operations                                │ │
│  │  - Honeypot logging                                           │ │
│  │  - Failed login tracking                                      │ │
│  │  - Security alerts                                            │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Production Architecture (Render.com)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Render.com Deployment                            │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │                    Internet                                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │              Render Load Balancer                             │ │
│  │              (SSL Termination)                                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│              ┌───────────────┴───────────────┐                     │
│              ▼                               ▼                     │
│  ┌──────────────────────┐       ┌──────────────────────┐          │
│  │  Web Service         │       │  Web Service         │          │
│  │  (Daphne ASGI)       │       │  (Daphne ASGI)       │          │
│  │  - HTTP              │       │  - HTTP              │          │
│  │  - WebSocket         │       │  - WebSocket         │          │
│  └──────────┬───────────┘       └───────────┬──────────┘          │
│             │                               │                      │
│             └───────────────┬───────────────┘                      │
│                             │                                      │
│              ┌──────────────┴──────────────┐                      │
│              ▼                             ▼                      │
│  ┌──────────────────────┐       ┌──────────────────────┐          │
│  │  PostgreSQL Database │       │  Redis (Cache)       │          │
│  │  (Managed)           │       │  (Managed)           │          │
│  └──────────────────────┘       └──────────────────────┘          │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Static Files (WhiteNoise + CDN)                              │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Development Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Local Development Environment                      │
│                                                                     │
│  ┌─────────────┐                                                   │
│  │   Browser   │                                                   │
│  └──────┬──────┘                                                   │
│         │ http://localhost:8000                                    │
│         ▼                                                          │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Django Development Server (Daphne)                           │ │
│  │  - Debug mode enabled                                         │ │
│  │  - Auto-reload on changes                                     │ │
│  │  - Debug toolbar                                              │ │
│  └──────────┬────────────────────────────────────────────────────┘ │
│             │                                                      │
│    ┌────────┴────────┐                                            │
│    │                 │                                            │
│    ▼                 ▼                                            │
│  ┌────────┐      ┌────────┐                                      │
│  │ SQLite │      │ Redis  │ (optional)                           │
│  │  DB    │      │ Cache  │                                      │
│  └────────┘      └────────┘                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Performance Architecture

### Performance Optimization Strategies

#### Database Optimization

```python
# 1. Use select_related/prefetch_related
flights = Flight.objects.select_related('gate').prefetch_related('passengers')

# 2. Use database-level aggregation
from django.db.models import Count, Sum

stats = Flight.objects.aggregate(
    total=Count('id'),
    delayed=Count('id', filter=Q(status='delayed')),
    avg_delay=Avg('delay_minutes')
)

# 3. Use values/values_list for read-only queries
flight_numbers = Flight.objects.filter(status='scheduled').values_list('flight_number', flat=True)

# 4. Use iterator() for large querysets
for flight in Flight.objects.all().iterator(chunk_size=100):
    process(flight)
```

#### Caching Strategy

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# View-level caching
@cache_page(60 * 5)  # 5 minutes
def dashboard_api(request):
    return JsonResponse(data)

# Low-level caching
def get_dashboard_summary():
    cache_key = 'dashboard_summary'
    data = cache.get(cache_key)
    if data is None:
        data = calculate_dashboard_summary()
        cache.set(cache_key, data, 300)
    return data
```

#### Async Processing

```python
# Offload long-running tasks to background
from django_q.tasks import async_task

def create_report(request):
    report = Report.objects.create(...)
    async_task('core.tasks.generate_report_task', report.id)
    return redirect('report_detail', report.id)
```

### Performance Monitoring

```python
# Django Debug Toolbar (development)
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Query logging
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['debug_log'],
        },
    },
}
```

---

*Last Updated: March 24, 2026*
*Version: 1.0*
