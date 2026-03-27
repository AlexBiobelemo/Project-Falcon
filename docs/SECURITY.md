# Security Documentation

> **Project:** Blue Falcon - Airport Operations Management System
> **Version:** 1.0
> **Last Updated:** March 26, 2026
> **Django Version:** 5.2.12
> **Classification:** Internal Use

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Authentication](#authentication)
3. [Authorization](#authorization)
4. [Input Validation](#input-validation)
5. [CSRF Protection](#csrf-protection)
6. [Honeypot Protection](#honeypot-protection)
7. [Rate Limiting](#rate-limiting)
8. [Audit Logging](#audit-logging)
9. [Data Protection](#data-protection)
10. [WebSocket Security](#websocket-security)
11. [Security Headers](#security-headers)
12. [Password Security](#password-security)
13. [Session Security](#session-security)
14. [Security Monitoring](#security-monitoring)
15. [Incident Response](#incident-response)
16. [Security Checklist](#security-checklist)

---

## Security Overview

### Security Architecture

Blue Falcon implements defense-in-depth security with multiple layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Security Layers                                 │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 1: Network Security                                    │ │
│  │  - HTTPS/TLS Encryption                                       │ │
│  │  - CORS Configuration                                         │ │
│  │  - Allowed Hosts Validation                                   │ │
│  │  - Firewall Rules                                             │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 2: Application Security                                │ │
│  │  - Authentication (Session + Token + 2FA)                     │ │
│  │  - Authorization (RBAC)                                       │ │
│  │  - Session Management                                         │ │
│  │  - Rate Limiting                                              │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 3: Input Security                                      │ │
│  │  - Form Validation                                            │ │
│  │  - Serializer Validation                                      │ │
│  │  - SQL Injection Prevention                                   │ │
│  │  - XSS Prevention                                             │ │
│  │  - Honeypot Protection                                        │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 4: Data Security                                       │ │
│  │  - Password Hashing                                           │ │
│  │  - Data Encryption at Rest                                    │ │
│  │  - Secure File Storage                                        │ │
│  │  - Database Security                                          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Layer 5: Monitoring & Audit                                  │ │
│  │  - Activity Logging                                           │ │
│  │  - Security Event Monitoring                                  │ │
│  │  - Intrusion Detection                                        │ │
│  │  - Alert System                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Security Principles

| Principle | Implementation |
|-----------|----------------|
| **Least Privilege** | Users have minimum required permissions |
| **Defense in Depth** | Multiple security layers |
| **Secure by Default** | Secure settings out of the box |
| **Fail Securely** | Errors don't expose sensitive information |
| **Complete Mediation** | Every access is checked |
| **Audit Trail** | All actions are logged |

---

## Authentication

### Authentication Methods

#### 1. Session Authentication

**Use Case:** Browser-based access

**Features:**
- Cookie-based sessions
- CSRF token required
- Session expiration
- Secure cookie flags

**Configuration:**
```python
# settings.py
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1209600  # 2 weeks
```

#### 2. Token Authentication

**Use Case:** API clients, mobile apps

**Features:**
- Stateless authentication
- CSRF exempt
- Bearer token format
- Revocable tokens

**Usage:**
```bash
curl -H "Authorization: Bearer <token>" https://api.example.com/api/v1/flights/
```

#### 3. Two-Factor Authentication (2FA)

**Use Case:** Enhanced security for all users

**Features:**
- TOTP (Time-based One-Time Password)
- QR code setup
- Backup codes
- SMS support (optional)

**Setup:**
1. Go to Profile → Security
2. Click "Enable 2FA"
3. Scan QR code with authenticator app
4. Enter verification code
5. Save backup codes

### Password Requirements

| Requirement | Description |
|-------------|-------------|
| Minimum Length | 8 characters |
| Complexity | At least 3 of: uppercase, lowercase, numbers, symbols |
| History | Cannot reuse last 5 passwords |
| Expiration | Optional, configurable |
| Lockout | 5 failed attempts = 15 minute lockout |

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Authentication Flow                              │
│                                                                     │
│  User          Application          Database                        │
│   │                │                    │                           │
│   │  1. Login     │                    │                           │
│   │─────────────>│                    │                           │
│   │                │                    │                           │
│   │                │  2. Verify creds  │                           │
│   │                │──────────────────>│                           │
│   │                │                    │                           │
│   │                │  3. User data     │                           │
│   │                │<──────────────────│                           │
│   │                │                    │                           │
│   │                │  4. Check 2FA     │                           │
│   │                │──────────────────>│                           │
│   │                │                    │                           │
│   │                │  5. 2FA status    │                           │
│   │                │<──────────────────│                           │
│   │                │                    │                           │
│   │  6a. Session  │                    │                           │
│   │<─────────────│                    │                           │
│   │   (if no 2FA) │                    │                           │
│   │                │                    │                           │
│   │  6b. 2FA Page │                    │                           │
│   │<─────────────│                    │                           │
│   │                │                    │                           │
│   │  7. 2FA Code  │                    │                           │
│   │─────────────>│                    │                           │
│   │                │                    │                           │
│   │                │  8. Verify code   │                           │
│   │                │──────────────────>│                           │
│   │                │                    │                           │
│   │  9. Session   │                    │                           │
│   │<─────────────│                    │                           │
│   │                │                    │                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Authorization

### Role-Based Access Control (RBAC)

#### User Roles

| Role | Group | Permissions |
|------|-------|-------------|
| **Viewer** | (none) | Read-only access to all data |
| **Editor** | editors | Create and edit operational data |
| **Approver** | approvers | Approve fiscal assessments, generate reports |
| **Admin** | (superuser) | Full system access |

#### Role Hierarchy

```
┌─────────────────────────────────────────┐
│              ADMIN                      │
│         (Superuser Only)                │
│    ─────────────────────────────        │
│  All Permissions                        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            APPROVER                     │
│      (approvers group)                  │
│    ─────────────────────────────        │
│  Editor + Approve Assessments           │
│  Generate Reports                       │
│  Export Data                            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              EDITOR                     │
│       (editors group)                   │
│    ─────────────────────────────        │
│  Viewer + Create Flights/Gates          │
│  Edit Operational Data                  │
│  Import Data                            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              VIEWER                     │
│      (Default for all users)            │
│    ─────────────────────────────        │
│  View Dashboards                        │
│  View Reports                           │
│  View Flight/Gate Status                │
└─────────────────────────────────────────┘
```

### Permission Classes

#### Model-Level Permissions

```python
# Example: FiscalAssessmentPermissions
class FiscalAssessmentPermissions(BasePermission):
    """
    Permissions for FiscalAssessment model.
    - Viewers: Can read
    - Editors: Can create and edit
    - Approvers: Can approve
    - Admins: Full access including delete
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        elif request.method == 'POST':
            return has_minimum_role(request.user, UserRole.EDITOR)
        elif request.method in ['PUT', 'PATCH']:
            return has_minimum_role(request.user, UserRole.EDITOR)
        elif request.method == 'DELETE':
            return request.user.is_superuser
        return False
```

#### Object-Level Permissions

```python
def has_object_permission(self, request, view, obj):
    # Read permissions are allowed to any authenticated user
    if request.method in permissions.SAFE_METHODS:
        return True
    
    # Write permissions require Editor role
    if request.method in ['PUT', 'PATCH']:
        return has_minimum_role(request.user, UserRole.EDITOR)
    
    # Delete requires superuser
    return request.user.is_superuser
```

### Permission Enforcement

#### In Views

```python
from core.permissions import PermissionMixin, UserRole

class FiscalAssessmentCreateView(PermissionMixin, CreateView):
    """Create fiscal assessment - requires Editor role."""
    
    required_role = UserRole.EDITOR
    model = FiscalAssessment
    form_class = FiscalAssessmentCreateForm
    template_name = 'core/fiscal_assessment_form.html'
```

#### In API

```python
from rest_framework.permissions import IsAuthenticated
from core.permissions import FiscalAssessmentPermissions

class FiscalAssessmentViewSet(viewsets.ModelViewSet):
    """API endpoint for fiscal assessments."""
    
    queryset = FiscalAssessment.objects.all()
    serializer_class = FiscalAssessmentSerializer
    permission_classes = [IsAuthenticated, FiscalAssessmentPermissions]
```

#### In Templates

```django
{% load core_filters %}

{% if user|has_role:'editor' %}
    <a href="{% url 'core:fiscal_assessment_create' %}">New Assessment</a>
{% endif %}

{% if user|has_role:'approver' %}
    <a href="{% url 'core:fiscal_assessment_approve' assessment.id %}">Approve</a>
{% endif %}

{% if user.is_superuser %}
    <a href="{% url 'core:fiscal_assessment_delete' assessment.id %}">Delete</a>
{% endif %}
```

---

## Input Validation

### Form Validation

All forms use Django's form validation:

```python
class FiscalAssessmentCreateForm(HoneypotFieldMixin, forms.Form):
    """Form with comprehensive validation."""
    
    # Required fields with validation
    airport = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_active=True),
        required=True,
        error_messages={'required': 'Airport is required.'}
    )
    
    # Numeric validation
    fuel_revenue = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        min_value=0,
        initial=0
    )
    
    # Date validation
    start_date = forms.DateField(
        required=True,
        error_messages={
            'required': 'Start date is required.',
            'invalid': 'Invalid date format.'
        }
    )
    
    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError('End date must be after start date.')
        
        return cleaned_data
```

### API Serializer Validation

```python
class FlightSerializer(serializers.ModelSerializer):
    """Serializer with validation."""
    
    class Meta:
        model = Flight
        fields = '__all__'
    
    def validate_flight_number(self, value):
        """Validate flight number format."""
        if not re.match(r'^[A-Z]{2,3}\d{1,4}$', value):
            raise serializers.ValidationError(
                'Invalid flight number format.'
            )
        return value
    
    def validate(self, data):
        """Cross-field validation."""
        if data.get('actual_departure') and data.get('scheduled_departure'):
            if data['actual_departure'] < data['scheduled_departure']:
                raise serializers.ValidationError({
                    'actual_departure': 'Cannot be before scheduled departure.'
                })
        return data
```

### SQL Injection Prevention

**ORM Usage:** All database queries use Django ORM (parameterized queries)

```python
# SAFE - Uses ORM parameterization
flights = Flight.objects.filter(flight_number=flight_number)

# SAFE - Uses parameterized raw SQL
flights = Flight.objects.raw(
    'SELECT * FROM core_flight WHERE flight_number = %s',
    [flight_number]
)

# UNSAFE - Never do this (string interpolation)
# flights = Flight.objects.raw(
#     f'SELECT * FROM core_flight WHERE flight_number = {flight_number}'
# )
```

### XSS Prevention

**Auto-escaping:** Django templates auto-escape by default

```django
{# SAFE - Auto-escaped #}
<p>{{ user_input }}</p>

{# UNSAFE - Never use |safe unless input is sanitized #}
<p>{{ user_input|safe }}</p>
```

---

## CSRF Protection

### CSRF Token Configuration

```python
# settings.py
CSRF_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_HTTPONLY = True  # No JavaScript access
CSRF_COOKIE_SAMESITE = 'Lax'  # CSRF protection
CSRF_TRUSTED_ORIGINS = [
    'https://your-domain.com',
    'https://www.your-domain.com',
]
```

### CSRF Token Usage

#### In Templates

```django
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Submit</button>
</form>
```

#### In AJAX Requests

```javascript
// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Include in AJAX requests
fetch('/api/v1/flights/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
    },
    body: JSON.stringify(data),
});
```

### CSRF Exemptions

Token authentication is CSRF-exempt:

```python
# API endpoints using TokenAuthentication don't require CSRF
# Session authentication requires CSRF
```

---

## Honeypot Protection

### Overview

Honeypot protection detects and blocks automated bot submissions using:
- Hidden form fields
- Time-based validation
- Token verification
- Decoy endpoints

### Form Honeypot

```python
from core.honeypot import HoneypotFieldMixin

class FiscalAssessmentCreateForm(HoneypotFieldMixin, forms.Form):
    """Form with honeypot protection."""
    
    # Honeypot fields are added automatically by mixin
    # They are hidden from users but visible to bots
    
    airport = forms.ModelChoiceField(...)
    # ... other fields
```

### Honeypot Fields

```html
<!-- Rendered as hidden fields -->
<div class="hp-field" style="display:none;">
    <label for="hp_username">Username</label>
    <input type="text" name="hp_username" id="hp_username" autocomplete="off">
</div>

<div class="hp-field" style="display:none;">
    <label for="hp_email">Email</label>
    <input type="email" name="hp_email" id="hp_email" autocomplete="off">
</div>

<!-- Honeypot token -->
<input type="hidden" name="hp_token" value="abc123...">
```

### Time-Based Validation

```python
def validate_honeypot_token(token: str) -> bool:
    """Validate honeypot token with timestamp."""
    try:
        # Token format: timestamp:hash
        timestamp, hash_value = token.split(':')
        
        # Check timestamp is within valid window
        current_time = int(time.time())
        token_time = int(timestamp)
        
        if abs(current_time - token_time) > 3600:  # 1 hour window
            return False
        
        # Verify hash
        expected_hash = hashlib.sha256(
            f"{timestamp}{settings.SECRET_KEY}".encode()
        ).hexdigest()[:10]
        
        return hash_value == expected_hash
    except Exception:
        return False
```

### Decoy Endpoints

```python
# Honeypot API endpoints to trap scanners
urlpatterns += [
    path('api/v1/.env', honeypot_decoy_view),
    path('api/v1/wp-admin', honeypot_decoy_view),
    path('api/v1/phpmyadmin', honeypot_decoy_view),
    path('api/v1/admin.php', honeypot_decoy_view),
]

def honeypot_decoy_view(request):
    """Log and block suspicious requests."""
    honeypot_logger.warning(
        f'Honeypot triggered: {request.path} from {request.META.get("REMOTE_ADDR")}'
    )
    return HttpResponse(status=418)  # I'm a teapot
```

---

## Rate Limiting

### API Rate Limiting

```python
# settings.py (REST_FRAMEWORK configuration)
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',       # Anonymous users
        'user': '1000/hour',      # Authenticated users
        'burst': '60/min',        # Burst protection for all
    },
}
```

| User Type     | Rate Limit         |
| ------------- | ------------------ |
| Anonymous     | 100 requests/hour  |
| Authenticated | 1000 requests/hour |
| Burst (all)   | 60 requests/minute |

### Custom Throttling

```python
from rest_framework.throttling import UserRateThrottle

class ApprovalRateThrottle(UserRateThrottle):
    """Stricter rate limit for approval actions."""
    
    rate = '10/hour'  # Max 10 approvals per hour
    
    def allow_request(self, request, view):
        # Skip throttling for superusers
        if request.user.is_superuser:
            return True
        return super().allow_request(request, view)
```

### WebSocket Rate Limiting

```python
class WebSocketRateLimiterMiddleware:
    """Rate limit WebSocket messages."""
    
    def __init__(self, application, rate="100/s"):
        self.application = application
        self.max_messages = 100
        self.time_window = 1.0
        self.connection_counts = {}
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            connection_id = id(scope.get('client'))
            
            # Check rate limit
            if self.is_rate_limited(connection_id):
                await send({
                    'type': 'websocket.close',
                    'code': 1013,
                })
                return
        
        return await self.application(scope, receive, send)
```

### Connection Limits

```python
class ConnectionLimitMiddleware:
    """Limit concurrent WebSocket connections per user."""
    
    def __init__(self, application, max_connections=10):
        self.application = application
        self.max_connections = max_connections
        self.active_connections = {}
    
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'websocket':
            user = scope.get('user')
            user_id = str(user.id) if user and user.is_authenticated else 'anonymous'
            
            if user_id in self.active_connections:
                if self.active_connections[user_id] >= self.max_connections:
                    await send({'type': 'websocket.close', 'code': 1013})
                    return
                self.active_connections[user_id] += 1
            else:
                self.active_connections[user_id] = 1
        
        try:
            return await self.application(scope, receive, send)
        finally:
            # Clean up on disconnect
            if scope['type'] == 'websocket':
                self.active_connections[user_id] -= 1
```

---

## Audit Logging

### Automatic Logging

All CRUD operations are automatically logged via Django signals:

```python
@receiver(post_save, sender=FiscalAssessment)
def log_fiscal_assessment_change(sender, instance, created, **kwargs):
    """Log fiscal assessment changes."""
    if created:
        EventLog.objects.create(
            event_type='fiscal_assessment',
            action='create',
            description=f'Fiscal assessment created for {instance.airport}',
            severity='info',
            ip_address=get_current_request().META.get('REMOTE_ADDR'),
        )
    else:
        EventLog.objects.create(
            event_type='fiscal_assessment',
            action='update',
            description=f'Fiscal assessment updated: {instance.airport}',
            severity='info',
            ip_address=get_current_request().META.get('REMOTE_ADDR'),
        )
```

### Logged Events

| Event Type | Actions Logged |
|------------|---------------|
| Authentication | login, logout, 2fa_enable, 2fa_disable |
| Flight | create, update, delete, status_change |
| Gate | create, update, delete, assignment |
| Fiscal Assessment | create, update, delete, approve, reject |
| Report | create, update, delete, export, generate |
| Document | create, update, delete, export |
| User | password_change, profile_update, permission_change |

### Log Entry Structure

```python
class EventLog(models.Model):
    """Audit log entry."""
    
    event_id = models.UUIDField(default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    event_type = models.CharField(max_length=50)
    description = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField(null=True)
    flight = models.ForeignKey(Flight, on_delete=models.SET_NULL, null=True)
    severity = models.CharField(max_length=20)  # info, warning, error
```

### Log Retention

```python
# settings.py
# Retain logs for 1 year
EVENT_LOG_RETENTION_DAYS = 365

# Background task to clean old logs
def cleanup_old_logs():
    cutoff = timezone.now() - timedelta(days=EVENT_LOG_RETENTION_DAYS)
    EventLog.objects.filter(timestamp__lt=cutoff).delete()
```

---

## Data Protection

### Password Hashing

```python
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',  # Primary (most secure)
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Fallback
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Note: MD5PasswordHasher is explicitly NOT used, even in DEBUG mode
# The system fails fast if SECRET_KEY is not set (no insecure fallbacks)
```

### Sensitive Data Handling

```python
# Never log sensitive data
logger.info(f'User {user.username} logged in')  # OK
logger.info(f'User {user.username} password: {password}')  # NEVER

# Mask sensitive data in responses
def mask_passport_number(passport: str) -> str:
    """Mask passport number for display."""
    return f"***{passport[-4:]}" if len(passport) > 4 else "***"
```

### Database Security

```python
# settings.py
# Use parameterized queries (Django ORM does this by default)
# Enable SSL for database connections in production
DATABASES = {
    'default': {
        # ...
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}
```

---

## WebSocket Security

### Authentication

```python
# WebSocket authentication middleware
class AuthMiddlewareStack(MiddlewareStack):
    """Authenticate WebSocket connections."""
    
    def __init__(self, inner):
        self.inner = inner
    
    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        
        if 'token' in params:
            token = params['token'][0]
            user = await self.get_user_from_token(token)
            scope['user'] = user
        else:
            scope['user'] = AnonymousUser()
        
        return await self.inner(scope, receive, send)
```

### Connection Validation

```python
async def connect(self):
    """Validate WebSocket connection."""
    user = self.scope['user']
    
    # Require authentication
    if not user.is_authenticated:
        await self.close(code=4001)
        return
    
    # Check user is active
    if not user.is_active:
        await self.close(code=4002)
        return
    
    # Join room group
    await self.channel_layer.group_add(
        self.room_group_name,
        self.channel_name
    )
    
    await self.accept()
```

### Message Validation

```python
async def receive(self, text_data):
    """Validate and process incoming messages."""
    try:
        data = json.loads(text_data)
        
        # Validate message structure
        if 'type' not in data:
            await self.send(json.dumps({'error': 'Missing type'}))
            return
        
        # Validate message size
        if len(text_data) > 65536:  # 64KB limit
            await self.send(json.dumps({'error': 'Message too large'}))
            return
        
        # Process message
        await self.handle_message(data)
        
    except json.JSONDecodeError:
        await self.send(json.dumps({'error': 'Invalid JSON'}))
```

---

## Security Headers

### HTTP Security Headers

```python
# settings.py
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME sniffing
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
SECURE_BROWSER_XSS_FILTER = True  # XSS filter
SECURE_HSTS_SECONDS = 31536000  # 1 year HSTS
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
```

### Content Security Policy

```python
# settings.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net')
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net')
CSP_FONT_SRC = ("'self'", 'https://cdn.jsdelivr.net')
CSP_IMG_SRC = ("'self'", 'data:', 'https:')
```

---

## Password Security

### Password Validation

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### Password Reset

```python
# settings.py
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours
PASSWORD_RESET_EMAIL_SUBJECT = 'Password Reset Request'
```

---

## Session Security

### Session Configuration

```python
# settings.py
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = True  # Extend session on each request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

### Session Management

```python
# Invalidate sessions on password change
user.set_password(new_password)
user.save()

# Invalidate all sessions
from django.contrib.auth import update_session_auth_hash
update_session_auth_hash(request, user)

# Or invalidate all sessions
Session.objects.filter(expire_date__gte=timezone.now()).delete()
```

---

## Security Monitoring

### Honeypot Monitoring

```python
# Log honeypot triggers
honeypot_logger.warning(
    f'Honeypot triggered: {request.path}',
    extra={
        'ip': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT'),
        'path': request.path,
    }
)
```

### Failed Login Monitoring

```python
@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts."""
    logger.warning(
        f'Failed login attempt for user: {credentials.get("username")}',
        extra={
            'ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
        }
    )
```

### Alert Thresholds

| Event | Threshold | Action |
|-------|-----------|--------|
| Failed logins | 5 in 15 minutes | Lock account, alert admin |
| Honeypot triggers | 10 in 1 hour | Block IP, alert security |
| API rate limit | Exceeded 100 times | Temporary ban, alert |
| WebSocket connections | 50 from same IP | Block IP |

---

## Incident Response

### Security Incident Types

| Type | Description | Response |
|------|-------------|----------|
| **Unauthorized Access** | Successful login without authorization | Revoke sessions, investigate, reset passwords |
| **Data Breach** | Unauthorized data access/export | Contain, assess, notify, remediate |
| **DDoS Attack** | Denial of service | Enable rate limiting, contact hosting |
| **Malware** | Malicious code injection | Isolate, scan, remove, patch |
| **Insider Threat** | Malicious employee/contractor | Revoke access, investigate, legal |

### Incident Response Procedure

1. **Detection:** Identify security incident
2. **Containment:** Limit damage and spread
3. **Eradication:** Remove threat
4. **Recovery:** Restore systems
5. **Lessons Learned:** Document and improve

### Contact Information

| Role | Contact |
|------|---------|
| Security Team | security@example.com |
| System Admin | admin@example.com |
| Emergency | +1-XXX-XXX-XXXX |

---

## Security Checklist

### Pre-Deployment Checklist

- [ ] SECRET_KEY is set from environment variable
- [ ] DEBUG is set to False
- [ ] ALLOWED_HOSTS is configured
- [ ] DATABASE_PASSWORD is secure
- [ ] HTTPS is enabled
- [ ] Security headers are configured
- [ ] CORS is properly configured
- [ ] Rate limiting is enabled
- [ ] Honeypot protection is active
- [ ] Audit logging is working
- [ ] Backup system is configured
- [ ] Monitoring is enabled

### Regular Security Tasks

| Task | Frequency |
|------|-----------|
| Review audit logs | Daily |
| Check for security updates | Weekly |
| Review user permissions | Monthly |
| Test backup restoration | Monthly |
| Security audit | Quarterly |
| Penetration testing | Annually |
| Update dependencies | As released |

### Security Update Procedure

1. Review security advisories
2. Test updates in staging
3. Backup production database
4. Apply updates during maintenance window
5. Verify functionality
6. Monitor for issues

---

*Last Updated: March 15, 2026*  
*Version: 1.0*
