# Blue Falcon - Airport Operations Management System

> **Version:** 1.0  
> **Last Updated:** March 15, 2026  
> **Status:** Production Ready  
> **Category:** Aviation Management System  

---

## Table of Contents

1. [Introduction](#introduction)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Quick Start](#quick-start)
5. [System Architecture](#system-architecture)
6. [Core Modules](#core-modules)
7. [API Reference](#api-reference)
8. [Security](#security)
9. [Deployment](#deployment)
10. [Development](#development)
11. [Troubleshooting](#troubleshooting)
12. [Support](#support)

---

## Introduction

**Blue Falcon** is a comprehensive, enterprise-grade Airport Operations Management System built with Django 5.1. It provides a complete solution for managing real-world airport operations including flight scheduling, gate management, passenger tracking, staff assignments, fiscal assessments, and regulatory compliance.

### Purpose

The system is designed to:
- Centralize all airport operational data in a single platform
- Provide real-time visibility into airport operations via dashboards and WebSocket updates
- Enable data-driven decision making through comprehensive analytics and reporting
- Ensure regulatory compliance through audit logging and approval workflows
- Support multiple airports with comparative analytics
- Provide public-facing portals for flight status and baggage tracking

### Target Users

| User Type | Access Level | Capabilities |
|-----------|-------------|--------------|
| **Administrators** | Full Access | System configuration, user management, all CRUD operations |
| **Approvers** | Elevated Access | Review and approve fiscal assessments, generate reports |
| **Editors** | Standard Access | Create and edit operational data (flights, gates, staff) |
| **Viewers** | Read-Only | View dashboards, reports, and operational data |
| **Public Users** | Limited Access | Flight status portal, baggage tracking (no authentication required) |

---

## Key Features

### Flight Operations Management
- **Flight Scheduling**: Create, update, and track flights with complete itinerary information
- **Status Tracking**: Real-time flight status updates (scheduled, boarding, departed, arrived, delayed, cancelled)
- **Gate Assignment**: Automatic and manual gate assignment with conflict detection
- **Delay Management**: Track and report delay minutes with root cause analysis

### Gate Management
- **Real-time Availability**: Live gate status tracking (available, occupied, maintenance, closed)
- **Terminal Organization**: Gates organized by terminal with capacity classification
- **Utilization Analytics**: Gate occupancy rates and turnover metrics

### Passenger Management
- **Check-in Tracking**: Passenger check-in status and boarding progress
- **Baggage Tracking**: Checked baggage count and tracking per passenger
- **UUID-based Identification**: Unique passenger identifiers for privacy compliance

### Staff & Crew Management
- **Staff Registry**: Complete staff database with roles, certifications, and contact information
- **Assignment Tracking**: Staff-to-flight assignments with conflict detection
- **Role-based Access**: Staff roles (pilot, co-pilot, cabin crew, ground crew, security, maintenance, cleaning)
- **Availability Management**: Track staff availability and assignments

### Aircraft & Maintenance
- **Aircraft Registry**: Complete aircraft database with tail numbers, models, and capacities
- **Maintenance Logs**: Track maintenance activities with cost tracking
- **Flight Hours Tracking**: Monitor total flight hours and maintenance schedules

### Fiscal Management
- **Financial Assessments**: Period-based fiscal assessments (daily, weekly, monthly, quarterly, yearly)
- **Revenue Tracking**: Multiple revenue streams (fuel, parking, retail, landing fees, cargo)
- **Expense Management**: Comprehensive expense tracking (security, maintenance, operations, staff, utilities)
- **Approval Workflows**: Multi-stage approval process with audit trails
- **Profit/Loss Analysis**: Automated calculation of net profit and operational metrics

### Reporting & Analytics
- **Report Generation**: Automated report generation (fiscal, operational, passenger, financial, compliance)
- **Multiple Formats**: Export to HTML, PDF, CSV, JSON
- **Scheduled Reports**: Automated report scheduling (daily, weekly, monthly)
- **Email Delivery**: Automatic email delivery of scheduled reports
- **Analytics Dashboard**: Interactive charts and metrics with Chart.js visualization

### Real-time Features
- **WebSocket Updates**: Live dashboard updates without page refresh
- **Flight Status Streaming**: Real-time flight status changes broadcast to connected clients
- **Gate Status Updates**: Live gate availability updates
- **Event Logging**: Real-time audit log streaming
- **Browser Notifications**: Push notifications for important events

### Public Portals
- **Flight Status Portal**: Public-facing flight status lookup (no authentication required)
- **Baggage Tracking**: Public baggage status tracking

### Integration Features
- **RESTful API**: Complete API v1 with versioning support
- **API Documentation**: Interactive Swagger UI and ReDoc documentation
- **Webhook Support**: Event-driven integrations via WebSocket
- **Weather Service**: Open-Meteo API integration for airport weather data

---

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | Django | 5.1.7 |
| **API Framework** | Django REST Framework | 3.15.2 |
| **WebSocket** | Django Channels | 4.2.0 |
| **Background Tasks** | Django-Q2 | 1.9.0 |
| **Caching** | Django Cache Framework | Built-in |
| **Authentication** | Django Auth + Token Auth | Built-in |
| **Two-Factor Auth** | django-two-factor-auth | 1.16.0 |

### Database
| Component | Technology | Version |
|-----------|-----------|---------|
| **Production** | PostgreSQL | 12+ (via psycopg2-binary) |
| **Development** | SQLite | 3.x (built-in) |

### Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| **CSS Framework** | Bootstrap | 5.x |
| **Dynamic Loading** | HTMX | Latest |
| **Charts** | Chart.js | Latest |
| **Icons** | Font Awesome | Latest |

### Infrastructure
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **WSGI/ASGI Server** | Daphne | WebSocket + HTTP |
| **Production Server** | Gunicorn | WSGI HTTP server |
| **Static Files** | WhiteNoise | Static file serving |
| **Deployment** | Render.com | Cloud hosting |
| **Message Broker** | Redis | Django-Q2 backend, caching |

### Development Tools
| Tool | Purpose |
|------|---------|
| **django-debug-toolbar** | Development debugging |
| **drf-spectacular** | API documentation (OpenAPI/Swagger) |
| **django-cors-headers** | CORS management |
| **python-dotenv** | Environment variable management |

---

## Quick Start

### Prerequisites

- Python 3.12 or higher
- PostgreSQL 12+ (for production) or SQLite (for development)
- Redis (optional, for background tasks and caching)
- pip and virtualenv

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Blue Falcon"
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Production Environment:**
```env
SECRET_KEY=<secure-random-key>
DEBUG=False
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=blue_falcon
DATABASE_USER=postgres
DATABASE_PASSWORD=secure-password
ALLOWED_HOSTS=your-domain.com
```

#### 5. Run Migrations

```bash
python manage.py migrate
```

#### 6. Create Superuser

```bash
python create_superuser.py
# Or manually:
python manage.py createsuperuser
```

#### 7. Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### 8. Start Development Server

```bash
# For HTTP only
python manage.py runserver

# For WebSocket support (ASGI)
daphne airport_sim.asgi:application
```

#### 9. Start Background Task Processor (Optional)

```bash
python manage.py qcluster
```

#### 10. Access the Application

- **Dashboard**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐ │
│  │  Browser │  │  Mobile  │  │   API    │  │  Public Portal │ │
│  │   (HTTP) │  │   App    │  │  Client  │  │   (Flight Status)│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘ │
└───────┼─────────────┼─────────────┼────────────────┼──────────┘
        │             │             │                │
        └─────────────┴──────┬──────┴────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Application Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Django ASGI/WSGI Application                │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐ │  │
│  │  │   Views    │  │   API      │  │   WebSocket        │ │  │
│  │  │  (Django)  │  │  (DRF)     │  │   Consumers        │ │  │
│  │  └─────┬──────┘  └─────┬──────┘  └──────────┬─────────┘ │  │
│  └────────┼────────────────┼────────────────────┼───────────┘  │
│           │                │                    │              │
│  ┌────────▼────────────────▼────────────────────▼───────────┐  │
│  │                 Business Logic Layer                      │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────┐  │  │
│  │  │  Models    │  │  Services  │  │   Tasks (Q2)       │  │  │
│  │  │            │  │            │  │  - Reports         │  │  │
│  │  │            │  │            │  │  - Emails          │  │  │
│  │  │            │  │            │  │  - Cache Warming   │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  PostgreSQL  │  │    Redis     │  │   File Storage       │  │
│  │  (Primary)   │  │   (Cache)    │  │   (Static/Media)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
Blue Falcon/
├── airport_sim/                 # Django Project Configuration
│   ├── settings.py              # Application settings
│   ├── urls.py                  # Root URL configuration
│   ├── asgi.py                  # ASGI configuration (WebSocket)
│   ├── wsgi.py                  # WSGI configuration
│   └── websocket_routing.py     # WebSocket URL routing
│
├── core/                        # Main Application Module
│   ├── models.py                # Database models (2117 lines)
│   ├── views.py                 # Django views (2299 lines)
│   ├── forms.py                 # Form validation
│   ├── serializers.py           # DRF serializers
│   ├── api.py                   # API ViewSets (983 lines)
│   ├── api_urls.py              # API URL routing
│   ├── urls.py                  # App URL patterns
│   ├── admin.py                 # Django admin configuration
│   ├── consumers.py             # WebSocket consumers
│   ├── permissions.py           # Role-based permissions
│   ├── middleware.py            # Custom middleware
│   ├── signals.py               # Django signals
│   ├── tasks.py                 # Background tasks
│   ├── honeypot.py              # Bot protection
│   ├── weather_service.py       # Weather API integration
│   ├── map_service.py           # Map visualization
│   │
│   ├── management/commands/     # Custom Django commands
│   │   ├── populate_demo_data.py
│   │   ├── populate_test_data.py
│   │   ├── setup_permissions.py
│   │   ├── backup_db.py
│   │   └── add_staff_assignments.py
│   │
│   ├── templatetags/            # Custom template filters
│   │   └── core_filters.py
│   │
│   └── tests/                   # Test suite
│       ├── test_models.py
│       ├── test_views.py
│       ├── test_api.py
│       ├── test_permissions.py
│       └── test_security.py
│
├── templates/                   # HTML Templates
│   ├── core/                    # Core app templates
│   │   ├── dashboard.html
│   │   ├── fiscal_assessment_*.html
│   │   ├── report_*.html
│   │   ├── document_*.html
│   │   ├── analytics_dashboard.html
│   │   ├── public/
│   │   │   ├── flight_status.html
│   │   │   └── baggage_tracking.html
│   │   └── emails/
│   │       └── report_email.html
│   ├── admin/                   # Admin templates
│   ├── registration/            # Auth templates
│   └── common/                  # Shared templates
│
├── static/                      # Static Assets
│   ├── css/
│   │   └── base.css             # Main stylesheet (WCAG 2.1 AA)
│   └── js/
│       ├── base.js              # Core JavaScript
│       └── notifications.js     # Browser notifications
│
├── staticfiles/                 # Collected static files
├── docs/                        # Documentation
├── logs/                        # Application logs
│
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── render.yaml                  # Render.com deployment config
├── create_superuser.py          # Superuser creation script
├── check_admin.py               # Admin permission checker
└── reset_sessions.py            # Session cleanup script
```

### Request Flow

#### HTTP Request Flow

```
Client Request
    │
    ▼
Daphne/Gunicorn (ASGI/WSGI Server)
    │
    ▼
Django Middleware Stack
    ├── RequestMiddleware (thread-local storage)
    ├── HoneypotMiddleware (bot detection)
    ├── CSRF Protection
    ├── Authentication
    └── Session Management
    │
    ▼
URL Routing (urls.py)
    │
    ├──────┬──────────┬─────────────┐
    ▼      ▼          ▼             ▼
  Views   API      Admin       Static Files
    │      │          │             │
    ▼      ▼          ▼             ▼
  Models (Database Queries)
    │
    ▼
  Templates (HTML Rendering)
    │
    ▼
  HTTP Response
```

#### WebSocket Flow

```
Client WebSocket Connection
    │
    ▼
ConnectionLimitMiddleware (max 10 per user)
    │
    ▼
WebSocketRateLimiterMiddleware (100 msg/s)
    │
    ▼
AuthMiddlewareStack (user authentication)
    │
    ▼
AllowedHostsOriginValidator
    │
    ▼
URL Router (websocket_routing.py)
    │
    ├──────────┬──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼          ▼
Dashboard  Flights    Gates     Events   Notifications
Consumer   Consumer   Consumer  Consumer   Consumer
    │
    ▼
Channel Layer (Group Messaging)
    │
    ├──────────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼
  Client 1  Client 2  Client 3  ... Client N
```

### Database Schema

#### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Airport   │───────┤    Gate     │       │   Flight    │
├─────────────┤  1:N  ├─────────────┤  N:1  ├─────────────┤
│ id          │       │ id          │       │ id          │
│ code        │       │ gate_id     │       │ flight_num  │
│ name        │       │ terminal    │       │ origin      │
│ city        │       │ capacity    │◄──────│ destination │
│ timezone    │       │ status      │  gate │ gate (FK)   │
│ is_active   │       │ airport(FK) │       │ status      │
└─────────────┘       └─────────────┘       └──────┬──────┘
                                                   │ 1:N
                    ┌─────────────┐       ┌────────▼──────┐
                    │  Passenger  │       │ StaffAssignment│
                    ├─────────────┤  N:1  ├───────────────┤
                    │ id          │◄──────│ id            │
                    │ passenger_id│ flight│ staff (FK)    │
                    │ first_name  │       │ flight (FK)   │
                    │ last_name   │       │ assignment_type│
                    │ flight (FK) │       └───────┬───────┘
                    │ seat_number │               │
                    │ status      │         ┌─────▼─────┐
                    └─────────────┘         │   Staff   │
                                            ├───────────┤
┌─────────────┐       ┌─────────────┐       │ id        │
│FiscalAssess.│───────┤   Report    │       │ staff_id  │
├─────────────┤  1:N  ├─────────────┤       │ role      │
│ id          │       │ id          │       │ is_avail  │
│ airport(FK) │       │ airport(FK) │       └───────────┘
│ period_type │       │ report_type │
│ status      │       │ content     │       ┌───────────┐
│ revenues... │       │ generated_by│       │ EventLog  │
│ expenses... │       └─────────────┘       ├───────────┤
└─────────────┘                             │ id        │
                                            │ event_id  │
┌─────────────┐       ┌─────────────┐       │ timestamp │
│   Aircraft  │       │MaintenanceLog│       │ event_type│
├─────────────┤       ├─────────────┤       │ user (FK) │
│ tail_number │       │ equipment   │       │ action    │
│ model       │       │ status      │       │ severity  │
│ status      │       │ performed_by│       └───────────┘
└─────────────┘       └─────────────┘
```

---

## Core Modules

### 1. Flight Management Module

**Models:**
- `Flight` - Flight operations with scheduling and tracking
- `Passenger` - Passenger records with booking information
- `StaffAssignment` - Staff-to-flight assignments

**Key Features:**
- Flight status lifecycle management
- Gate assignment with conflict detection
- Passenger check-in and boarding tracking
- Delay tracking and reporting

**API Endpoints:**
```
GET    /api/v1/flights/              # List all flights
POST   /api/v1/flights/              # Create new flight
GET    /api/v1/flights/{id}/         # Get flight details
PUT    /api/v1/flights/{id}/         # Update flight
DELETE /api/v1/flights/{id}/         # Delete flight
GET    /api/v1/flights/?status=delayed  # Filter by status
```

### 2. Gate Management Module

**Models:**
- `Gate` - Airport gate entities
- `MaintenanceLog` - Gate maintenance tracking

**Key Features:**
- Real-time gate status tracking
- Terminal-based organization
- Capacity classification (narrow-body/wide-body)
- Maintenance scheduling

**API Endpoints:**
```
GET    /api/v1/gates/                # List all gates
POST   /api/v1/gates/                # Create new gate
GET    /api/v1/gates/?terminal=A     # Filter by terminal
GET    /api/v1/gates/?status=available  # Filter by status
```

### 3. Fiscal Management Module

**Models:**
- `FiscalAssessment` - Financial assessments
- `Report` - Generated reports
- `Document` - Document templates and files

**Key Features:**
- Period-based financial assessments
- Revenue and expense tracking
- Approval workflows
- Automated report generation
- Multi-format export (HTML, PDF, CSV, JSON)

**Views:**
```
/core/assessments/                  # List assessments
/core/assessments/create/           # Create assessment
/core/assessments/{id}/             # View details
/core/assessments/{id}/edit/        # Edit assessment
/core/assessments/{id}/approve/     # Approve/reject
/core/assessments/{id}/print/       # Print view
```

### 4. Staff & Crew Management Module

**Models:**
- `Staff` - Airport/airline staff
- `CrewMember` - Flight crew members
- `StaffAssignment` - Assignment tracking

**Key Features:**
- Staff registry with certifications
- Role-based access control
- Assignment conflict detection
- Availability tracking

### 5. Aircraft & Maintenance Module

**Models:**
- `Aircraft` - Aircraft registry
- `MaintenanceLog` - Maintenance activities
- `IncidentReport` - Incident tracking

**Key Features:**
- Aircraft registration and tracking
- Maintenance schedule management
- Cost tracking for maintenance
- Incident reporting and resolution

### 6. Analytics & Reporting Module

**Views:**
- `AnalyticsDashboardView` - Interactive analytics
- `AirportComparisonView` - Multi-airport comparison
- `ReportScheduleListView` - Scheduled reports

**Features:**
- Chart.js visualizations
- Historical trend analysis
- Comparative analytics
- Scheduled report generation
- Email delivery

### 7. Real-time Updates Module

**Consumers:**
- `DashboardConsumer` - Dashboard metrics
- `FlightUpdatesConsumer` - Flight status
- `GateStatusConsumer` - Gate availability
- `EventLogConsumer` - Audit logs
- `NotificationConsumer` - Browser notifications

**WebSocket Channels:**
```
/ws/dashboard/      # Dashboard updates
/ws/flights/        # Flight updates
/ws/gates/          # Gate updates
/ws/events/         # Event log updates
/ws/notifications/  # Push notifications
```

---

## API Reference

### Authentication

The API supports two authentication methods:

1. **Token Authentication** (CSRF exempt)
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/api/v1/flights/
   ```

2. **Session Authentication** (CSRF required)
   ```bash
   curl --cookie "sessionid=YOUR_SESSION" -H "X-CSRFToken: YOUR_CSRF_TOKEN" ...
   ```

### Rate Limiting

| User Type | Rate Limit |
|-----------|-----------|
| Anonymous | 100 requests/hour |
| Authenticated | 1000 requests/hour |
| Burst | 60 requests/minute |

### Endpoints

#### Airports
```
GET    /api/v1/airports/              # List airports
POST   /api/v1/airports/              # Create airport
GET    /api/v1/airports/{id}/         # Get airport
PUT    /api/v1/airports/{id}/         # Update airport
DELETE /api/v1/airports/{id}/         # Delete airport
```

#### Flights
```
GET    /api/v1/flights/
POST   /api/v1/flights/
GET    /api/v1/flights/{id}/
PUT    /api/v1/flights/{id}/
DELETE /api/v1/flights/{id}/

# Filters
GET /api/v1/flights/?status=delayed&airline=BA&date_from=2026-03-01
```

#### Fiscal Assessments
```
GET    /api/v1/assessments/
POST   /api/v1/assessments/
GET    /api/v1/assessments/{id}/
PUT    /api/v1/assessments/{id}/
DELETE /api/v1/assessments/{id}/
POST   /api/v1/assessments/{id}/approve/  # Approve/reject
```

#### Custom Endpoints

**Dashboard Summary:**
```
GET /api/v1/dashboard-summary/
```
Response:
```json
{
  "total_airports": 5,
  "total_gates": 50,
  "total_flights": 1200,
  "available_gates": 12,
  "active_flights": 45,
  "delayed_flights": 3,
  "flights_by_status": {...},
  "passengers_today": 8500
}
```

**Trend Data:**
```
GET /api/v1/trend-data/?period=6months
```

**Analytics:**
```
GET /api/v1/analytics/?airport=LOS&metric=revenue
```

**Weather:**
```
GET /api/v1/weather/search/?airport=LOS
```

### Response Format

**Success Response:**
```json
{
  "count": 100,
  "next": "/api/v1/flights/?page=2",
  "previous": null,
  "results": [...]
}
```

**Error Response:**
```json
{
  "error": "Invalid input",
  "details": {
    "flight_number": ["This field is required."]
  }
}
```

### API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/api/schema/swagger-ui/`
- **ReDoc**: `/api/schema/redoc/`
- **OpenAPI Schema**: `/api/schema/`

---

## Security

### Authentication & Authorization

#### Role-Based Access Control (RBAC)

| Role | Permissions |
|------|-------------|
| **Viewer** | Read-only access to all data |
| **Editor** | Create and edit operational data |
| **Approver** | Approve fiscal assessments |
| **Admin** | Full system access (superuser only) |

#### Permission Classes

```python
# Example permission usage
class FiscalAssessmentCreateView(PermissionMixin, CreateView):
    required_role = UserRole.EDITOR
    permission_classes = [FiscalAssessmentPermissions]
```

### Security Features

#### 1. Honeypot Protection
- Hidden form fields to trap bots
- Time-based token validation
- Decoy API endpoints
- Automatic blocking of suspicious patterns

#### 2. CSRF Protection
- Enabled on all session-authenticated endpoints
- Token authentication is CSRF-exempt
- Secure cookie settings

#### 3. Input Validation
- Django Forms for all POST data
- Explicit field allowlists
- Type validation (Decimal, Integer, Date)
- JSON schema validation

#### 4. Audit Logging
- Automatic logging via Django signals
- EventLog tracks all CRUD operations
- User, IP address, and timestamp recorded
- Severity levels (info, warning, error)

#### 5. Rate Limiting
- API throttling (100/hour anon, 1000/hour user)
- WebSocket rate limiting (100 msg/s)
- Connection limits (10 per user)

#### 6. Password Security
- PBKDF2, Argon2, BCrypt support
- No weak hashers (MD5 removed)
- Two-factor authentication support

#### 7. Security Headers
```python
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
```

### Security Best Practices

1. **Never commit `.env` files** - Use environment variables
2. **Always use `SECRET_KEY` from environment** - No hardcoded keys
3. **Set `DEBUG=False` in production** - Prevents information disclosure
4. **Configure CORS explicitly** - Don't allow all origins
5. **Use HTTPS in production** - Enforce secure connections
6. **Regular security audits** - Review logs and permissions

---

## Deployment

### Production Deployment on Render.com

#### 1. Configure Render.com

The `render.yaml` file contains deployment configuration:

```yaml
services:
  - type: web
    name: blue-falcon
    runtime: python
    buildCommand: pip install -r requirements.txt && python manage.py collectstatic --noinput
    startCommand: daphne -b 0.0.0.0 -p $PORT airport_sim.asgi:application
    envVars:
      - key: PYTHON_VERSION
        value: "3.12.0"
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: DATABASE_ENGINE
        value: django.db.backends.postgresql
      - key: DATABASE_HOST
        fromDatabase:
          name: blue-falcon-db
          property: host
```

#### 2. Environment Variables

Set the following environment variables in Render:

```env
SECRET_KEY=<auto-generated>
DEBUG=False
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_HOST=<render-db-host>
DATABASE_PORT=5432
DATABASE_NAME=blue_falcon
DATABASE_USER=postgres
DATABASE_PASSWORD=<secure-password>
ALLOWED_HOSTS=blue-falcon.onrender.com,your-domain.com
REDIS_URL=<redis-connection-string>
```

#### 3. Database Setup

Render automatically provisions PostgreSQL. Configure in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'HOST': os.environ.get('DATABASE_HOST'),
        'PORT': os.environ.get('DATABASE_PORT'),
        'NAME': os.environ.get('DATABASE_NAME'),
        'USER': os.environ.get('DATABASE_USER'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
    }
}
```

#### 4. Static Files

WhiteNoise handles static files automatically:

```python
MIDDLEWARE = [
    # ... other middleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... other middleware
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Alternative Deployment (Traditional VPS)

#### 1. Install Dependencies

```bash
sudo apt update
sudo apt install python3.12 python3.12-venv postgresql redis-server nginx supervisor
```

#### 2. Configure PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE blue_falcon;
CREATE USER blue_falcon_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE blue_falcon TO blue_falcon_user;
\q
```

#### 3. Configure Gunicorn + Daphne

Create `/etc/supervisor/conf.d/blue-falcon.conf`:

```ini
[program:blue-falcon-web]
command=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 airport_sim.asgi:application
directory=/path/to/blue-falcon
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/blue-falcon/web.log
```

#### 4. Configure Nginx

Create `/etc/nginx/sites-available/blue-falcon`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/blue-falcon/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 5. Enable SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d your-domain.com
```

---

## Development

### Development Workflow

#### 1. Setting Up Development Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python create_superuser.py

# Populate demo data (optional)
python manage.py populate_demo_data
```

#### 2. Running Development Server

```bash
# HTTP only
python manage.py runserver

# ASGI (WebSocket support)
daphne airport_sim.asgi:application

# Background tasks
python manage.py qcluster
```

#### 3. Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test core.tests.test_models

# With coverage
coverage run manage.py test
coverage report
```

### Coding Standards

#### Code Style

- **PEP 8** compliance (use `ruff` or `black` with line length 88)
- **Type hints** required on all functions
- **Google-style docstrings** for all public classes/methods
- **Maximum function length**: 40 lines (excluding docstrings)

#### Example

```python
"""Module docstring."""

from typing import List, Optional
from django.db import models


class Airport(models.Model):
    """Represents an airport facility.
    
    Attributes:
        code: IATA airport code (e.g., "LOS")
        name: Full airport name
        city: City location
    """
    
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    
    def __str__(self) -> str:
        """Return string representation of airport."""
        return f"{self.code} - {self.name}"
    
    def get_flights_by_status(self, status: str) -> models.QuerySet:
        """Return flights filtered by status.
        
        Args:
            status: Flight status to filter by
            
        Returns:
            QuerySet of flights with specified status
        """
        return self.flights.filter(status=status)
```

#### Django-Specific Rules

1. **Views**: Class-based views where appropriate
2. **Transactions**: Use `@transaction.atomic` for data mutations
3. **Forms**: Use Django Forms/ModelForms for validation
4. **Signals**: Use sparingly for automatic logging only
5. **No business logic in models or views** - Use service layer

### Custom Management Commands

#### Populate Demo Data

```bash
python manage.py populate_demo_data
```

Creates sample airports, gates, flights, passengers, and staff for testing.

#### Setup Permissions

```bash
python manage.py setup_permissions
```

Creates permission groups (viewers, editors, approvers) with appropriate permissions.

#### Backup Database

```bash
python manage.py backup_db
```

Creates a database backup in the `backups/` directory.

### Debugging

#### Django Debug Toolbar

Enabled in development mode:

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

Access at `http://localhost:8000/__debug__/`

#### Logging

Configure logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Fails

**Symptoms:** WebSocket connections return 404 or fail to connect

**Solutions:**
- Ensure ASGI server is running (Daphne, not Gunicorn)
- Check WebSocket URL routing in `websocket_routing.py`
- Verify `ALLOWED_HOSTS` includes your domain
- Check browser console for CORS errors

#### 2. Background Tasks Not Running

**Symptoms:** Reports stuck in "pending" state

**Solutions:**
```bash
# Check if Q cluster is running
python manage.py qcluster

# Check Redis connection
redis-cli ping

# Verify Q_CLUSTER settings in settings.py
```

#### 3. Static Files Not Loading

**Symptoms:** 404 errors for CSS/JS files

**Solutions:**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check STATIC_ROOT in settings.py
# Verify WhiteNoise middleware is enabled
```

#### 4. Database Migration Errors

**Symptoms:** Migration conflicts or errors

**Solutions:**
```bash
# Show migration status
python manage.py showmigrations

# Fake initial migration (if starting fresh)
python manage.py migrate core zero --fake
python manage.py migrate core

# Reset database (development only)
python manage.py flush
python manage.py migrate
```

#### 5. Permission Denied Errors

**Symptoms:** Users can't access certain pages

**Solutions:**
- Run `python manage.py setup_permissions`
- Check user is in correct group (editors, approvers)
- Verify `required_role` in view classes
- Check superuser status for admin-only features

#### 6. Honeypot Blocking Legitimate Requests

**Symptoms:** Forms submit but return 403 errors

**Solutions:**
- Ensure honeypot fields are hidden (not visible to users)
- Check honeypot token validation timing
- Review honeypot middleware logs

### Log Files

Check logs for debugging:

```bash
# Application logs
tail -f logs/debug.log

# Django server logs
journalctl -u blue-falcon-web -f

# Nginx logs
tail -f /var/log/nginx/error.log
```

---

## Support

### Documentation

- **API Documentation**: `/api/schema/swagger-ui/`
- **WCAG Compliance**: See `docs/WCAG_COMPLIANCE_CHECKLIST.md`
- **Change Log**: See `changes.md`
- **Security Audit**: See `rc.md`

### Contact

For support and questions:
- **GitHub Issues**: [Create an issue](https://github.com/yourusername/Blue-Falcon/issues)
- **Email**: support@example.com

### Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure PEP 8 compliance
5. Submit a pull request

### License

Copyright © 2026 Blue Falcon Project. All rights reserved.

---

*Last Updated: March 15, 2026*  
*Version: 1.0*
