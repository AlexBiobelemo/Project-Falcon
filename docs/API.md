# API Documentation

> **Project:** Project Falcon - Airport Operations Management System
> **API Version:** v1
> **Base URL:** `/api/v1/`
> **Last Updated:** March 24, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Request/Response Format](#requestresponse-format)
5. [Endpoints Reference](#endpoints-reference)
6. [Filtering & Search](#filtering--search)
7. [Pagination](#pagination)
8. [Error Handling](#error-handling)
9. [WebSocket API](#websocket-api)
10. [Code Examples](#code-examples)

---

## Overview

The Project Falcon API is a RESTful API built with Django REST Framework. It provides programmatic access to all airport operations data including flights, gates, passengers, staff, fiscal assessments, and more.

### Base URL

```
Production: https://your-domain.com/api/v1/
Development: http://localhost:8000/api/v1/
```

### Available Resources

| Resource | Endpoint | Description |
|----------|----------|-------------|
| Airports | `/api/v1/airports/` | Airport facilities |
| Gates | `/api/v1/gates/` | Airport gates |
| Flights | `/api/v1/flights/` | Flight operations |
| Passengers | `/api/v1/passengers/` | Passenger records |
| Staff | `/api/v1/staff/` | Staff members |
| Staff Assignments | `/api/v1/staff-assignments/` | Staff-to-flight assignments |
| Events | `/api/v1/events/` | Event logs (read-only) |
| Assessments | `/api/v1/assessments/` | Fiscal assessments |
| Aircraft | `/api/v1/aircraft/` | Aircraft registry |
| Crew | `/api/v1/crew/` | Crew members |
| Maintenance | `/api/v1/maintenance/` | Maintenance logs |
| Incidents | `/api/v1/incidents/` | Incident reports |
| Reports | `/api/v1/reports/` | Generated reports |
| Documents | `/api/v1/documents/` | Documents |

### Custom Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/v1/dashboard-summary/` | Dashboard aggregate metrics |
| `/api/v1/trend-data/` | Historical trend data |
| `/api/v1/analytics/` | Analytics data |
| `/api/v1/map-data/` | Map visualization data |
| `/api/v1/weather/search/` | Weather data lookup |

### API Documentation UIs

Interactive API documentation is available at:

- **Swagger UI:** `/api/schema/swagger-ui/`
- **ReDoc:** `/api/schema/redoc/`
- **OpenAPI Schema:** `/api/schema/`

---

## Authentication

The API supports two authentication methods:

### 1. Token Authentication (Recommended for API Clients)

Token authentication is **CSRF-exempt** and recommended for programmatic API access.

#### Obtain Token

```bash
curl -X POST http://localhost:8000/api/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

Response:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

#### Use Token

Include the token in the `Authorization` header:

```bash
curl -X GET http://localhost:8000/api/v1/flights/ \
  -H "Authorization: Bearer 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

### 2. Session Authentication (For Browser Clients)

Session authentication requires CSRF tokens and is suitable for browser-based clients.

#### Login

```bash
curl -X POST http://localhost:8000/accounts/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-username&password=your-password" \
  --cookie-jar cookies.txt
```

#### Use Session

```bash
curl -X GET http://localhost:8000/api/v1/flights/ \
  --cookie cookies.txt \
  -H "X-CSRFToken: your-csrf-token"
```

### Authentication Comparison

| Feature | Token Auth | Session Auth |
|---------|-----------|--------------|
| CSRF Protection | Not Required | Required |
| Use Case | API Clients, Mobile Apps | Browser Clients |
| State | Stateless | Stateful |
| Header | `Authorization: Bearer <token>` | `Cookie: sessionid=<session>` |

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

| User Type | Rate Limit |
|-----------|-----------|
| Anonymous | 100 requests/hour |
| Authenticated | 1000 requests/hour |
| Burst (all users) | 60 requests/minute |

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1647360000
```

### Rate Limit Exceeded

```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

---

## Request/Response Format

### Request Format

**Content-Type:** `application/json`

```json
{
  "field_name": "value",
  "another_field": 123
}
```

### Response Format

**Content-Type:** `application/json`

#### Single Object

```json
{
  "id": 1,
  "code": "LOS",
  "name": "Murtala Muhammed International Airport",
  "city": "Lagos",
  "is_active": true,
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-01T10:00:00Z"
}
```

#### List Response (Paginated)

```json
{
  "count": 100,
  "next": "http://api.example.com/v1/flights/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "flight_number": "BA123",
      "status": "scheduled"
    }
  ]
}
```

#### Error Response

```json
{
  "error": "Invalid input",
  "details": {
    "flight_number": ["This field is required."],
    "status": ["\"invalid_status\" is not a valid choice."]
  }
}
```

---

## Endpoints Reference

### Airports

Manage airport facilities.

#### List Airports

```http
GET /api/v1/airports/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search code, name, or city |
| `is_active` | boolean | Filter by active status |
| `city` | string | Filter by city |
| `ordering` | string | Sort field (prefix with `-` for desc) |

**Response:**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "code": "LOS",
      "name": "Murtala Muhammed International Airport",
      "city": "Lagos",
      "timezone": "UTC",
      "is_active": true,
      "created_at": "2026-03-01T10:00:00Z",
      "updated_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

#### Create Airport

```http
POST /api/v1/airports/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "code": "JFK",
  "name": "John F. Kennedy International Airport",
  "city": "New York",
  "timezone": "America/New_York",
  "is_active": true
}
```

#### Get Airport

```http
GET /api/v1/airports/{id}/
```

#### Update Airport

```http
PUT /api/v1/airports/{id}/
Content-Type: application/json
Authorization: Bearer <token>
```

#### Delete Airport

```http
DELETE /api/v1/airports/{id}/
Authorization: Bearer <token>
```

---

### Gates

Manage airport gates.

#### List Gates

```http
GET /api/v1/gates/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `terminal` | string | Filter by terminal (A, B, C) |
| `status` | string | Filter by status |
| `capacity` | string | Filter by capacity |
| `airport` | integer | Filter by airport ID |

**Status Options:** `available`, `occupied`, `maintenance`, `closed`

**Response:**
```json
{
  "count": 50,
  "next": "http://api.example.com/v1/gates/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "gate_id": "A1",
      "terminal": "A",
      "capacity": "wide-body",
      "status": "available",
      "airport": 1,
      "created_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

#### Create Gate

```http
POST /api/v1/gates/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "gate_id": "B5",
  "terminal": "B",
  "capacity": "narrow-body",
  "status": "available",
  "airport": 1
}
```

---

### Flights

Manage flight operations.

#### List Flights

```http
GET /api/v1/flights/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | string | Filter by flight status |
| `airline` | string | Filter by airline |
| `origin` | string | Filter by origin airport code |
| `destination` | string | Filter by destination airport code |
| `gate` | integer | Filter by gate ID |
| `date_from` | date | Filter from date (YYYY-MM-DD) |
| `date_to` | date | Filter to date (YYYY-MM-DD) |
| `search` | string | Search flight number |

**Status Options:** `scheduled`, `boarding`, `departed`, `arrived`, `delayed`, `cancelled`

**Response:**
```json
{
  "count": 150,
  "next": "http://api.example.com/v1/flights/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "flight_number": "BA123",
      "airline": "British Airways",
      "origin": "LOS",
      "destination": "LHR",
      "scheduled_departure": "2026-03-15T14:00:00Z",
      "actual_departure": "2026-03-15T14:15:00Z",
      "scheduled_arrival": "2026-03-15T20:00:00Z",
      "actual_arrival": null,
      "gate": 5,
      "status": "boarding",
      "delay_minutes": 15,
      "aircraft_type": "Boeing 777",
      "created_at": "2026-03-01T10:00:00Z"
    }
  ]
}
```

#### Create Flight

```http
POST /api/v1/flights/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "flight_number": "BA456",
  "airline": "British Airways",
  "origin": "LOS",
  "destination": "JFK",
  "scheduled_departure": "2026-03-16T10:00:00Z",
  "scheduled_arrival": "2026-03-16T18:00:00Z",
  "gate": 3,
  "status": "scheduled",
  "aircraft_type": "Boeing 787"
}
```

#### Update Flight

```http
PUT /api/v1/flights/{id}/
Content-Type: application/json
Authorization: Bearer <token>
```

**Example - Update Status:**
```json
{
  "status": "delayed",
  "delay_minutes": 45
}
```

---

### Passengers

Manage passenger records.

#### List Passengers

```http
GET /api/v1/passengers/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `flight` | integer | Filter by flight ID |
| `status` | string | Filter by status |
| `search` | string | Search name or passport |

**Status Options:** `checked_in`, `boarded`, `arrived`, `no_show`

#### Create Passenger

```http
POST /api/v1/passengers/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "passport_number": "A12345678",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "flight": 1,
  "seat_number": "12A",
  "status": "checked_in",
  "checked_bags": 2
}
```

---

### Staff

Manage staff members.

#### List Staff

```http
GET /api/v1/staff/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `role` | string | Filter by role |
| `is_available` | boolean | Filter by availability |
| `search` | string | Search name or employee number |

**Role Options:** `pilot`, `co_pilot`, `cabin_crew`, `ground_crew`, `security`, `cleaning`, `maintenance`

#### Create Staff

```http
POST /api/v1/staff/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "employee_number": "EMP001",
  "role": "pilot",
  "certification": "ATP, B777, B787",
  "is_available": true,
  "email": "jane.smith@airline.com",
  "phone": "+1234567890"
}
```

---

### Staff Assignments

Manage staff-to-flight assignments.

#### List Assignments

```http
GET /api/v1/staff-assignments/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `staff` | integer | Filter by staff ID |
| `flight` | integer | Filter by flight ID |
| `assignment_type` | string | Filter by type |

#### Create Assignment

```http
POST /api/v1/staff-assignments/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "staff": 1,
  "flight": 5,
  "assignment_type": "pilot"
}
```

**Note:** The API automatically checks for scheduling conflicts.

---

### Fiscal Assessments

Manage financial assessments.

#### List Assessments

```http
GET /api/v1/assessments/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `airport` | integer | Filter by airport ID |
| `period_type` | string | Filter by period type |
| `status` | string | Filter by status |
| `start_date` | date | Filter from date |
| `end_date` | date | Filter to date |

**Period Types:** `daily`, `weekly`, `monthly`, `quarterly`, `yearly`

**Status Options:** `draft`, `in_progress`, `completed`, `approved`, `rejected`

#### Create Assessment

```http
POST /api/v1/assessments/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "airport": 1,
  "period_type": "monthly",
  "start_date": "2026-03-01",
  "end_date": "2026-03-31",
  "status": "draft",
  "fuel_revenue": 500000.00,
  "parking_revenue": 150000.00,
  "retail_revenue": 300000.00,
  "landing_fees": 400000.00,
  "cargo_revenue": 200000.00,
  "other_revenue": 50000.00,
  "security_costs": 250000.00,
  "maintenance_costs": 180000.00,
  "operational_costs": 300000.00,
  "staff_costs": 450000.00,
  "utility_costs": 100000.00,
  "other_expenses": 50000.00,
  "passenger_count": 50000,
  "flight_count": 1200
}
```

#### Get Assessment

```http
GET /api/v1/assessments/{id}/
```

#### Update Assessment

```http
PUT /api/v1/assessments/{id}/
Content-Type: application/json
Authorization: Bearer <token>
```

#### Approve Assessment

```http
POST /api/v1/assessments/{id}/approve/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "approved": true,
  "comments": "All figures verified and approved."
}
```

**Permissions:** Requires `approver` role or above.

#### Delete Assessment

```http
DELETE /api/v1/assessments/{id}/
Authorization: Bearer <token>
```

**Permissions:** Requires superuser (admin) privileges.

---

### Events (Read-Only)

View event logs.

#### List Events

```http
GET /api/v1/events/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_type` | string | Filter by event type |
| `severity` | string | Filter by severity |
| `action` | string | Filter by action |
| `date_from` | date | Filter from date |
| `date_to` | date | Filter to date |

**Event Types:** `flight`, `gate`, `fiscal_assessment`, `report`, `document`, `staff`, `passenger`, `system`

**Severity Options:** `info`, `warning`, `error`

**Actions:** `create`, `update`, `delete`, `approve`, `reject`, `login`, `logout`, `export`

---

### Custom Endpoints

#### Dashboard Summary

Aggregated dashboard metrics.

```http
GET /api/v1/dashboard-summary/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_airports": 5,
  "total_gates": 50,
  "total_flights": 1200,
  "available_gates": 12,
  "active_flights": 45,
  "delayed_flights": 3,
  "flights_by_status": {
    "scheduled": 800,
    "boarding": 15,
    "departed": 250,
    "arrived": 100,
    "delayed": 25,
    "cancelled": 10
  },
  "passengers_today": 8500,
  "gate_utilization": 76.0,
  "on_time_performance": 92.5
}
```

**Caching:** 5 minutes

#### Trend Data

Historical trend data for charts.

```http
GET /api/v1/trend-data/
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | string | Time period (`day`, `week`, `month`, `6months`, `year`) |
| `metric` | string | Metric type (`revenue`, `passengers`, `flights`) |
| `airport` | integer | Filter by airport ID |

**Response:**
```json
{
  "period": "6months",
  "metric": "revenue",
  "data": {
    "labels": ["Oct 2025", "Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026"],
    "datasets": [
      {
        "label": "Total Revenue",
        "data": [1500000, 1650000, 1800000, 1720000, 1890000, 2100000],
        "borderColor": "#0d6efd",
        "backgroundColor": "rgba(13, 110, 253, 0.1)"
      },
      {
        "label": "Total Expenses",
        "data": [1200000, 1300000, 1400000, 1350000, 1450000, 1550000],
        "borderColor": "#dc3545",
        "backgroundColor": "rgba(220, 53, 69, 0.1)"
      }
    ]
  }
}
```

#### Analytics Data

Detailed analytics metrics.

```http
GET /api/v1/analytics/
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `airport` | integer | Filter by airport ID |
| `metric` | string | Metric type |
| `period` | string | Time period |

#### Map Data

Geographic data for map visualization.

```http
GET /api/v1/map-data/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "airports": [
    {
      "code": "LOS",
      "name": "Murtala Muhammed International Airport",
      "latitude": 6.5774,
      "longitude": 3.3212,
      "active_flights": 15
    }
  ],
  "flights": [
    {
      "flight_number": "BA123",
      "origin": "LOS",
      "destination": "LHR",
      "latitude": 10.5,
      "longitude": 5.2,
      "altitude": 35000,
      "speed": 550,
      "status": "departed"
    }
  ]
}
```

#### Weather Search

Weather data for airports.

```http
GET /api/v1/weather/search/?airport=LOS
```

**Response:**
```json
{
  "airport": "LOS",
  "temperature": 32.5,
  "humidity": 75,
  "wind_speed": 15.2,
  "wind_direction": 220,
  "conditions": "Partly Cloudy",
  "visibility": 10.0,
  "pressure": 1013.25,
  "last_updated": "2026-03-15T14:00:00Z"
}
```

---

## Filtering & Search

### Search

Most endpoints support full-text search:

```http
GET /api/v1/flights/?search=BA123
GET /api/v1/airports/?search=Lagos
GET /api/v1/staff/?search=pilot
```

### Field Filters

Filter by specific fields:

```http
GET /api/v1/flights/?status=delayed&airline=British Airways
GET /api/v1/gates/?terminal=A&status=available
GET /api/v1/assessments/?airport=1&period_type=monthly
```

### Date Range Filters

```http
GET /api/v1/flights/?date_from=2026-03-01&date_to=2026-03-31
GET /api/v1/events/?date_from=2026-03-01
```

### Ordering

Sort results by any field:

```http
GET /api/v1/flights/?ordering=-scheduled_departure  # Descending
GET /api/v1/flights/?ordering=flight_number         # Ascending
GET /api/v1/assessments/?ordering=airport__name     # By related field
```

---

## Pagination

### Default Pagination

- **Page Size:** 50 items per page
- **Max Page Size:** 100 items per page

### Pagination Controls

```http
GET /api/v1/flights/?page=2
GET /api/v1/flights/?page=3&page_size=25
```

### Pagination Response

```json
{
  "count": 250,
  "next": "http://api.example.com/v1/flights/?page=3&page_size=25",
  "previous": "http://api.example.com/v1/flights/?page=1&page_size=25",
  "results": [...]
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (authentication required) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not Found |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "error": "Error message",
  "details": {
    "field_name": ["Error detail 1", "Error detail 2"]
  },
  "code": "invalid_input"
}
```

### Common Errors

#### Validation Error (400)

```json
{
  "error": "Validation failed",
  "details": {
    "flight_number": ["This field is required."],
    "status": ["\"invalid\" is not a valid choice."]
  }
}
```

#### Authentication Error (401)

```json
{
  "error": "Authentication credentials were not provided."
}
```

#### Permission Error (403)

```json
{
  "error": "You do not have permission to perform this action.",
  "code": "permission_denied"
}
```

#### Not Found Error (404)

```json
{
  "error": "Not found."
}
```

#### Rate Limit Error (429)

```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

---

## WebSocket API

Real-time updates via WebSocket connections.

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/dashboard/');
```

### Authentication

WebSocket connections require authentication via session or token:

```javascript
// Session authentication (browser)
const ws = new WebSocket('ws://localhost:8000/ws/dashboard/');

// Token authentication (custom header in channels)
const ws = new WebSocket('ws://localhost:8000/ws/dashboard/?token=YOUR_TOKEN');
```

### Available Channels

| Channel | URL | Description |
|---------|-----|-------------|
| Dashboard | `/ws/dashboard/` | Real-time dashboard metrics |
| Flights | `/ws/flights/` | Flight status updates |
| Gates | `/ws/gates/` | Gate status updates |
| Events | `/ws/events/` | Event log updates |
| Notifications | `/ws/notifications/` | Push notifications |

### Message Format

#### Incoming Messages

```json
{
  "type": "flight_update",
  "data": {
    "flight_number": "BA123",
    "status": "delayed",
    "delay_minutes": 30
  },
  "timestamp": "2026-03-15T14:30:00Z"
}
```

#### Outgoing Messages

```json
{
  "action": "ping"
}
```

### Example Usage

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/flights/');

ws.onopen = () => {
  console.log('Connected to flight updates');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Flight update:', data);
  
  if (data.type === 'flight_update') {
    updateFlightDisplay(data.data);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Connection closed');
};
```

---

## Code Examples

### Python (requests)

```python
import requests

BASE_URL = 'http://localhost:8000/api/v1'

# Authenticate
response = requests.post(f'{BASE_URL}/api-token-auth/', json={
    'username': 'admin',
    'password': 'password123'
})
token = response.json()['token']

headers = {'Authorization': f'Bearer {token}'}

# List flights
response = requests.get(f'{BASE_URL}/flights/', headers=headers)
flights = response.json()['results']

# Create flight
response = requests.post(f'{BASE_URL}/flights/', headers=headers, json={
    'flight_number': 'BA789',
    'airline': 'British Airways',
    'origin': 'LOS',
    'destination': 'JFK',
    'scheduled_departure': '2026-03-20T10:00:00Z',
    'scheduled_arrival': '2026-03-20T18:00:00Z',
    'status': 'scheduled'
})
flight = response.json()

# Update flight
response = requests.put(f'{BASE_URL}/flights/{flight["id"]}/', headers=headers, json={
    'status': 'delayed',
    'delay_minutes': 45
})

# Get dashboard summary
response = requests.get(f'{BASE_URL}/dashboard-summary/', headers=headers)
dashboard = response.json()
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Authenticate
async function login(username, password) {
  const response = await fetch(`${BASE_URL}/api-token-auth/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await response.json();
  return data.token;
}

// List flights
async function getFlights(token) {
  const response = await fetch(`${BASE_URL}/flights/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  return data.results;
}

// Create flight
async function createFlight(token, flightData) {
  const response = await fetch(`${BASE_URL}/flights/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(flightData)
  });
  return await response.json();
}

// Usage
const token = await login('admin', 'password123');
const flights = await getFlights(token);
console.log('Flights:', flights);
```

### cURL

```bash
# Get API token
TOKEN=$(curl -s -X POST http://localhost:8000/api/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}' | jq -r '.token')

# List all airports
curl -X GET http://localhost:8000/api/v1/airports/ \
  -H "Authorization: Bearer $TOKEN"

# Create a new flight
curl -X POST http://localhost:8000/api/v1/flights/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_number": "BA123",
    "airline": "British Airways",
    "origin": "LOS",
    "destination": "LHR",
    "scheduled_departure": "2026-03-20T14:00:00Z",
    "status": "scheduled"
  }'

# Get dashboard summary
curl -X GET http://localhost:8000/api/v1/dashboard-summary/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## API Changelog

### Version 1.0 (March 2026)

**Initial Release:**
- All core CRUD endpoints
- Dashboard summary API
- Trend data API
- Analytics API
- Map data API
- Weather integration
- WebSocket real-time updates
- Role-based access control
- Rate limiting
- Comprehensive filtering

---

*Last Updated: March 24, 2026*
*Version: 1.0*
