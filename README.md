# Airport Operations Management System - Technical Documentation

> **Version:** 1.0  
> **Last Updated:** March 2026  
> **Project:** Blue Falcon - Airport Operations Management System

---

## Table of Contents

1. [Application Overview](#1-application-overview)
2. [Architecture](#2-architecture)
3. [Data Models & Database Schema](#3-data-models--database-schema)
4. [API Endpoints](#4-api-endpoints)
5. [Views & URL Routing](#5-views--url-routing)
6. [Templates & User Interface](#6-templates--user-interface)
7. [Setup & Installation](#7-setup--installation)
8. [Security Features](#8-security-features)
9. [Configuration Reference](#9-configuration-reference)

---

## 1. Application Overview

### 1.1 Introduction

The **Airport Operations Management System** (also known as Blue Falcon) is a comprehensive Django-based application designed to manage real-world airport operations. The system provides functionality for managing flights, gates, passengers, staff, aircraft, crew members, fiscal assessments, reports, and incident tracking.

### 1.2 Core Features

| Feature Category | Capabilities |
|-----------------|-------------|
| **Flight Management** | Schedule flights, track status, manage delays, assign gates |
| **Gate Management** | Track gate availability, occupancy status, maintenance scheduling |
| **Passenger Management** | Check-in tracking, boarding status, passenger records |
| **Staff Management** | Staff assignments, role tracking, availability management |
| **Aircraft Management** | Aircraft registry, maintenance tracking, capacity management |
| **Crew Management** | Crew assignments, license tracking, flight hours |
| **Fiscal Assessments** | Financial reporting, revenue/expense tracking, period-based assessments |
| **Document Management** | Document templates, generated reports, file storage |
| **Incident Tracking** | Safety incidents, operational issues, resolution workflows |
| **Maintenance Logs** | Equipment maintenance tracking, cost management |

### 1.3 Technology Stack

| Layer | Technology |
|-------|------------|
| **Framework** | Django 5.1 |
| **Database** | PostgreSQL (default) / SQLite (development) |
| **API** | Django REST Framework |
| **WebSocket** | Django Channels |
| **Authentication** | Token + Session Authentication |
| **Frontend** | HTMX, Bootstrap, Chart.js |
| **Python Version** | 3.12+ |

---

## 2. Architecture

### 2.1 Project Structure

```
airport_sim/                  # Main Django project
├── airport_sim/              # Project configuration
│   ├── settings.py           # Main settings module
│   ├── urls.py               # Root URL configuration
│   ├── asgi.py               # ASGI configuration
│   └── wsgi.py               # WSGI configuration
├── core/                     # Main application module
│   ├── models.py             # Database models
│   ├── views.py              # View classes
│   ├── forms.py              # Form validation
│   ├── serializers.py        # DRF serializers
│   ├── api.py                # API ViewSets
│   ├── urls.py               # App URL patterns
│   ├── api_urls.py           # API URL patterns
│   ├── admin.py              # Django admin configuration
│   └── consumers.py          # WebSocket consumers
└── templates/                # HTML templates
    ├── core/                 # Core app templates
    └── admin/                # Admin templates
```

### 2.2 Application Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Requests                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Django URLs (airport_sim/urls.py)            │
│  - /admin/        → Django Admin                                │
│  - /core/         → Core app views                              │
│  - /api/v1/       → REST API endpoints                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │  Views   │ │   API    │ │  Admin   │
            │(Django)  │ │  (DRF)   │ │ Interface│
            └────┬─────┘ └────┬─────┘ └──────────┘
                 │            │
                 ▼            ▼
        ┌─────────────────────────────┐
        │      Models / Database      │
        │   (PostgreSQL / SQLite)     │
        └─────────────────────────────┘
```

### 2.3 Authentication & Authorization

The application uses a dual authentication mechanism:

1. **Token Authentication** - For stateless API clients (CSRF exempt)
2. **Session Authentication** - For browser-based access (CSRF required)

```python
# Authentication classes in settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

### 2.4 Signal System

The application uses Django signals for automatic activity logging:

| Signal Type | Purpose |
|------------|--------|
| `post_save` | Log create/update operations on models |
| `post_delete` | Log delete operations |
| `pre_save` | Track changes before saving |

**Automatic Logging:**
- Fiscal Assessments: Creation, status changes, approvals
- Documents: Creation, modification, export
- Reports: Generation and export
- Staff Assignments: Assignment changes

### 2.5 Request Middleware

Thread-local storage middleware captures request context for signals:

- User information
- IP addresses
- Session data

This enables audit logging without explicitly passing request through all function calls.

---

### 2.6 WebSocket Real-time Updates

The application uses Django Channels for real-time WebSocket communication:

| Consumer | Channel Group | Purpose |
|----------|--------------|---------|
| `DashboardConsumer` | `dashboard_updates` | Real-time dashboard metrics |
| `FlightUpdatesConsumer` | `flight_updates` | Flight status changes |
| `GateStatusConsumer` | `gate_updates` | Gate availability updates |
| `EventLogConsumer` | `event_updates` | Audit log updates |

**WebSocket URL:** `/ws/`

```python
# Example WebSocket message
{
    "type": "flight_update",
    "data": {
        "flight_number": "BA123",
        "status": "delayed",
        "delay_minutes": 30
    },
    "timestamp": "2026-03-05T18:00:00Z"
}
```

**Broadcast Functions:**
- `notify_flight_update()` - Broadcast flight changes
- `notify_gate_update()` - Broadcast gate changes
- `notify_new_event()` - Broadcast new audit events

---

## 3. Data Models & Database Schema

### 3.1 Core Entities

> **Note:** Each model includes custom managers with helpful query methods for common operations.

#### 3.1.1 Airport

Represents an airport facility.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `code` | CharField(3) | IATA airport code (e.g., "LOS") |
| `name` | CharField(200) | Full airport name |
| `city` | CharField(100) | City location |
| `timezone` | CharField(50) | Airport timezone (default: UTC) |
| `is_active` | BooleanField | Active status |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last update timestamp |

**String Representation:** `"LOS - Murtala Muhammed International Airport"`

---

#### 3.1.2 Gate

Represents an airport gate with physical constraints.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `gate_id` | CharField(10) | Unique gate identifier (e.g., "A1") |
| `terminal` | CharField(10) | Terminal location |
| `capacity` | CharField(20) | Aircraft size (narrow-body/wide-body) |
| `status` | CharField(20) | Gate status (available/occupied/maintenance/closed) |

**Status Options:**
- `available` - Gate is ready for assignment
- `occupied` - Gate is currently in use
- `maintenance` - Gate is under maintenance
- `closed` - Gate is closed

**Indexes:**
- `gate_status_idx` - Status queries
- `gate_terminal_idx` - Terminal queries
- `gate_term_status_idx` - Composite for availability

---

#### 3.1.3 Flight

Represents a flight operation with scheduling and tracking.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `flight_number` | CharField(10) | Unique flight identifier |
| `airline` | CharField(50) | Operating airline |
| `origin` | CharField(3) | Departure airport code |
| `destination` | CharField(3) | Arrival airport code |
| `scheduled_departure` | DateTimeField | Planned departure time |
| `actual_departure` | DateTimeField | Actual departure time |
| `scheduled_arrival` | DateTimeField | Planned arrival time |
| `actual_arrival` | DateTimeField | Actual arrival time |
| `gate` | ForeignKey | Assigned gate |
| `status` | CharField(20) | Flight status |
| `delay_minutes` | IntegerField | Accumulated delay |
| `aircraft_type` | CharField(30) | Aircraft type |

**Status Options:**
- `scheduled` - Flight is scheduled
- `boarding` - Boarding in progress
- `departed` - Flight has departed
- `arrived` - Flight has arrived
- `delayed` - Flight is delayed
- `cancelled` - Flight was cancelled

**Indexes:**
- `flight_depart_idx` - Scheduled departures
- `flight_status_idx` - Status filtering
- `flight_route_idx` - Origin/destination queries
- `flight_airline_idx` - Airline filtering

---

#### 3.1.4 Passenger

Represents a passenger with booking and boarding information.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `passenger_id` | UUIDField | Unique passenger ID |
| `first_name` | CharField(100) | Passenger first name |
| `last_name` | CharField(100) | Passenger last name |
| `passport_number` | CharField(20) | Passport number (unique) |
| `email` | EmailField | Contact email |
| `phone` | CharField(20) | Contact phone |
| `flight` | ForeignKey | Associated flight |
| `seat_number` | CharField(5) | Assigned seat |
| `status` | CharField(20) | Passenger status |
| `checked_bags` | IntegerField | Number of checked bags |

**Status Options:**
- `checked_in` - Passenger has checked in
- `boarded` - Passenger has boarded
- `arrived` - Passenger has arrived
- `no_show` - Passenger did not show up

---

#### 3.1.5 Staff

Represents airport or airline staff members.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `staff_id` | UUIDField | Unique staff identifier |
| `first_name` | CharField(100) | Staff first name |
| `last_name` | CharField(100) | Staff last name |
| `employee_number` | CharField(20) | Employee ID (unique) |
| `role` | CharField(20) | Staff role |
| `certification` | CharField(200) | Required certifications |
| `is_available` | BooleanField | Availability status |
| `email` | EmailField | Contact email |
| `phone` | CharField(20) | Contact phone |

**Role Options:**
- `pilot` - Pilot
- `co_pilot` - Co-pilot
- `cabin_crew` - Cabin crew
- `ground_crew` - Ground crew
- `security` - Security personnel
- `cleaning` - Cleaning staff
- `maintenance` - Maintenance personnel

---

#### 3.1.6 StaffAssignment

Tracks staff assignments to flights for conflict detection.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `staff` | ForeignKey | Staff member |
| `flight` | ForeignKey | Assigned flight |
| `assignment_type` | CharField(20) | Type of assignment |
| `assigned_at` | DateTimeField | Assignment timestamp |

**Unique Constraint:** `(staff, flight, assignment_type)`

---

#### 3.1.7 EventLog

Audit log for all airport operations events.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `event_id` | UUIDField | Unique event identifier |
| `timestamp` | DateTimeField | Event timestamp |
| `event_type` | CharField(50) | Event category |
| `description` | TextField | Event description |
| `user` | ForeignKey | User who performed the action |
| `action` | CharField(20) | Action type performed |
| `ip_address` | CharField(45) | Client IP address |
| `flight` | ForeignKey | Associated flight (optional) |
| `severity` | CharField(20) | Event severity |
| `created_at` | DateTimeField | Creation timestamp |

**Action Types:**
- `create` - Object created
- `update` - Object updated
- `delete` - Object deleted
- `login` - User login
- `logout` - User logout
- `view` - Object viewed
- `approve` - Object approved
- `reject` - Object rejected
- `export` - Data exported
- `other` - Other actions

**Severity Options:**
- `info` - Informational
- `warning` - Warning
- `error` - Error

**Indexes:**
- `event_timestamp_idx` - Recent events
- `event_type_idx` - Event type queries
- `event_severity_idx` - Severity filtering

---

### 3.2 Financial Entities

#### 3.2.1 FiscalAssessment

Represents a fiscal/financial assessment for an airport over a period.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `airport` | ForeignKey | Assessed airport |
| `period_type` | CharField(20) | Assessment period |
| `start_date` | DateField | Period start |
| `end_date` | DateField | Period end |
| `status` | CharField(20) | Assessment status |
| `total_revenue` | DecimalField(15,2) | Total revenue |
| `total_expenses` | DecimalField(15,2) | Total expenses |
| `net_profit` | DecimalField(15,2) | Net profit |

**Revenue Fields:**
- `fuel_revenue` - Fuel services
- `parking_revenue` - Parking facilities
- `retail_revenue` - Retail/concession
- `landing_fees` - Landing fees
- `cargo_revenue` - Cargo services
- `other_revenue` - Other revenue

**Expense Fields:**
- `security_costs` - Security costs
- `maintenance_costs` - Maintenance costs
- `operational_costs` - General operations
- `staff_costs` - Staff-related costs
- `utility_costs` - Utilities
- `other_expenses` - Other expenses

**Operational Metrics:**
- `passenger_count` - Total passengers
- `flight_count` - Total flights

**Status Options:**
- `draft` - Initial draft
- `in_progress` - Under review
- `completed` - Review completed
- `approved` - Approved
- `rejected` - Rejected

---

#### 3.2.2 Report

Represents a generated report for airport operations.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `report_id` | UUIDField | Unique report ID |
| `airport` | ForeignKey | Associated airport |
| `report_type` | CharField(30) | Type of report |
| `title` | CharField(200) | Report title |
| `description` | TextField | Report description |
| `period_start` | DateField | Reporting period start |
| `period_end` | DateField | Reporting period end |
| `format` | CharField(10) | Output format |
| `content` | JSONField | Report data |
| `generated_by` | CharField(100) | Generator username |
| `is_generated` | BooleanField | Generation status |
| `generated_at` | DateTimeField | Generation timestamp |

**Report Types:**
- `fiscal_summary` - Financial summary
- `operational` - Operations report
- `passenger` - Passenger statistics
- `financial` - Financial details
- `performance` - Performance metrics
- `compliance` - Compliance report

**Output Formats:**
- `html` - HTML format
- `pdf` - PDF format
- `csv` - CSV format
- `json` - JSON format

---

#### 3.2.3 Document

Represents a document template or generated document.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `document_id` | UUIDField | Unique document ID |
| `name` | CharField(200) | Document name |
| `document_type` | CharField(30) | Type of document |
| `airport` | ForeignKey | Associated airport |
| `fiscal_assessment` | ForeignKey | Related assessment |
| `report` | ForeignKey | Related report |
| `file_path` | CharField(500) | File path |
| `content` | JSONField | Document content |
| `is_template` | BooleanField | Template flag |
| `created_by` | CharField(100) | Creator username |

**Document Types:**
- `invoice`, `receipt`, `certificate`, `permit`
- `report`, `agreement`, `memo`, `other`

---

### 3.3 Aircraft & Crew Entities

#### 3.3.1 Aircraft

Represents an individual aircraft with registration and capacity.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `tail_number` | CharField(20) | Registration (unique) |
| `aircraft_type` | CharField(20) | Type category |
| `model` | CharField(50) | Specific model |
| `manufacturer` | CharField(50) | Manufacturer |
| `capacity_passengers` | IntegerField | Passenger capacity |
| `capacity_cargo` | DecimalField(10,2) | Cargo capacity (kg) |
| `status` | CharField(20) | Operational status |
| `registration_country` | CharField(50) | Country of registration |
| `year_manufactured` | IntegerField | Year of manufacture |
| `last_maintenance_date` | DateField | Last maintenance |
| `next_maintenance_due` | DateField | Next maintenance due |
| `total_flight_hours` | DecimalField(10,2) | Total flight hours |

**Aircraft Types:**
- `narrow_body` - Single-aisle aircraft
- `wide_body` - Twin-aisle aircraft
- `regional` - Regional jets
- `cargo` - Cargo aircraft

**Status Options:**
- `active`, `maintenance`, `retired`, `stored`

---

#### 3.3.2 CrewMember

Represents crew members for flight operations.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `employee_id` | CharField(20) | Employee ID (unique) |
| `first_name` | CharField(100) | First name |
| `last_name` | CharField(100) | Last name |
| `crew_type` | CharField(25) | Position type |
| `license_number` | CharField(50) | License number |
| `license_expiry` | DateField | License expiration |
| `status` | CharField(20) | Availability status |
| `total_flight_hours` | DecimalField(10,2) | Flight hours |
| `rank` | CharField(30) | Seniority rank |
| `base_airport` | ForeignKey | Home airport |
| `email` | EmailField | Contact email |
| `phone` | CharField(20) | Contact phone |
| `hire_date` | DateField | Date of hire |
| `date_of_birth` | DateField | Date of birth |

**Crew Types:**
- `pilot`, `first_officer`, `flight_attendant`
- `lead_flight_attendant`, `flight_engineer`

**Status Options:**
- `available`, `assigned`, `on_leave`, `unavailable`

---

### 3.4 Maintenance & Incident Entities

#### 3.4.1 MaintenanceLog

Tracks maintenance activities for gates and equipment.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `equipment_type` | CharField(30) | Type of equipment |
| `equipment_id` | CharField(50) | Equipment identifier |
| `maintenance_type` | CharField(20) | Type of maintenance |
| `description` | TextField | Work description |
| `status` | CharField(20) | Maintenance status |
| `started_at` | DateTimeField | Start time |
| `completed_at` | DateTimeField | Completion time |
| `performed_by` | ForeignKey | Staff member |
| `parts_replaced` | JSONField | Parts replaced |
| `cost` | DecimalField(12,2) | Maintenance cost |
| `notes` | TextField | Additional notes |

**Equipment Types:**
- `gate`, `ground_equipment`, `baggage_system`
- `security_equipment`, `hvac`, `lighting`, `other`

**Maintenance Types:**
- `routine`, `scheduled`, `unscheduled`, `inspection`, `repair`

**Status Options:**
- `pending`, `in_progress`, `completed`, `cancelled`

---

#### 3.4.2 IncidentReport

Tracks safety and operational incidents.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `incident_id` | UUIDField | Unique incident ID |
| `incident_type` | CharField(20) | Incident category |
| `severity` | CharField(20) | Severity level |
| `status` | CharField(20) | Current status |
| `title` | CharField(200) | Incident title |
| `description` | TextField | Detailed description |
| `location` | CharField(100) | Incident location |
| `reported_by` | ForeignKey | Reporting staff |
| `assigned_to` | ForeignKey | Assigned staff |
| `date_occurred` | DateField | Occurrence date |
| `date_reported` | DateTimeField | Report date |
| `date_resolved` | DateTimeField | Resolution date |
| `root_cause` | TextField | Root cause analysis |
| `corrective_action` | TextField | Corrective measures |
| `related_flight` | ForeignKey | Related flight |
| `related_gate` | ForeignKey | Related gate |
| `attachments` | JSONField | Attachment references |

**Incident Types:**
- `safety`, `security`, `operational`, `environmental`, `equipment`, `other`

**Severity Levels:**
- `low`, `medium`, `high`, `critical`

**Status Options:**
- `reported`, `investigating`, `resolved`, `closed`

---

## 4. API Endpoints

### 4.1 Base URL

```
/api/v1/
```

### 4.2 Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/airports/` | GET, POST | List/Create airports |
| `/api/v1/airports/{id}/` | GET, PUT, DELETE | Retrieve/Update/Delete airport |
| `/api/v1/gates/` | GET, POST | List/Create gates |
| `/api/v1/gates/{id}/` | GET, PUT, DELETE | Retrieve/Update/Delete gate |
| `/api/v1/flights/` | GET, POST | List/Create flights |
| `/api/v1/flights/{id}/` | GET, PUT, DELETE | Retrieve/Update/Delete flight |
| `/api/v1/passengers/` | GET, POST | List/Create passengers |
| `/api/v1/passengers/{id}/` | GET, PUT, DELETE | Retrieve/Update/Delete passenger |
| `/api/v1/staff/` | GET, POST | List/Create staff |
| `/api/v1/staff/{id}/` | GET, PUT, DELETE | Retrieve/Update/Delete staff |
| `/api/v1/staff-assignments/` | GET, POST | List/Create staff assignments |
| `/api/v1/staff-assignments/{id}/` | GET, PUT, DELETE | Manage staff assignment |
| `/api/v1/events/` | GET | List event logs (read-only) |
| `/api/v1/events/{id}/` | GET | Retrieve event log details |
| `/api/v1/assessments/` | GET, POST | List/Create fiscal assessments |
| `/api/v1/assessments/{id}/` | GET, PUT, DELETE | Manage assessment |
| `/api/v1/assessments/{id}/approve/` | POST | Approve/Reject assessment |
| `/api/v1/activity/` | GET | List activity logs |
| `/api/v1/aircraft/` | GET, POST | List/Create aircraft |
| `/api/v1/aircraft/{id}/` | GET, PUT, DELETE | Manage aircraft |
| `/api/v1/crew/` | GET, POST | List/Create crew members |
| `/api/v1/crew/{id}/` | GET, PUT, DELETE | Manage crew member |
| `/api/v1/maintenance/` | GET, POST | List/Create maintenance logs |
| `/api/v1/maintenance/{id}/` | GET, PUT, DELETE | Manage maintenance log |
| `/api/v1/incidents/` | GET, POST | List/Create incident reports |
| `/api/v1/incidents/{id}/` | GET, PUT, DELETE | Manage incident report |
| `/api/v1/reports/` | GET, POST | List/Create reports |
| `/api/v1/reports/{id}/` | GET, PUT, DELETE | Manage report |
| `/api/v1/documents/` | GET, POST | List/Create documents |
| `/api/v1/documents/{id}/` | GET, PUT, DELETE | Manage document |

### 4.3 Custom Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/dashboard-summary/` | GET | Dashboard aggregate data |
| `/api/v1/metrics/?period=day\|week\|month\|year` | GET | Operational metrics |

### 4.4 Query Parameters

Common query parameters across endpoints:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `search` | Text search | `?search=London` |
| `ordering` | Sort field | `?ordering=-created_at` |
| `page` | Page number | `?page=2` |
| `page_size` | Items per page (default: 50) | `?page_size=25` |

### 4.5 Model-Specific Filters

#### Gates
| Parameter | Description |
|-----------|-------------|
| `terminal` | Filter by terminal (A, B, C) |
| `status` | Filter by status |
| `capacity` | Filter by capacity |

#### Flights
| Parameter | Description |
|-----------|-------------|
| `status` | Filter by flight status |
| `airline` | Filter by airline |
| `origin` | Filter by origin airport |
| `destination` | Filter by destination airport |
| `date_from` | Filter from date |
| `date_to` | Filter to date |
| `gate` | Filter by assigned gate |

#### Staff
| Parameter | Description |
|-----------|-------------|
| `role` | Filter by role |
| `is_available` | Filter by availability |

#### Event Logs
| Parameter | Description |
|-----------|-------------|
| `event_type` | Filter by event type |
| `severity` | Filter by severity |
| `flight` | Filter by related flight |

### 4.6 Filtering Examples

```bash
# Filter flights by status
GET /api/v1/flights/?status=delayed

# Filter gates by terminal
GET /api/v1/gates/?terminal=A

# Filter staff by role
GET /api/v1/staff/?role=security

# Filter by date range
GET /api/v1/flights/?date_from=2026-01-01&date_to=2026-01-31

# Search flights
GET /api/v1/flights/?search=BA

# Order by departure time
GET /api/v1/flights/?ordering=scheduled_departure
```

### 4.6 Authentication

Include the token in request headers:

```bash
Authorization: Token <your-token-here>
```

---

## 5. Views & URL Routing

### 5.1 URL Patterns

#### Core App URLs (`/core/`)

| URL | View | Description |
|-----|------|-------------|
| `/core/` | `DashboardView` | Main dashboard with metrics |
| `/core/dashboard/` | `DashboardView` | Alternative dashboard URL |
| `/core/activity/` | `ActivityLogListView` | Activity/event log viewer |
| `/core/assessments/` | `FiscalAssessmentListView` | List all fiscal assessments |
| `/core/assessments/create/` | `FiscalAssessmentCreateView` | Create new assessment |
| `/core/assessments/<id>/` | `FiscalAssessmentDetailView` | View assessment details |
| `/core/assessments/<id>/edit/` | `FiscalAssessmentUpdateView` | Edit assessment |
| `/core/assessments/<id>/approve/` | `FiscalAssessmentApproveView` | Approve/Reject assessment |
| `/core/assessments/<id>/print/` | `FiscalAssessmentPrintView` | Printable view |
| `/core/reports/` | `ReportListView` | List all reports |
| `/core/reports/create/` | `ReportCreateView` | Create new report |
| `/core/reports/<id>/` | `ReportDetailView` | View report details |
| `/core/reports/<id>/export/` | `ReportExportView` | Export report |
| `/core/documents/` | `DocumentListView` | List all documents |
| `/core/documents/create/` | `DocumentCreateView` | Create new document |
| `/core/documents/<id>/` | `DocumentDetailView` | View document details |
| `/core/documents/<id>/export/` | `DocumentExportView` | Export document |

### 5.2 View Classes

#### Fiscal Assessment Views

```python
# List view with filtering and pagination
class FiscalAssessmentListView(LoginRequiredMixin, View):
    """Displays table of fiscal assessments with filters."""
    template_name = "core/fiscal_assessment_list.html"
    
# Detail view
class FiscalAssessmentDetailView(LoginRequiredMixin, View):
    """Shows comprehensive assessment details."""
    template_name = "core/fiscal_assessment_detail.html"
    
# Create/Update views with form validation
class FiscalAssessmentCreateView(LoginRequiredMixin, View)
class FiscalAssessmentUpdateView(LoginRequiredMixin, View)
    
# Approval with rate limiting and permissions
class FiscalAssessmentApproveView(LoginRequiredMixin, View):
    """Includes rate limiting (5 min), permission checks, audit logging."""
```

---

## 6. Templates & User Interface

### 6.1 Template Structure

```
templates/
├── admin/
│   └── csv_form.html              # Admin CSV upload form
├── common/
│   ├── list_view.html             # Generic list view
│   └── partials/                 # Reusable partials
│       ├── data_table.html
│       ├── filter_form.html
│       └── page_header.html
├── core/
│   ├── fiscal_assessment_list.html
│   ├── fiscal_assessment_detail.html
│   ├── fiscal_assessment_form.html
│   ├── fiscal_assessment_print.html
│   ├── report_list.html
│   ├── report_detail.html
│   ├── report_form.html
│   ├── document_list.html
│   ├── document_detail.html
│   ├── document_form.html
│   ├── dashboard.html
│   ├── activity_log_list.html
│   └── templatetags/
│       └── core_filters.py         # Custom template filters
├── registration/
│   └── login.html                  # Login page
└── simulation/
    └── dashboard.html              # Simulation dashboard
```

### 6.2 UI Components

#### Common Templates

The application includes reusable templates in `templates/common/`:

| Template | Purpose |
|----------|---------|
| `list_view.html` | Generic list view with filters and pagination |
| `partials/data_table.html` | Reusable data table component |
| `partials/filter_form.html` | Reusable filter form component |
| `partials/page_header.html` | Page header with title and actions |

#### Metrics Cards

Displays key performance indicators:
- Total flights, passengers, staff
- Gate utilization percentage
- Delayed flight count
- Recent events summary

#### Data Tables

- Sortable columns
- Pagination (configurable 10-100 items)
- Filter by status, type, date range
- Search functionality

#### Forms

- Multi-field fiscal assessment forms
- Date pickers for period selection
- Financial input fields with validation
- Error display with field highlighting

### 6.3 Template Filters

Located in [`core/templatetags/core_filters.py`](core/templatetags/core_filters.py):

```python
@register.filter
def currency(value):  # Format as currency
    return f"${value:,.2f}"

@register.filter
def percentage(value):  # Format as percentage
    return f"{value:.1f}%"
```

---

## 7. Setup & Installation

### 7.1 Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.12+ |
| PostgreSQL | 13+ (production) |
| pip | Latest |

### 7.2 Installation Steps

#### 1. Clone and Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

#### 2. Install Dependencies

```bash
pip install django==5.1 psycopg2-binary djangorestframework django-cors-headers channels django-environ
```

#### 3. Environment Configuration

Create `.env` file:

```env
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3

# Or PostgreSQL for production
# DATABASE_ENGINE=django.db.backends.postgresql
# DATABASE_NAME=airport_db
# DATABASE_USER=postgres
# DATABASE_PASSWORD=your-password
# DATABASE_HOST=localhost
# DATABASE_PORT=5432

# Optional: Redis for channels (production)
# REDIS_URL=redis://127.0.0.1:6379/1
```

#### 4. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

#### 5. Run Development Server

```bash
python manage.py runserver
```

Access the application at `http://localhost:8000/`

### 7.3 Management Commands

```bash
# Set up default groups and permissions
python manage.py setup_permissions

# Create initial airport data
python manage.py setup_airport

# Load sample data
python manage.py seed_airport --flights=80 --days=1
```

**setup_permissions** - Creates default groups (`editors`, `approvers`) and assigns appropriate permissions to them. This command is typically run after the initial migration to set up the role-based access control system.

---

## 8. Security Features

### 8.1 Authentication & Authorization

| Feature | Implementation |
|---------|---------------|
| **Token Authentication** | Stateless API access via DRF TokenAuthentication |
| **Session Authentication** | Browser-based access with CSRF protection |
| **Permission Classes** | `IsAuthenticated` on all views |
| **Login Required** | `LoginRequiredMixin` on all views |

### 8.2 Role-Based Access Control (RBAC)

The application implements a least-privilege access control system:

| Role | Description | Group Required |
|------|-------------|----------------|
| **Viewer** | View-only access (default) | None |
| **Editor** | Create and edit data | `editors` |
| **Approver** | Approve assessments | `approvers` |
| **Admin** | Full access | Superuser only |

**Key Points:**
- New users have minimal permissions by default
- Admin features restricted to superusers
- Specific features require specific permissions/groups
- Role bypass is prevented at all levels

### 8.3 Automatic Group Setup

On application startup, the system automatically creates default groups:
- `editors` - Permissions for creating and editing content
- `approvers` - Permissions for approval workflows

This ensures the permission system works out of the box without manual setup.

### 8.4 Input Validation

```python
# Form-based validation (core/forms.py)
class FiscalAssessmentCreateForm(forms.Form):
    """All fields validated with type checking"""
    fuel_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2,
        required=False, min_value=0
    )
```

### 8.5 Mass Assignment Protection

Explicit field allowlisting in forms:

```python
FISCAL_ASSESSMENT_UPDATE_FIELDS = [
    'airport', 'period_type', 'start_date', 'end_date',
    'status', 'fuel_revenue', 'parking_revenue', ...
]
```

### 8.6 Honeypot Form Protection

The application implements honeypot-based bot detection using [`core/honeypot.py`](core/honeypot.py):

**Features:**
- Hidden honeypot fields that bots may fill out (but humans cannot see)
- Time-based submission validation (fast submissions = bots)
- Token-based validation to ensure forms were properly loaded

**Implementation:**

```python
from core.honeypot import HoneypotFieldMixin

class MyForm(HoneypotFieldMixin, forms.Form):
    """Form with honeypot protection"""
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    # Honeypot fields are automatically added
```

**Honeypot Fields:**
- `website_url` - Hidden field that should remain empty
- `contact_email` - Hidden email field
- `phone_number` - Hidden phone field
- `_form_ts` - Timestamp token
- `_form_tk` - Validation token

**Configuration:**

```python
# settings.py
HONEYPOT_MIN_SUBMIT_TIME = 2  # Minimum seconds before submission
HONEYPOT_FIELD_NAME = 'website_url'
HONEYPOT_EMAIL_NAME = 'contact_email'
HONEYPOT_ENABLED = True
```

### 8.7 Honeypot Middleware

The application includes [`HoneypotMiddleware`](core/middleware.py:78) to detect and respond to honeypot attacks:

**Features:**
- Detects access to suspicious/honeypot paths
- Rate limiting to prevent aggressive scanning
- Obfuscated responses to confuse attackers
- Comprehensive logging for security analysis

**Honeypot Paths (trap URLs):**
- `/admin/secret-panel/`
- `/api/internal/debug/`
- `/api/backup/`
- `/wp-admin/`
- `/phpmyadmin/`
- `/server-status/`

**Configuration:**

```python
# settings.py
HONEYPOT_ENABLED = True
HONEYPOT_RATE_LIMIT_WINDOW = 60  # seconds
HONEYPOT_RATE_LIMIT_MAX = 3  # max triggers per window
HONEYPOT_PATHS = [
    '/admin/secret-panel/',
    '/api/internal/debug/',
    '/wp-admin/',
]
```

### 8.8 Advanced Permissions System

The application implements a comprehensive role-based access control system in [`core/permissions.py`](core/permissions.py):

**User Roles:**

| Role | Description | Group Required | Privileges |
|------|-------------|----------------|------------|
| Viewer | View-only access (default) | None | Read data |
| Editor | Create and edit data | `editors` | Create, Update |
| Approver | Approve assessments | `approvers` | Create, Update, Approve |
| Admin | Full access | Superuser only | All operations |

**Permission Classes:**

```python
from core.permissions import (
    IsAdminUser,
    IsEditorOrAbove,
    IsApproverOrAbove,
    IsViewerOrAbove,
)

# Usage in API views
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsEditorOrAbove]
```

**Permission Functions:**
- `can_create_assessment(user)` - Check if user can create fiscal assessments
- `can_edit_assessment(user)` - Check if user can edit fiscal assessments
- `can_approve_assessment(user)` - Check if user can approve fiscal assessments
- `can_access_admin(user)` - Check if user can access Django admin
- `has_role(user, role)` - Check if user has specific role
- `has_minimum_role(user, role)` - Check if user has minimum role level

**Key Security Features:**
- All DELETE operations require admin (superuser) - cannot be bypassed
- Permission bypass is prevented at all levels
- Comprehensive audit logging for permission denials

### 8.9 Rate Limiting

Approval actions include rate limiting:

```python
class FiscalAssessmentApproveView(View):
    RATE_LIMIT_SECONDS = 300  # 5 minutes between approvals
```

### 8.10 Audit Logging

All approval actions logged:

```python
audit_logger.info(
    f"ASSESSMENT_APPROVED: user={user}, "
    f"assessment_id={id}, airport={airport}"
)
```

### 8.11 Security Settings

Configured in [`airport_sim/settings.py`](airport_sim/settings.py):

```python
# CSRF protection
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True

# SSL redirect (production)
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
```

---

## 9. Configuration Reference

### 9.1 Settings Overview

Key settings in [`airport_sim/settings.py`](airport_sim/settings.py):

| Setting | Default | Description |
|---------|---------|-------------|
| `DEBUG` | `False` | Debug mode |
| `SECRET_KEY` | - | Django secret key |
| `ALLOWED_HOSTS` | `[]` | Allowed hostnames |
| `DATABASE_ENGINE` | `postgresql` | Database backend |
| `TIME_ZONE` | `UTC` | Server timezone |
| `USE_TZ` | `True` | Enable timezone support |

### 9.2 REST Framework Settings

```python
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'PAGE_SIZE': 50,
}
```

### 9.3 File Upload Settings

```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_FILE_EXTENSIONS = ['.csv', '.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.doc', '.docx', '.xls', '.xlsx']
ALLOWED_MIME_TYPES = ['text/csv', 'text/plain', 'application/pdf', ...]

# Chunked upload settings
CHUNKED_UPLOAD_ENABLED = True
CHUNKED_UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1MB
```

### 9.4 CORS Settings

```python
CORS_ALLOWED_ORIGINS = []  # Empty by default - must be configured in production
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['Content-Type', 'Authorization']
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours
```

### 9.5 Django Channels (WebSocket)

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        # Production: Use Redis
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
    }
}
```

### 9.6 Rate Limiting

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/day',
        'user': '10000/day',
    }
}
```

---

## Appendix A: Quick Reference

### Common Commands

```bash
# Development
python manage.py runserver

# Database
python manage.py migrate
python manage.py makemigrations
python manage.py showmigrations

# Admin
python manage.py createsuperuser
python manage.py changepassword <username>

# Testing
python manage.py test
```

### Key URLs

| Path | Description |
|------|-------------|
| `/admin/` | Django admin interface |
| `/core/assessments/` | Fiscal assessments list |
| `/core/reports/` | Reports list |
| `/api/v1/` | API endpoint base |
| `/api/v1/flights/` | Flights API |
| `/api/v1/dashboard-summary/` | Dashboard data |

---

## Appendix B: Database Indexes Summary

The application uses strategic indexes for performance:

| Model | Index Name | Fields |
|-------|------------|--------|
| Gate | `gate_status_idx` | status |
| Gate | `gate_terminal_idx` | terminal |
| Gate | `gate_term_status_idx` | terminal, status |
| Flight | `flight_depart_idx` | scheduled_departure |
| Flight | `flight_status_idx` | status |
| Flight | `flight_route_idx` | origin, destination |
| Flight | `flight_gate_status_idx` | gate, status, scheduled_departure |
| Passenger | `pass_flight_status_idx` | flight, status |
| Staff | `staff_role_idx` | role |
| Staff | `staff_avail_role_idx` | is_available, role |
| EventLog | `event_timestamp_idx` | -timestamp |
| EventLog | `event_type_idx` | event_type |
| EventLog | `event_severity_idx` | severity |
| FiscalAssessment | `fiscal_airport_date_idx` | airport, -start_date |

---

###Alex Alagoa Biobelemo
