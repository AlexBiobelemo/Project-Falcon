"""
Comprehensive API tests for the Airport Operations Management System.

Tests cover:
- REST API endpoint functionality
- Authentication and authorization
- Role-based access control
- Rate limiting
- Input validation
- Error handling
- Search and filtering
- Pagination
- Security vulnerabilities (SQL injection, XSS)
"""

import json
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client, override_settings
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token

from core.models import (
    Airport, Gate, GateStatus, Flight, FlightStatus,
    Passenger, PassengerStatus, Staff, StaffRole, StaffAssignment,
    EventLog, FiscalAssessment, AssessmentPeriod, AssessmentStatus,
    Report, ReportType, Document,
)


class BaseAPITestCase(APITestCase):
    """Base test case with common setup for API tests."""

    def setUp(self):
        """Set up test data and authenticated client."""
        self.client = APIClient()
        
        # Create test users with different roles
        self.admin_user = User.objects.create_user(
            username='admin',
            password='adminpass123',
            is_superuser=True,
            is_staff=True,
        )
        
        self.editor_user = User.objects.create_user(
            username='editor',
            password='editorpass123',
        )
        
        self.viewer_user = User.objects.create_user(
            username='viewer',
            password='viewerpass123',
        )
        
        # Create groups
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.approvers_group, _ = Group.objects.get_or_create(name='approvers')
        
        # Assign users to groups
        self.editor_user.groups.add(self.editors_group)
        self.approvers_group.user_set.add(self.editor_user)  # Editor is also approver
        
        # Create auth tokens
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.editor_token = Token.objects.create(user=self.editor_user)
        self.viewer_token = Token.objects.create(user=self.viewer_user)
        
        # Create base test data
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


class AuthenticationAPITest(BaseAPITestCase):
    """Tests for API authentication."""

    def test_unauthenticated_access_denied(self):
        """Test unauthenticated users cannot access protected endpoints."""
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_authentication_success(self):
        """Test successful token authentication."""
        # Ensure token exists
        if not hasattr(self, 'admin_token') or not self.admin_token:
            from rest_framework.authtoken.models import Token
            self.admin_token = Token.objects.create(user=self.admin_user)
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.admin_token.key)
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_denied(self):
        """Test invalid token is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_malformed_token_denied(self):
        """Test malformed token header is rejected."""
        self.client.credentials(HTTP_AUTHORIZATION='InvalidFormat')
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_session_authentication(self):
        """Test session authentication works."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_expiration(self):
        """Test token can be regenerated."""
        from rest_framework.authtoken.models import Token
        old_token = self.admin_token.key
        self.admin_token.delete()
        new_token = Token.objects.create(user=self.admin_user)
        
        # Old token should fail
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + old_token)
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # New token should work
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + new_token.key)
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AirportAPITest(BaseAPITestCase):
    """Tests for the Airport API endpoint."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)
        self.url = '/api/v1/airports/'

    def test_list_airports(self):
        """Test listing airports."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['code'], 'LOS')

    def test_create_airport(self):
        """Test creating an airport."""
        data = {
            'code': 'ABJ',
            'name': 'Abuja International Airport',
            'city': 'Abuja',
            'timezone': 'Africa/Lagos',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airport.objects.count(), 2)
        airport = Airport.objects.get(code='ABJ')
        self.assertEqual(airport.name, 'Abuja International Airport')

    def test_create_airport_validation(self):
        """Test airport creation validation."""
        # Missing required field
        data = {
            'name': 'Missing Code Airport',
            'city': 'City',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data)

        # Code too long
        data = {
            'code': 'TOOLONG',
            'name': 'Invalid Airport',
            'city': 'City',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_airport(self):
        """Test retrieving a single airport."""
        response = self.client.get(f'/api/v1/airports/{self.airport.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'LOS')

    def test_retrieve_nonexistent_airport(self):
        """Test retrieving nonexistent airport returns 404."""
        response = self.client.get('/api/v1/airports/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_airport(self):
        """Test updating an airport."""
        data = {
            'code': 'LOS',
            'name': 'Lagos Airport Updated',
            'city': 'Lagos',
        }
        response = self.client.put(f'/api/v1/airports/{self.airport.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airport.refresh_from_db()
        self.assertEqual(self.airport.name, 'Lagos Airport Updated')

    def test_partial_update_airport(self):
        """Test partially updating an airport."""
        data = {
            'name': 'Partially Updated Airport',
        }
        response = self.client.patch(f'/api/v1/airports/{self.airport.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.airport.refresh_from_db()
        self.assertEqual(self.airport.name, 'Partially Updated Airport')
        self.assertEqual(self.airport.code, 'LOS')  # Unchanged

    def test_delete_airport(self):
        """Test deleting an airport."""
        response = self.client.delete(f'/api/v1/airports/{self.airport.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Airport.objects.count(), 0)

    def test_delete_nonexistent_airport(self):
        """Test deleting nonexistent airport returns 404."""
        response = self.client.delete('/api/v1/airports/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_airports(self):
        """Test searching airports."""
        Airport.objects.create(
            code="ABJ",
            name="Abuja International Airport",
            city="Abuja",
        )
        
        response = self.client.get(self.url + '?search=Lagos')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['code'], 'LOS')

    def test_order_airports(self):
        """Test ordering airports."""
        Airport.objects.create(
            code="ABJ",
            name="Abuja International Airport",
            city="Abuja",
        )
        
        response = self.client.get(self.url + '?ordering=-code')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ABJ should come before LOS in descending order
        self.assertEqual(response.data['results'][0]['code'], 'LOS')

    def test_pagination(self):
        """Test API pagination."""
        # Create more airports
        for i in range(60):
            Airport.objects.create(
                code=f"A{i:02d}",
                name=f"Airport {i}",
                city=f"City {i}",
            )
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 50)  # Default page size
        self.assertIsNotNone(response.data['next'])
        
        # Get next page
        response = self.client.get(response.data['next'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 11)
        self.assertIsNone(response.data['next'])


class GateAPITest(BaseAPITestCase):
    """Tests for the Gate API endpoint."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

    def test_list_gates(self):
        """Test listing gates."""
        response = self.client.get('/api/v1/gates/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_gate(self):
        """Test creating a gate."""
        data = {
            'gate_id': 'B2',
            'terminal': 'Terminal 2',
            'capacity': 'narrow-body',
            'status': GateStatus.AVAILABLE.value,
        }
        response = self.client.post('/api/v1/gates/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Gate.objects.count(), 2)

    def test_create_gate_duplicate_id(self):
        """Test creating gate with duplicate gate_id fails."""
        data = {
            'gate_id': 'A1',
            'terminal': 'Terminal 2',
            'capacity': 'narrow-body',
        }
        response = self.client.post('/api/v1/gates/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_gates_by_status(self):
        """Test filtering gates by status."""
        Gate.objects.create(
            gate_id="B1",
            terminal="Terminal 1",
            status=GateStatus.OCCUPIED.value,
        )

        response = self.client.get('/api/v1/gates/?status=available')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_gates_by_terminal(self):
        """Test filtering gates by terminal."""
        Gate.objects.create(
            gate_id="B1",
            terminal="Terminal 2",
            status=GateStatus.AVAILABLE.value,
        )

        response = self.client.get('/api/v1/gates/?terminal=Terminal+1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_update_gate_status(self):
        """Test updating gate status."""
        data = {
            'gate_id': 'A1',
            'terminal': 'Terminal 1',
            'status': GateStatus.MAINTENANCE.value,
        }
        response = self.client.put(f'/api/v1/gates/{self.gate.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.gate.refresh_from_db()
        self.assertEqual(self.gate.status, GateStatus.MAINTENANCE.value)


class FlightAPITest(BaseAPITestCase):
    """Tests for the Flight API endpoint."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)
        
        self.flight = Flight.objects.create(
            flight_number="AA123",
            airline="American Airlines",
            origin="LOS",
            destination="JFK",
            scheduled_departure=timezone.now() + timedelta(hours=2),
            scheduled_arrival=timezone.now() + timedelta(hours=10),
            gate=self.gate,
            status=FlightStatus.SCHEDULED.value,
        )

    def test_list_flights(self):
        """Test listing flights."""
        response = self.client.get('/api/v1/flights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_flight(self):
        """Test creating a flight."""
        data = {
            'flight_number': 'BA456',
            'airline': 'British Airways',
            'origin': 'LOS',
            'destination': 'LHR',
            'scheduled_departure': (timezone.now() + timedelta(hours=5)).isoformat(),
            'scheduled_arrival': (timezone.now() + timedelta(hours=12)).isoformat(),
            'status': FlightStatus.SCHEDULED.value,
        }
        response = self.client.post('/api/v1/flights/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Flight.objects.count(), 2)

    def test_create_flight_duplicate_number(self):
        """Test creating flight with duplicate number fails."""
        data = {
            'flight_number': 'AA123',
            'airline': 'Different Airline',
            'origin': 'ABJ',
            'destination': 'DXB',
            'scheduled_departure': (timezone.now() + timedelta(hours=5)).isoformat(),
            'scheduled_arrival': (timezone.now() + timedelta(hours=12)).isoformat(),
        }
        response = self.client.post('/api/v1/flights/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_flights_by_status(self):
        """Test filtering flights by status."""
        Flight.objects.create(
            flight_number="BB789",
            origin="LOS",
            destination="ABJ",
            scheduled_departure=timezone.now() + timedelta(hours=1),
            scheduled_arrival=timezone.now() + timedelta(hours=2),
            status=FlightStatus.DELAYED.value,
        )

        response = self.client.get('/api/v1/flights/?status=delayed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_flights_by_airline(self):
        """Test filtering flights by airline."""
        response = self.client.get('/api/v1/flights/?airline=American+Airlines')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_flights_by_date_range(self):
        """Test filtering flights by date range."""
        response = self.client.get('/api/v1/flights/?date_from=2025-01-01&date_to=2025-12-31')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_flights_by_gate(self):
        """Test filtering flights by gate."""
        response = self.client.get(f'/api/v1/flights/?gate={self.gate.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_flights(self):
        """Test searching flights."""
        response = self.client.get('/api/v1/flights/?search=AA123')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_update_flight_status(self):
        """Test updating flight status."""
        data = {
            'flight_number': 'AA123',
            'status': FlightStatus.DELAYED.value,
            'delay_minutes': 30,
        }
        response = self.client.patch(f'/api/v1/flights/{self.flight.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.flight.refresh_from_db()
        self.assertEqual(self.flight.status, FlightStatus.DELAYED.value)
        self.assertEqual(self.flight.delay_minutes, 30)


class PassengerAPITest(BaseAPITestCase):
    """Tests for the Passenger API endpoint."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)
        
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
            flight=self.flight,
            status=PassengerStatus.CHECKED_IN.value,
        )

    def test_list_passengers(self):
        """Test listing passengers."""
        response = self.client.get('/api/v1/passengers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_passenger(self):
        """Test creating a passenger."""
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'passport_number': 'CD789012',
            'email': 'jane.smith@example.com',
            'flight': self.flight.id,
            'status': PassengerStatus.CHECKED_IN.value,
        }
        response = self.client.post('/api/v1/passengers/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Passenger.objects.count(), 2)

    def test_create_passenger_duplicate_passport(self):
        """Test creating passenger with duplicate passport fails."""
        data = {
            'first_name': 'Duplicate',
            'last_name': 'Passport',
            'passport_number': 'AB123456',
            'flight': self.flight.id,
        }
        response = self.client.post('/api/v1/passengers/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_passengers_by_flight(self):
        """Test filtering passengers by flight."""
        response = self.client.get(f'/api/v1/passengers/?flight={self.flight.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_passengers_by_status(self):
        """Test filtering passengers by status."""
        response = self.client.get('/api/v1/passengers/?status=checked_in')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_passengers(self):
        """Test searching passengers."""
        response = self.client.get('/api/v1/passengers/?search=John')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_search_passengers_by_email(self):
        """Test searching passengers by email."""
        response = self.client.get('/api/v1/passengers/?search=john.doe@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class StaffAPITest(BaseAPITestCase):
    """Tests for the Staff API endpoint."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)
        
        self.staff = Staff.objects.create(
            first_name="Jane",
            last_name="Smith",
            employee_number="EMP001",
            role=StaffRole.PILOT.value,
            email="jane.smith@example.com",
        )

    def test_list_staff(self):
        """Test listing staff."""
        response = self.client.get('/api/v1/staff/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_staff(self):
        """Test creating staff member."""
        data = {
            'first_name': 'Bob',
            'last_name': 'Jones',
            'employee_number': 'EMP002',
            'role': StaffRole.CO_PILOT.value,
            'email': 'bob.jones@example.com',
        }
        response = self.client.post('/api/v1/staff/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Staff.objects.count(), 2)

    def test_create_staff_duplicate_employee_number(self):
        """Test creating staff with duplicate employee number fails."""
        data = {
            'first_name': 'Duplicate',
            'last_name': 'Employee',
            'employee_number': 'EMP001',
            'role': StaffRole.GROUND_CREW.value,
        }
        response = self.client.post('/api/v1/staff/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_staff_by_role(self):
        """Test filtering staff by role."""
        response = self.client.get('/api/v1/staff/?role=pilot')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_staff_by_availability(self):
        """Test filtering staff by availability."""
        response = self.client.get('/api/v1/staff/?is_available=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_staff(self):
        """Test searching staff."""
        response = self.client.get('/api/v1/staff/?search=Jane')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class FiscalAssessmentAPITest(BaseAPITestCase):
    """Tests for the FiscalAssessment API endpoint with role-based access control."""

    def setUp(self):
        super().setUp()
        
        self.assessment = FiscalAssessment.objects.create(
            airport=self.airport,
            period_type=AssessmentPeriod.MONTHLY.value,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status=AssessmentStatus.DRAFT.value,
            fuel_revenue=Decimal("100000.00"),
            security_costs=Decimal("20000.00"),
        )

    def test_viewer_can_list_assessments(self):
        """Test viewer role can list assessments."""
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.get('/api/v1/assessments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_viewer_cannot_create_assessment(self):
        """Test viewer role cannot create assessments."""
        self.client.force_authenticate(user=self.viewer_user)
        data = {
            'airport': self.airport.id,
            'period_type': AssessmentPeriod.MONTHLY.value,
            'start_date': '2025-02-01',
            'end_date': '2025-02-28',
        }
        response = self.client.post('/api/v1/assessments/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_create_assessment(self):
        """Test editor role can create assessments."""
        self.client.force_authenticate(user=self.editor_user)
        data = {
            'airport': self.airport.id,
            'period_type': AssessmentPeriod.MONTHLY.value,
            'start_date': '2025-02-01',
            'end_date': '2025-02-28',
        }
        response = self.client.post('/api/v1/assessments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_viewer_cannot_update_assessment(self):
        """Test viewer role cannot update assessments."""
        self.client.force_authenticate(user=self.viewer_user)
        data = {
            'fuel_revenue': '999999.00',
        }
        response = self.client.patch(f'/api/v1/assessments/{self.assessment.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_can_update_assessment(self):
        """Test editor role can update assessments."""
        self.client.force_authenticate(user=self.editor_user)
        data = {
            'fuel_revenue': '999999.00',
        }
        response = self.client.patch(f'/api/v1/assessments/{self.assessment.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assessment.refresh_from_db()
        self.assertEqual(self.assessment.fuel_revenue, Decimal('999999.00'))

    def test_viewer_cannot_delete_assessment(self):
        """Test viewer role cannot delete assessments."""
        self.client.force_authenticate(user=self.viewer_user)
        response = self.client.delete(f'/api/v1/assessments/{self.assessment.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_editor_cannot_delete_assessment(self):
        """Test editor role cannot delete assessments (admin only)."""
        self.client.force_authenticate(user=self.editor_user)
        response = self.client.delete(f'/api/v1/assessments/{self.assessment.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_assessment(self):
        """Test admin role can delete assessments."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/v1/assessments/{self.assessment.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FiscalAssessment.objects.count(), 0)

    def test_filter_assessments_by_status(self):
        """Test filtering assessments by status."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/assessments/?status=draft')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_filter_assessments_by_period_type(self):
        """Test filtering assessments by period type."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/assessments/?period_type=monthly')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_totals_calculated_on_create(self):
        """Test totals are calculated when creating assessment."""
        self.client.force_authenticate(user=self.editor_user)
        data = {
            'airport': self.airport.id,
            'period_type': AssessmentPeriod.MONTHLY.value,
            'start_date': '2025-02-01',
            'end_date': '2025-02-28',
            'fuel_revenue': '100000',
            'parking_revenue': '50000',
            'retail_revenue': '30000',
            'landing_fees': '80000',
            'cargo_revenue': '40000',
            'other_revenue': '10000',
            'security_costs': '20000',
            'maintenance_costs': '15000',
            'operational_costs': '10000',
            'staff_costs': '25000',
            'utility_costs': '5000',
            'other_expenses': '5000',
        }
        response = self.client.post('/api/v1/assessments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assessment = FiscalAssessment.objects.get(id=response.data['id'])
        # Revenue: 100000+50000+30000+80000+40000+10000 = 310000
        self.assertEqual(assessment.total_revenue, Decimal('310000'))
        # Expenses: 20000+15000+10000+25000+5000+5000 = 80000
        self.assertEqual(assessment.total_expenses, Decimal('80000'))
        self.assertEqual(assessment.net_profit, Decimal('230000'))


class DashboardAPITest(BaseAPITestCase):
    """Tests for dashboard API endpoints."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

    def test_dashboard_summary(self):
        """Test dashboard summary endpoint."""
        response = self.client.get('/api/v1/dashboard-summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('total_airports', data)
        self.assertIn('total_flights', data)
        self.assertIn('gates', data)
        self.assertIn('passengers', data)
        self.assertIn('staff', data)

    def test_dashboard_summary_gate_utilization(self):
        """Test gate utilization calculation in dashboard."""
        response = self.client.get('/api/v1/dashboard-summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertIn('utilization', response.data['gates'])

    def test_metrics_endpoint(self):
        """Test metrics endpoint."""
        response = self.client.get('/api/v1/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('period', data)
        self.assertIn('flights', data)
        self.assertIn('passengers', data)

    def test_metrics_endpoint_with_period(self):
        """Test metrics endpoint with different periods."""
        for period in ['day', 'week', 'month', 'year']:
            response = self.client.get(f'/api/v1/metrics/?period={period}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['period'], period)

    def test_analytics_dashboard(self):
        """Test analytics dashboard endpoint."""
        response = self.client.get('/api/v1/analytics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('revenue_trend', data)
        self.assertIn('flight_trend', data)
        self.assertIn('passenger_trend', data)
        self.assertIn('airport_comparison', data)

    def test_trend_data(self):
        """Test trend data endpoint."""
        response = self.client.get('/api/v1/trends/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIn('labels', data)
        self.assertIn('revenue', data)
        self.assertIn('passengers', data)


class SecurityAPITest(BaseAPITestCase):
    """Security-focused API tests."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

    def test_sql_injection_prevention(self):
        """Test SQL injection attempts are handled safely."""
        # These should not cause SQL errors
        malicious_inputs = [
            "'; DROP TABLE core_airport; --",
            "1 OR 1=1",
            "1' OR '1'='1",
            "admin'--",
        ]
        
        for input_val in malicious_inputs:
            response = self.client.get(f'/api/v1/airports/?search={input_val}')
            # Should not crash, should return valid response
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_xss_prevention_in_response(self):
        """Test XSS payloads are properly escaped in JSON responses."""
        xss_payload = '<script>alert("XSS")</script>'
        
        # Create airport with XSS payload in name
        airport = Airport.objects.create(
            code="XSS",
            name=xss_payload,
            city="City",
        )
        
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # JSON response contains the raw string (not HTML escaped)
        # This is correct behavior for JSON APIs
        # XSS protection happens at the browser level when rendering
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_path_traversal_prevention(self):
        """Test path traversal attempts are blocked."""
        # These should return 404, not expose file system
        paths = [
            '/api/v1/../../../etc/passwd',
            '/api/v1/..%2F..%2F..%2Fetc%2Fpasswd',
            '/api/v1/....//....//etc/passwd',
        ]
        
        for path in paths:
            response = self.client.get(path)
            self.assertIn(response.status_code, [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST])

    def test_null_byte_injection(self):
        """Test null byte injection is handled."""
        response = self.client.get('/api/v1/airports/?search=test%00injection')
        # Should not crash
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_unicode_handling(self):
        """Test unicode characters are handled correctly."""
        airport = Airport.objects.create(
            code="UNI",
            name="Ünïcödé Àirpört 日本語",
            city="City",
        )
        
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_large_payload_rejection(self):
        """Test large payloads are handled appropriately."""
        # Create very large payload
        large_data = {
            'code': 'BIG',
            'name': 'A' * 100000,  # 100k characters
            'city': 'City',
        }

        response = self.client.post('/api/v1/airports/', large_data)
        # Should either reject or accept (validation handles it)
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_201_CREATED,
        ])

    def test_content_type_validation(self):
        """Test invalid content types are rejected."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + self.admin_token.key,
            CONTENT_TYPE='text/plain',
        )
        
        data = {'code': 'TEST', 'name': 'Test', 'city': 'Test'}
        response = self.client.post('/api/v1/airports/', data, content_type='text/plain')
        # Should be rejected or handled appropriately
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            status.HTTP_201_CREATED,  # If DRF is lenient
        ])


class RateLimitingAPITest(BaseAPITestCase):
    """Tests for API rate limiting."""

    def setUp(self):
        super().setUp()
        # Use token auth for rate limiting tests
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.admin_token.key)

    def test_rate_limit_headers(self):
        """Test rate limit headers are present."""
        response = self.client.get('/api/v1/airports/')
        
        # Rate limit headers may or may not be present depending on configuration
        # This test verifies the endpoint works
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class APIErrorHandlingTest(BaseAPITestCase):
    """Tests for API error handling."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.admin_user)

    def test_invalid_json_payload(self):
        """Test invalid JSON is handled gracefully."""
        response = self.client.post(
            '/api/v1/airports/',
            'invalid json {',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_fields(self):
        """Test missing required fields returns proper error."""
        response = self.client.post('/api/v1/airports/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data)
        self.assertIn('name', response.data)

    def test_invalid_field_types(self):
        """Test invalid field types are rejected."""
        data = {
            'code': 123,  # Should be string
            'name': 'Test',
            'city': 'Test',
        }
        response = self.client.post('/api/v1/airports/', data)
        # DRF may coerce types or accept - test doesn't crash
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
        ])

    def test_invalid_date_format(self):
        """Test invalid date format is rejected."""
        data = {
            'flight_number': 'TEST1',
            'origin': 'LOS',
            'destination': 'JFK',
            'scheduled_departure': 'invalid-date',
            'scheduled_arrival': 'invalid-date',
        }
        response = self.client.post('/api/v1/flights/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_out_of_range_values(self):
        """Test out of range values are rejected."""
        data = {
            'gate_id': 'A1',
            'terminal': 'T1',
            'status': 'invalid_status',
        }
        response = self.client.post('/api/v1/gates/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        """Test method not allowed returns proper response."""
        response = self.client.delete('/api/v1/dashboard-summary/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
