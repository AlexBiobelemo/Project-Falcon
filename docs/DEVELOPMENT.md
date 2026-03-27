# Development Guide

> **Project:** Blue Falcon - Airport Operations Management System
> **Version:** 1.0
> **Last Updated:** March 26, 2026
> **Django Version:** 5.2.12

---

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Coding Standards](#coding-standards)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Database Management](#database-management)
8. [Static Files](#static-files)
9. [Background Tasks](#background-tasks)
10. [WebSocket Development](#websocket-development)
11. [API Development](#api-development)
12. [Template Development](#template-development)
13. [Version Control](#version-control)
14. [Code Review](#code-review)
15. [Troubleshooting](#troubleshooting)

---

## Development Environment Setup

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.12+ | Runtime environment |
| pip | Latest | Package manager |
| Git | Latest | Version control |
| PostgreSQL | 12+ (optional) | Production database |
| Redis | Latest (optional) | Cache and background tasks |
| Node.js | 18+ (optional) | Frontend tooling |

**Note:** SQLite is used for development by default. PostgreSQL is recommended for production.

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd "Blue Falcon"
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Create Environment File

```bash
# Copy example
cp .env.example .env

# Or create manually
cat > .env << EOF
SECRET_KEY=django-insecure-your-development-key-here
DEBUG=True
DATABASE_ENGINE=django.db.backends.sqlite3
DATABASE_NAME=db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
EOF
```

### Step 5: Initialize Database

```bash
python manage.py migrate
```

### Step 6: Create Superuser

```bash
python create_superuser.py
# Or manually:
python manage.py createsuperuser
```

### Step 7: Run Development Server

```bash
# HTTP only
python manage.py runserver

# ASGI (WebSocket support)
daphne airport_sim.asgi:application
```

### Step 8: Start Background Tasks (Optional)

```bash
python manage.py qcluster
```

### Step 9: Start Redis (Optional)

```bash
# Windows (with WSL or Redis for Windows)
redis-server

# Linux
sudo systemctl start redis

# Mac (with Homebrew)
brew services start redis
```

### Development Tools (Recommended)

```bash
# Code formatting and linting
pip install black ruff

# Type checking
pip install mypy

# Testing
pip install pytest pytest-django coverage

# Debugging
pip install django-debug-toolbar ipdb

# API testing
pip install httpie  # Optional: HTTP client for API testing
```

**Note:** Install development tools in a separate requirements file or use pipenv/poetry for dependency management.

---

## Project Structure

```
Blue Falcon/
├── airport_sim/                 # Django Project Configuration
│   ├── settings.py              # Application settings
│   ├── urls.py                  # Root URL configuration
│   ├── asgi.py                  # ASGI configuration
│   ├── wsgi.py                  # WSGI configuration
│   ├── websocket_routing.py     # WebSocket routing
│   └── test_settings.py         # Test settings
│
├── core/                        # Main Application Module
│   ├── models.py                # Database models
│   ├── views.py                 # Django views
│   ├── forms.py                 # Form validation
│   ├── serializers.py           # DRF serializers
│   ├── api.py                   # API ViewSets
│   ├── api_urls.py              # API URL routing
│   ├── urls.py                  # App URL patterns
│   ├── admin.py                 # Django admin
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
│   │   ├── add_staff_assignments.py
│   │   ├── complete_analytics_data.py
│   │   └── populate_analytics_data.py
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
│   ├── admin/                   # Admin templates
│   ├── registration/            # Auth templates
│   └── common/                  # Shared templates
│
├── static/                      # Source Static Assets
│   ├── css/
│   │   └── base.css
│   └── js/
│       ├── base.js
│       └── notifications.js
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
├── reset_sessions.py            # Session cleanup script
└── db.sqlite3                   # SQLite database
```

---

## Coding Standards

### Python Style Guide

Follow PEP 8 with these project-specific conventions:

#### Line Length

Maximum 88 characters (Black default):

```python
# GOOD
long_variable_name = some_function_call(
    argument1, argument2, argument3
)

# BAD - Too long
long_variable_name = some_function_call(argument1, argument2, argument3, argument4, argument5)
```

#### Type Hints

Required on all function parameters and return values:

```python
from typing import List, Optional, Dict, Any

def get_flights_by_status(status: str) -> List[Flight]:
    """Return flights filtered by status."""
    return Flight.objects.filter(status=status)

def calculate_total(
    revenue: float,
    expenses: float,
    tax_rate: Optional[float] = None
) -> Dict[str, float]:
    """Calculate total with optional tax."""
    tax = revenue * (tax_rate or 0)
    return {'total': revenue - expenses - tax, 'tax': tax}
```

#### Docstrings

Google-style docstrings for all public classes and methods:

```python
class FlightManager(models.Manager):
    """Custom manager for Flight model with common query methods.
    
    Provides convenient methods for filtering flights by status,
    airline, route, and time periods.
    
    Example:
        >>> Flight.objects.delayed()
        >>> Flight.objects.upcoming()
    """
    
    def delayed(self) -> models.QuerySet:
        """Return all delayed flights.
        
        Returns:
            QuerySet of Flight objects with status 'delayed'
        """
        return self.filter(status=FlightStatus.DELAYED.value)
```

#### Function Length

Maximum 40 lines (excluding docstrings and comments):

```python
# GOOD - Focused function
def create_flight(data: Dict[str, Any]) -> Flight:
    """Create a new flight."""
    flight = Flight.objects.create(
        flight_number=data['flight_number'],
        airline=data['airline'],
        origin=data['origin'],
        destination=data['destination'],
    )
    log_flight_creation(flight)
    notify_flight_update(flight)
    return flight

# BAD - Too long, split into smaller functions
```

#### Naming Conventions

```python
# Classes: PascalCase
class FiscalAssessment(models.Model):
    pass

# Functions/Methods: snake_case
def calculate_total_revenue():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FLIGHTS_PER_DAY = 100

# Private: Leading underscore
def _internal_helper():
    pass

# Models: Clear domain language
class Flight(models.Model):
    scheduled_departure = models.DateTimeField()
    actual_departure = models.DateTimeField()
    delay_minutes = models.IntegerField()
```

### Django-Specific Rules

#### Models

```python
# Rules compliance: PEP8, type hints, docstrings, atomic transactions verified.

class Flight(models.Model):
    """Represents a flight operation with scheduling and tracking."""
    
    # Use timezone.now, not datetime.now
    created_at = models.DateTimeField(default=timezone.now)
    
    # Define __str__
    def __str__(self) -> str:
        return self.flight_number
    
    # Use custom managers
    objects = FlightManager()
    
    # Add indexes for performance
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_departure']),
        ]
```

#### Views

```python
# Use class-based views where appropriate
class FlightListView(PermissionMixin, ListView):
    """List all flights with filtering and pagination."""
    
    model = Flight
    template_name = 'core/flight_list.html'
    context_object_name = 'flights'
    paginate_by = 25
    required_role = UserRole.VIEWER
    
    def get_queryset(self) -> models.QuerySet:
        """Return filtered and ordered flights."""
        queryset = Flight.objects.select_related('gate').all()
        
        # Apply filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
```

#### Forms

```python
# Use Django Forms for validation
class FlightCreateForm(HoneypotFieldMixin, forms.Form):
    """Form for creating new flights."""
    
    flight_number = forms.CharField(
        max_length=10,
        required=True,
        validators=[validate_flight_number]
    )
    
    def clean_flight_number(self) -> str:
        """Validate flight number format."""
        value = self.cleaned_data['flight_number']
        if not re.match(r'^[A-Z]{2,3}\d{1,4}$', value):
            raise ValidationError('Invalid flight number format.')
        return value
```

---

## Development Workflow

### Feature Development

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/feature-name
   ```

2. **Make Changes**
   - Write tests first (TDD)
   - Implement feature
   - Run tests

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/feature-name
   ```

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/description` | `feature/flight-tracking` |
| Bug Fix | `fix/description` | `fix/delay-calculation` |
| Hotfix | `hotfix/description` | `hotfix/security-patch` |
| Documentation | `docs/description` | `docs/api-update` |
| Refactor | `refactor/description` | `refactor/model-optimization` |

### Commit Message Convention

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Example:**
```
feat(flights): add delay tracking

- Add delay_minutes field to Flight model
- Update flight status calculation
- Add delay reporting to dashboard

Closes #123
```

---

## Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific test module
python manage.py test core.tests.test_models

# Run with verbosity
python manage.py test -v 2

# Run with coverage
coverage run manage.py test
coverage report
coverage html
```

### Test Structure

```python
# core/tests/test_models.py
from django.test import TestCase
from core.models import Flight, FlightStatus

class FlightModelTest(TestCase):
    """Test Flight model methods."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.flight = Flight.objects.create(
            flight_number='BA123',
            airline='British Airways',
            origin='LOS',
            destination='LHR',
            status=FlightStatus.SCHEDULED.value,
        )
    
    def test_str_method(self):
        """Test string representation."""
        self.assertEqual(str(self.flight), 'BA123')
    
    def test_is_delayed_property(self):
        """Test is_delayed property."""
        self.assertFalse(self.flight.is_delayed)
        
        self.flight.status = FlightStatus.DELAYED.value
        self.flight.save()
        self.assertTrue(self.flight.is_delayed)
```

### Test Categories

#### Unit Tests

```python
class FlightCalculationTest(TestCase):
    """Test flight calculation methods."""
    
    def test_delay_calculation(self):
        """Test delay minutes calculation."""
        flight = Flight(
            scheduled_departure=timezone.now(),
            actual_departure=timezone.now() + timedelta(minutes=30),
        )
        self.assertEqual(flight.delay_minutes, 30)
```

#### Integration Tests

```python
class FlightAPITest(TestCase):
    """Test flight API endpoints."""
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.force_login(self.user)
    
    def test_list_flights(self):
        """Test flight list endpoint."""
        Flight.objects.create(flight_number='BA123', ...)
        
        response = self.client.get('/api/v1/flights/')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
```

#### Security Tests

```python
class PermissionTest(TestCase):
    """Test permission enforcement."""
    
    def test_viewer_cannot_delete(self):
        """Test viewers cannot delete assessments."""
        user = self.create_user_with_role(UserRole.VIEWER)
        self.client.force_login(user)
        
        response = self.client.delete(f'/core/assessments/{self.assessment.id}/')
        
        self.assertEqual(response.status_code, 403)
```

### Test Coverage Goals

| Component | Coverage Goal |
|-----------|--------------|
| Models | 90%+ |
| Views | 80%+ |
| API | 85%+ |
| Forms | 90%+ |
| Overall | 85%+ |

---

## Debugging

### Django Debug Toolbar

Enabled automatically in DEBUG mode:

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

Access at: `http://localhost:8000/__debug__/`

### Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# Usage in code
import logging
logger = logging.getLogger(__name__)

def my_function():
    logger.debug('Debug message')
    logger.info('Info message')
    logger.warning('Warning message')
    logger.error('Error message')
```

### Python Debugger

```python
# Set breakpoint
import pdb; pdb.set_trace()

# Or in Python 3.7+
breakpoint()

# Common commands:
# n (next line)
# s (step into)
# c (continue)
# p variable (print)
# l (list code)
# q (quit)
```

### Query Debugging

```python
# Enable SQL logging
from django.db import connection

# Run query
Flight.objects.filter(status='delayed')

# View SQL
print(connection.queries[-1]['sql'])

# View query count
print(len(connection.queries))
```

---

## Database Management

### Migrations

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Rollback migration
python manage.py migrate core 0009

# Create empty migration
python manage.py makemigrations --empty core
```

### Custom Management Commands

```python
# core/management/commands/populate_demo_data.py
from django.core.management.base import BaseCommand
from core.models import Airport, Flight

class Command(BaseCommand):
    """Populate database with demo data."""
    
    help = 'Creates demo data for development'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--airports',
            type=int,
            default=5,
            help='Number of airports to create'
        )
    
    def handle(self, *args, **options):
        airport_count = options['airports']
        
        for i in range(airport_count):
            Airport.objects.create(
                code=f'AIR{i}',
                name=f'Airport {i}',
                city=f'City {i}',
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {airport_count} airports')
        )
```

**Usage:**
```bash
python manage.py populate_demo_data --airports 10
```

### Database Shell

```bash
python manage.py dbshell

# PostgreSQL commands
\dt          # List tables
\d table     # Describe table
SELECT * FROM table;
```

---

## Static Files

### Development

```bash
# Collect static files
python manage.py collectstatic --noinput

# Find static files
python manage.py findstatic css/base.css
```

### CSS Development

```css
/* static/css/base.css */

/* Use CSS custom properties for theming */
:root {
    --primary-color: #0d6efd;
    --background-dark: #0d1117;
    --text-light: #c9d1d9;
}

/* Dark theme */
[data-theme="dark"] {
    background-color: var(--background-dark);
    color: var(--text-light);
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 1rem;
    }
}

/* Accessibility */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    z-index: 100;
}

.skip-link:focus {
    top: 0;
}
```

### JavaScript Development

```javascript
// static/js/base.js

// Use ES6+ features
class ThemeToggle {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.applyTheme(this.currentTheme);
            this.bindEvents();
        });
    }
    
    toggle() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.currentTheme);
        this.applyTheme(this.currentTheme);
    }
}

// Export for use in other modules
export { ThemeToggle };
```

---

## Background Tasks

### Django-Q2 Configuration

```python
# settings.py
Q_CLUSTER = {
    'name': 'BlueFalcon',
    'workers': 4,
    'timeout': 60,
    'retry': 120,
    'orm': 'default',
}
```

### Creating Tasks

```python
# core/tasks.py
from django_q.tasks import async_task

def generate_report_task(report_id: int) -> bool:
    """Generate report in background."""
    try:
        report = Report.objects.get(id=report_id)
        # ... generation logic
        return True
    except Exception as e:
        logger.error(f'Error: {e}')
        return False

def send_email_task(recipient: str, subject: str, body: str):
    """Send email in background."""
    send_mail(subject, body, 'noreply@example.com', [recipient])
```

### Queueing Tasks

```python
# In views
from django_q.tasks import async_task

def create_report(request):
    report = Report.objects.create(...)
    
    # Queue background task
    async_task(
        'core.tasks.generate_report_task',
        report.id,
        group='reports',
    )
    
    return redirect('report_detail', report.id)
```

### Running Q Cluster

```bash
# Development
python manage.py qcluster

# View tasks in admin
# /admin/django_q/
```

---

## WebSocket Development

### Creating Consumers

```python
# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class FlightUpdatesConsumer(AsyncWebsocketConsumer):
    """Consumer for real-time flight updates."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.room_group_name = 'flight_updates'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming messages."""
        data = json.loads(text_data)
        
        if data.get('action') == 'subscribe':
            flight_id = data.get('flight_id')
            await self.subscribe_to_flight(flight_id)
    
    async def flight_update(self, event):
        """Send flight update to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'flight_update',
            'data': event['data'],
        }))
```

### Broadcasting Updates

```python
# In views or signals
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def notify_flight_update(flight):
    """Broadcast flight update via WebSocket."""
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        'flight_updates',
        {
            'type': 'flight_update',
            'data': {
                'flight_number': flight.flight_number,
                'status': flight.status,
                'delay_minutes': flight.delay_minutes,
            },
        }
    )
```

### Testing WebSockets

```python
# tests/test_websocket.py
from channels.testing import WebsocketCommunicator
from airport_sim.asgi import application

async def test_websocket_connection():
    """Test WebSocket connection."""
    communicator = WebsocketCommunicator(
        application,
        '/ws/flights/'
    )
    
    connected, _ = await communicator.connect()
    assert connected
    
    await communicator.disconnect()
```

---

## API Development

### Creating ViewSets

```python
# core/api.py
from rest_framework import viewsets, permissions
from .models import Flight
from .serializers import FlightSerializer
from .permissions import FlightPermissions

class FlightViewSet(viewsets.ModelViewSet):
    """API endpoint for flights."""
    
    queryset = Flight.objects.select_related('gate').all()
    serializer_class = FlightSerializer
    permission_classes = [FlightPermissions]
    search_fields = ['flight_number', 'airline']
    ordering_fields = ['scheduled_departure', 'status']
    
    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Custom action to update flight status."""
        flight = self.get_object()
        new_status = request.data.get('status')
        
        flight.status = new_status
        flight.save()
        
        return Response({'status': new_status})
```

### Serializers

```python
# core/serializers.py
from rest_framework import serializers
from .models import Flight

class FlightSerializer(serializers.ModelSerializer):
    """Serializer for Flight model."""
    
    gate_info = serializers.CharField(
        source='gate.gate_id',
        read_only=True
    )
    
    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'airline', 'origin',
            'destination', 'scheduled_departure', 'gate_info',
            'status', 'delay_minutes'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_flight_number(self, value):
        """Validate flight number uniqueness."""
        if Flight.objects.filter(flight_number=value).exists():
            raise serializers.ValidationError(
                'Flight number already exists.'
            )
        return value
```

### API Documentation

```bash
# Generate schema
python manage.py spectacular --file schema.yml

# View interactive docs
# http://localhost:8000/api/schema/swagger-ui/
# http://localhost:8000/api/schema/redoc/
```

---

## Template Development

### Template Structure

```django
{# templates/core/dashboard.html #}

{% extends 'base.html' %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="container">
    {% include 'common/partials/page_header.html' with title='Dashboard' %}
    
    <div class="row">
        {% include 'common/partials/data_table.html' with data=flights %}
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/dashboard.js' %}"></script>
{% endblock %}
```

### Custom Template Tags

```python
# core/templatetags/core_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply value by argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.simple_tag
def has_role(user, role):
    """Check if user has specific role."""
    return user.groups.filter(name=role).exists() or user.is_superuser
```

**Usage:**
```django
{% load core_filters %}

{{ value|multiply:1.15 }}

{% if user|has_role:'editor' %}
    <button>Edit</button>
{% endif %}
```

---

## Version Control

### Git Configuration

```bash
# Global settings
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Project-specific
git config core.autocrlf input  # For cross-platform
```

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
env/

# Django
*.log
db.sqlite3
media/
staticfiles/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### Common Git Commands

```bash
# Status
git status

# Add files
git add .
git add path/to/file

# Commit
git commit -m "feat: add new feature"

# Push
git push origin main

# Pull
git pull origin main

# Create branch
git checkout -b feature/new-feature

# Switch branch
git checkout main

# Merge
git checkout main
git merge feature/new-feature

# Rebase
git rebase main

# Stash
git stash
git stash pop

# View history
git log --oneline --graph
```

---

## Code Review

### Review Checklist

- [ ] Code follows style guide
- [ ] Type hints are present
- [ ] Docstrings are complete
- [ ] Tests are included
- [ ] No security vulnerabilities
- [ ] No performance issues
- [ ] Error handling is adequate
- [ ] Logging is appropriate

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Comments added where needed
- [ ] Documentation updated

## Related Issues
Closes #123
```

---

## Troubleshooting

### Common Issues

#### Migration Errors

```bash
# Fake initial migration
python manage.py migrate core zero --fake
python manage.py migrate core

# Or delete migration files and recreate
rm core/migrations/0*.py
python manage.py makemigrations core
python manage.py migrate
```

#### Static Files Not Loading

```bash
# Clear cache and recollect
rm -rf staticfiles/
python manage.py collectstatic --clear --noinput

# Check STATIC_URL in settings.py
```

#### WebSocket Not Connecting

```bash
# Check Daphne is running
# Check routing in websocket_routing.py
# Check browser console for errors
```

#### Background Tasks Not Running

```bash
# Check Q cluster is running
python manage.py qcluster

# Check Redis connection
redis-cli ping

# Check task imports
```

### Debug Mode Settings

```python
# settings.py for development
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Enable debug toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Show SQL queries
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}
```

---

*Last Updated: March 15, 2026*  
*Version: 1.0*
