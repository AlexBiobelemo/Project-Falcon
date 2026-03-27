"""Django REST Framework API views and serializers for versioned API.

This module provides API endpoints with versioning support (/api/v1/)
using Django REST Framework for better API documentation and client support.

Honeypot Protection:
- API honeypot endpoints trap automated scanners
- Request validation middleware blocks suspicious patterns
- Rate limiting prevents API abuse
"""

import django_filters
import logging
import secrets
import hashlib
import time
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.authentication import (
    SessionAuthentication,
    TokenAuthentication,
)
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# API Schema for documentation
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from .models import (
    Airport, Gate, Flight, Passenger, Staff, StaffAssignment,
    EventLog, FiscalAssessment, Aircraft, CrewMember, MaintenanceLog, IncidentReport,
    Report, Document, AssessmentStatus,
)
from .serializers import (
    AirportSerializer, GateSerializer, FlightSerializer,
    PassengerSerializer, StaffSerializer, EventLogSerializer,
    FiscalAssessmentSerializer, DashboardSummarySerializer,
    AircraftSerializer, CrewMemberSerializer, MaintenanceLogSerializer,
    IncidentReportSerializer, ReportSerializer, DocumentSerializer
)
from .permissions import (
    AirportPermissions,
    GatePermissions,
    FlightPermissions,
    StaffPermissions,
    FiscalAssessmentPermissions,
    ReportPermissions,
    DocumentPermissions,
    MaintenanceLogPermissions,
    IncidentReportPermissions,
)

# Honeypot logger
honeypot_logger = logging.getLogger('honeypot')


# Custom authentication class for API endpoints
# Uses TokenAuthentication (CSRF exempt) + SessionAuthentication (CSRF required)
# Token auth takes precedence - if valid token, CSRF is exempt
class APITokenAuthentication(TokenAuthentication):
    """
    Token-based authentication for API endpoints.
    Provides CSRF exemption for stateless token authentication.
    """
    keyword = 'Bearer'


class AirportViewSet(viewsets.ModelViewSet):
    """API endpoint for airports."""
    
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = [AirportPermissions]
    # Use TokenAuthentication for stateless API access (CSRF exempt)
    # SessionAuthentication still available for browser clients (CSRF required)
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    search_fields = ['code', 'name', 'city']
    ordering_fields = ['code', 'name', 'city', 'created_at']
    ordering = ['code']


class GateViewSet(viewsets.ModelViewSet):
    """API endpoint for gates."""
    
    queryset = Gate.objects.all()
    serializer_class = GateSerializer
    permission_classes = [GatePermissions]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['terminal', 'status', 'capacity']
    search_fields = ['gate_id', 'terminal']
    ordering_fields = ['gate_id', 'terminal', 'status']
    ordering = ['gate_id']


class FlightViewSet(viewsets.ModelViewSet):
    """API endpoint for flights."""
    
    queryset = Flight.objects.select_related('gate').all()
    serializer_class = FlightSerializer
    permission_classes = [FlightPermissions]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['status', 'airline', 'origin', 'destination']
    search_fields = ['flight_number', 'airline', 'origin', 'destination']
    ordering_fields = ['scheduled_departure', 'scheduled_arrival', 'status']
    ordering = ['scheduled_departure']
    
    def get_queryset(self):
        """Filter flights based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(scheduled_departure__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(scheduled_departure__date__lte=date_to)
        
        # Filter by gate
        gate_id = self.request.query_params.get('gate')
        if gate_id:
            queryset = queryset.filter(gate_id=gate_id)
        
        return queryset


class PassengerViewSet(viewsets.ModelViewSet):
    """API endpoint for passengers."""
    queryset = Passenger.objects.select_related('flight', 'flight__gate').all()
    serializer_class = PassengerSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'flight']
    search_fields = ['first_name', 'last_name', 'passport_number', 'email']
    ordering_fields = ['last_name', 'first_name', 'created_at']
    ordering = ['last_name', 'first_name']


class StaffViewSet(viewsets.ModelViewSet):
    """API endpoint for staff."""
    queryset = Staff.objects.prefetch_related('assignments', 'assignments__flight').all()
    serializer_class = StaffSerializer
    permission_classes = [StaffPermissions]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['role', 'is_available']
    search_fields = ['first_name', 'last_name', 'employee_number', 'email']
    ordering_fields = ['last_name', 'first_name', 'role']
    ordering = ['last_name', 'first_name']


class StaffAssignmentViewSet(viewsets.ModelViewSet):
    """API endpoint for staff assignments."""
    
    queryset = StaffAssignment.objects.select_related('staff', 'flight', 'flight__gate').all()
    permission_classes = [IsAuthenticated]
    filterset_fields = ['staff', 'flight', 'assignment_type']
    ordering_fields = ['assigned_at']
    ordering = ['-assigned_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        from .serializers import StaffAssignmentSerializer
        return StaffAssignmentSerializer


class EventLogViewSet(viewsets.ModelViewSet):
    """API endpoint for event logs."""
    
    queryset = EventLog.objects.select_related('user', 'flight').all()
    serializer_class = EventLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['event_type', 'severity', 'flight']
    search_fields = ['event_type', 'description']
    ordering_fields = ['timestamp', 'event_type', 'severity']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Filter events based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by flight
        flight_id = self.request.query_params.get('flight')
        if flight_id:
            queryset = queryset.filter(flight_id=flight_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset


class FiscalAssessmentViewSet(viewsets.ModelViewSet):
    """API endpoint for fiscal assessments.
    
    SECURITY: This endpoint enforces strict role-based access control.
    - DELETE operations require admin (superuser) privileges
    - CREATE/UPDATE operations require editor role
    - READ operations are allowed for any authenticated user
    """
    
    queryset = FiscalAssessment.objects.select_related('airport').all()
    serializer_class = FiscalAssessmentSerializer
    permission_classes = [FiscalAssessmentPermissions]
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ['status', 'period_type', 'airport']
    ordering_fields = ['start_date', 'end_date', 'status']
    ordering = ['-start_date']
    
    def get_queryset(self):
        """Filter assessments based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by airport
        airport_code = self.request.query_params.get('airport_code')
        if airport_code:
            queryset = queryset.filter(airport__code=airport_code)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
        
        return queryset


class AircraftViewSet(viewsets.ModelViewSet):
    """API endpoint for aircraft."""
    
    queryset = Aircraft.objects.all()
    serializer_class = AircraftSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['aircraft_type', 'status', 'manufacturer']
    search_fields = ['tail_number', 'model', 'manufacturer', 'registration_country']
    ordering_fields = ['tail_number', 'model', 'manufacturer', 'status']
    ordering = ['tail_number']


class CrewMemberViewSet(viewsets.ModelViewSet):
    """API endpoint for crew members."""
    
    queryset = CrewMember.objects.select_related('base_airport').all()
    serializer_class = CrewMemberSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['crew_type', 'status', 'base_airport']
    search_fields = ['first_name', 'last_name', 'employee_id', 'license_number', 'email']
    ordering_fields = ['last_name', 'first_name', 'crew_type', 'status']
    ordering = ['last_name', 'first_name']


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    """API endpoint for maintenance logs."""
    
    queryset = MaintenanceLog.objects.select_related('performed_by').all()
    serializer_class = MaintenanceLogSerializer
    permission_classes = [MaintenanceLogPermissions]
    filterset_fields = ['equipment_type', 'maintenance_type', 'status']
    ordering_fields = ['started_at', 'status', 'cost']
    ordering = ['-started_at']
    
    def get_queryset(self):
        """Filter maintenance logs based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by equipment
        equipment_id = self.request.query_params.get('equipment_id')
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(started_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(started_at__date__lte=date_to)
        
        return queryset


class IncidentReportViewSet(viewsets.ModelViewSet):
    """API endpoint for incident reports."""
    
    queryset = IncidentReport.objects.select_related(
        'reported_by', 'assigned_to', 'related_flight', 'related_gate'
    ).all()
    serializer_class = IncidentReportSerializer
    permission_classes = [IncidentReportPermissions]
    filterset_fields = ['incident_type', 'severity', 'status']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date_occurred', 'date_reported', 'severity', 'status']
    ordering = ['-date_occurred']
    
    def get_queryset(self):
        """Filter incident reports based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by flight
        flight_id = self.request.query_params.get('flight')
        if flight_id:
            queryset = queryset.filter(related_flight_id=flight_id)
        
        # Filter by gate
        gate_id = self.request.query_params.get('gate')
        if gate_id:
            queryset = queryset.filter(related_gate_id=gate_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date_occurred__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_occurred__date__lte=date_to)
        
        return queryset


class ReportViewSet(viewsets.ModelViewSet):
    """API endpoint for reports."""
    
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['report_type', 'airport', 'is_generated']
    
    def get_queryset(self):
        return Report.objects.select_related('airport').all()


class DocumentViewSet(viewsets.ModelViewSet):
    """API endpoint for documents."""
    
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['document_type']
    
    def get_queryset(self):
        return Document.objects.select_related('airport', 'fiscal_assessment', 'report').all()


class DashboardSummaryView(APIView):
    """API endpoint for dashboard summary data.
    
    Provides aggregated metrics for the dashboard including
    flight counts, gate utilization, and recent events.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard summary data."""
        now = timezone.now()
        today = now.date()
        
        # Optimized: Single query for flight status counts
        flight_stats = Flight.objects.aggregate(
            total=Count('id'),
            today=Count('id', filter=Q(scheduled_departure__date=today)),
            active=Count('id', filter=Q(status__in=['scheduled', 'boarding', 'departed'])),
            delayed=Count('id', filter=Q(status='delayed'))
        )
        
        # Optimized: Single query for gate status counts
        gate_stats = Gate.objects.aggregate(
            total=Count('id'),
            available=Count('id', filter=Q(status='available')),
            occupied=Count('id', filter=Q(status='occupied')),
            maintenance=Count('id', filter=Q(status='maintenance'))
        )
        
        total_gates = gate_stats['total']
        available_gates = gate_stats['available']
        gate_utilization = ((total_gates - available_gates) / total_gates * 100) if total_gates > 0 else 0
        
        # Optimized: select_related/prefetch_related for recent items
        recent_events = EventLog.objects.select_related('user', 'flight').order_by('-timestamp')[:10]
        
        # Upcoming flights (next 2 hours)
        upcoming_cutoff = now + timedelta(hours=2)
        upcoming_flights = Flight.objects.filter(
            scheduled_departure__gte=now,
            scheduled_departure__lte=upcoming_cutoff,
            status__in=['scheduled', 'boarding']
        ).select_related('gate').order_by('scheduled_departure')[:10]
        
        data = {
            'total_airports': Airport.objects.count(),
            'total_flights': flight_stats['total'],
            'flights': {
                'total': flight_stats['total'],
                'today': flight_stats['today'],
                'active': flight_stats['active'],
                'delayed': flight_stats['delayed'],
                'by_status': list(Flight.objects.values('status').annotate(count=Count('id'))),
            },
            'gates': {
                'total': total_gates,
                'available': available_gates,
                'occupied': gate_stats['occupied'],
                'maintenance': gate_stats['maintenance'],
                'utilization': round(gate_utilization, 2),
            },
            'passengers': {
                'total': Passenger.objects.count(),
            },
            'staff': {
                'total': Staff.objects.count(),
                'available': Staff.objects.filter(is_available=True).count(),
                'by_role': list(Staff.objects.values('role').annotate(count=Count('id'))),
            },
            'airports': {
                'total': Airport.objects.count(),
                'active': Airport.objects.filter(is_active=True).count(),
            },
            'upcoming_flights': FlightSerializer(upcoming_flights, many=True).data,
            'recent_events': EventLogSerializer(recent_events, many=True).data,
        }
        
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)


class TrendDataAPIView(APIView):
    """API endpoint for dashboard trend data (for Chart.js)."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get trend data for revenue and passenger counts."""
        # Get last 6 months of data
        six_months_ago = timezone.now().date() - timedelta(days=180)
        
        assessments = FiscalAssessment.objects.select_related('airport').filter(
            start_date__gte=six_months_ago
        ).order_by('start_date')
        
        labels = []
        revenue_data = []
        passenger_data = []
        
        for a in assessments:
            labels.append(f"{a.airport.code} ({a.start_date.strftime('%b %Y')})")
            revenue_data.append(float(a.total_revenue))
            passenger_data.append(a.passenger_count)
            
        return Response({
            "labels": labels,
            "revenue": revenue_data,
            "passengers": passenger_data,
        })


class MetricsView(APIView):
    """API endpoint for operational metrics.
    
    Provides detailed operational metrics including on-time performance,
    passenger counts, and revenue data.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get operational metrics."""
        # Time period
        period = request.query_params.get('period', 'day')
        
        if period == 'day':
            cutoff = timezone.now() - timedelta(days=1)
        elif period == 'week':
            cutoff = timezone.now() - timedelta(weeks=1)
        elif period == 'month':
            cutoff = timezone.now() - timedelta(days=30)
        elif period == 'year':
            cutoff = timezone.now() - timedelta(days=365)
        else:
            cutoff = timezone.now() - timedelta(days=1)
        
        # Flight metrics
        flights_total = Flight.objects.filter(scheduled_departure__gte=cutoff).count()
        flights_on_time = Flight.objects.filter(
            scheduled_departure__gte=cutoff,
            status__in=['departed', 'arrived'],
            delay_minutes__lte=15
        ).count()
        
        on_time_rate = (flights_on_time / flights_total * 100) if flights_total > 0 else 0
        
        # Average delay
        avg_delay = Flight.objects.filter(
            scheduled_departure__gte=cutoff,
            delay_minutes__gt=0
        ).aggregate(Avg('delay_minutes'))['delay_minutes__avg'] or 0
        
        # Passenger metrics
        passengers_total = Passenger.objects.filter(created_at__gte=cutoff).count()
        
        data = {
            'period': period,
            'flights': {
                'total': flights_total,
                'on_time': flights_on_time,
                'on_time_rate': round(on_time_rate, 2),
                'average_delay_minutes': round(avg_delay, 2),
            },
            'passengers': {
                'total': passengers_total,
            },
        }
        
        return Response(data)


class AnalyticsDashboardView(APIView):
    """API endpoint for advanced analytics dashboard.

    Provides comprehensive analytics data including trends,
    comparisons, and detailed metrics for Chart.js visualization.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get analytics dashboard data."""
        from django.db.models import Avg, Sum, Count, Max, Min
        from django.db.models.functions import TruncMonth, TruncWeek
        from datetime import date

        # Optional explicit date range (like Airport Comparison)
        start_date_str = request.query_params.get('start_date', '') or ''
        end_date_str = request.query_params.get('end_date', '') or ''

        now = timezone.now()
        end_dt = None
        if start_date_str:
            try:
                start_dt = timezone.make_aware(date.fromisoformat(start_date_str))
            except ValueError:
                start_dt = now - timedelta(days=180)
            if end_date_str:
                try:
                    end_dt = timezone.make_aware(date.fromisoformat(end_date_str))
                except ValueError:
                    end_dt = now
            else:
                end_dt = now

            date_cutoff = start_dt
            # Choose aggregation resolution based on range length
            days = max(1, (end_dt.date() - date_cutoff.date()).days)
            trunc_func = TruncWeek if days <= 60 else TruncMonth
            range_param = 'custom'
        else:
            # Time range parameter
            range_param = request.query_params.get('range', '6months')

            if range_param == '30days':
                date_cutoff = now - timedelta(days=30)
                trunc_func = TruncWeek
            elif range_param == '1year':
                date_cutoff = now - timedelta(days=365)
                trunc_func = TruncMonth
            else:  # 6months default
                date_cutoff = now - timedelta(days=180)
                trunc_func = TruncMonth

        # Revenue trend by period
        revenue_filters = Q(
            start_date__gte=date_cutoff,
            status=AssessmentStatus.APPROVED.value
        )
        if end_dt:
            revenue_filters &= Q(start_date__lte=end_dt)

        revenue_trend = FiscalAssessment.objects.filter(
            revenue_filters
        ).annotate(
            period=trunc_func('start_date')
        ).values('period').annotate(
            total_revenue=Sum('total_revenue'),
            total_expenses=Sum('total_expenses'),
            net_profit=Sum('net_profit'),
            assessment_count=Count('id')
        ).order_by('period')

        # Flight trend
        flight_filters = Q(scheduled_departure__gte=date_cutoff)
        if end_dt:
            flight_filters &= Q(scheduled_departure__lte=end_dt)

        # When filtering flights via Gate -> flights relation, qualify field names.
        gate_flight_filters = Q(flights__scheduled_departure__gte=date_cutoff)
        if end_dt:
            gate_flight_filters &= Q(flights__scheduled_departure__lte=end_dt)

        flight_trend = Flight.objects.filter(flight_filters).annotate(
            period=trunc_func('scheduled_departure')
        ).values('period').annotate(
            total_flights=Count('id'),
            delayed_flights=Count('id', filter=Q(status='delayed')),
            cancelled_flights=Count('id', filter=Q(status='cancelled')),
            avg_delay=Avg('delay_minutes')
        ).order_by('period')

        # Passenger trend
        passenger_filters = Q(created_at__gte=date_cutoff)
        if end_dt:
            passenger_filters &= Q(created_at__lte=end_dt)

        passenger_trend = Passenger.objects.filter(passenger_filters).annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            total_passengers=Count('id'),
            boarded=Count('id', filter=Q(status='boarded')),
            checked_in=Count('id', filter=Q(status='checked_in')),
            no_show=Count('id', filter=Q(status='no_show'))
        ).order_by('period')

        # Airport comparison
        assessment_date_filter = Q(fiscal_assessments__status=AssessmentStatus.APPROVED.value) & Q(fiscal_assessments__start_date__gte=date_cutoff)
        if end_dt:
            assessment_date_filter &= Q(fiscal_assessments__start_date__lte=end_dt)

        airport_comparison = Airport.objects.filter(is_active=True).annotate(
            total_assessments=Count('fiscal_assessments', filter=assessment_date_filter),
            total_revenue=Sum('fiscal_assessments__total_revenue', filter=assessment_date_filter),
            total_flights=Sum('fiscal_assessments__flight_count', filter=assessment_date_filter),
            avg_profit=Avg('fiscal_assessments__net_profit', filter=assessment_date_filter)
        ).order_by('-total_revenue').values('code', 'total_assessments', 'total_revenue', 'total_flights', 'avg_profit')

        # Gate utilization
        gate_utilization = Gate.objects.all().annotate(
            flight_count=Count('flights', filter=gate_flight_filters)
        ).values('gate_id', 'terminal', 'flight_count').order_by('-flight_count')

        # Status distribution
        flight_status_dist = Flight.objects.all().values('status').annotate(
            count=Count('id')
        ).order_by('-count')

        # Build response
        return Response({
            'range': range_param,
            'start_date': start_date_str or None,
            'end_date': end_date_str or None,
            'revenue_trend': {
                'labels': [item['period'].strftime('%b %Y') for item in revenue_trend],
                'revenue': [float(item['total_revenue'] or 0) for item in revenue_trend],
                'expenses': [float(item['total_expenses'] or 0) for item in revenue_trend],
                'profit': [float(item['net_profit'] or 0) for item in revenue_trend],
            },
            'flight_trend': {
                'labels': [item['period'].strftime('%b %Y') for item in flight_trend],
                'total': [item['total_flights'] or 0 for item in flight_trend],
                'delayed': [item['delayed_flights'] or 0 for item in flight_trend],
                'cancelled': [item['cancelled_flights'] or 0 for item in flight_trend],
                'avg_delay': [round(item['avg_delay'] or 0, 2) for item in flight_trend],
            },
            'passenger_trend': {
                'labels': [item['period'].strftime('%b %Y') for item in passenger_trend],
                'total': [item['total_passengers'] or 0 for item in passenger_trend],
                'boarded': [item['boarded'] or 0 for item in passenger_trend],
                'checked_in': [item['checked_in'] or 0 for item in passenger_trend],
            },
            'airport_comparison': {
                'labels': [item['code'] for item in airport_comparison],
                'revenue': [float(item['total_revenue'] or 0) for item in airport_comparison],
                'assessments': [item['total_assessments'] or 0 for item in airport_comparison],
                'flights': [item['total_flights'] or 0 for item in airport_comparison],
            },
            'gate_utilization': {
                'labels': [f"{item['gate_id']} ({item['terminal']})" for item in gate_utilization[:10]],
                'flights': [item['flight_count'] or 0 for item in gate_utilization[:10]],
            },
            'status_distribution': {
                'labels': [item['status'] for item in flight_status_dist],
                'counts': [item['count'] for item in flight_status_dist],
            },
            'summary': {
                'total_airports': Airport.objects.filter(is_active=True).count(),
                'total_gates': Gate.objects.count(),
                'total_flights': Flight.objects.count(),
                'total_passengers': Passenger.objects.count(),
                'approved_assessments': FiscalAssessment.objects.filter(status=AssessmentStatus.APPROVED.value).count(),
            }
        })


class TrendDataAPIView(APIView):
    """API endpoint for trend data for Chart.js visualizations.

    Provides 6-month historical data for revenue and passenger counts.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get trend data."""
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncMonth

        # Get last 6 months of data
        six_months_ago = timezone.now() - timedelta(days=180)

        # Revenue trend
        revenue_data = FiscalAssessment.objects.filter(
            start_date__gte=six_months_ago,
            status=AssessmentStatus.APPROVED.value
        ).annotate(
            month=TruncMonth('start_date')
        ).values('month').annotate(
            total_revenue=Sum('total_revenue'),
            total_expenses=Sum('total_expenses')
        ).order_by('month')

        # Passenger trend
        passenger_data = FiscalAssessment.objects.filter(
            start_date__gte=six_months_ago,
            status=AssessmentStatus.APPROVED.value
        ).annotate(
            month=TruncMonth('start_date')
        ).values('month').annotate(
            total_passengers=Sum('passenger_count')
        ).order_by('month')

        # Build chart-ready data
        labels = []
        revenue_values = []
        expense_values = []
        passenger_values = []

        for item in revenue_data:
            labels.append(item['month'].strftime('%b %Y'))
            revenue_values.append(float(item['total_revenue'] or 0))
            expense_values.append(float(item['total_expenses'] or 0))

        for item in passenger_data:
            passenger_values.append(item['total_passengers'] or 0)

        return Response({
            'labels': labels,
            'revenue': revenue_values,
            'expenses': expense_values,
            'passengers': passenger_values,
        })


class UserPreferencesView(APIView):
    """API endpoint for user preferences including theme.
    
    Allows users to save and retrieve their preferences.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user preferences."""
        user = request.user
        
        # Get preferences from user profile or session
        preferences = {
            'theme_preference': getattr(user, 'theme_preference', 'dark'),
            'notifications_enabled': getattr(user, 'notifications_enabled', True),
        }
        
        return Response(preferences)
    
    def patch(self, request):
        """Update user preferences."""
        user = request.user
        data = request.data
        
        # Update theme preference
        if 'theme_preference' in data:
            # Store in session for now (could be extended to user profile)
            request.session['theme_preference'] = data['theme_preference']
        
        if 'notifications_enabled' in data:
            request.session['notifications_enabled'] = data['notifications_enabled']
        
        return Response({'status': 'success', 'message': 'Preferences updated'})


# HONEYPOT API ENDPOINTS
# These are decoy endpoints designed to trap and confuse automated scanners.
# They return misleading responses and log all access for security analysis.


def get_client_ip(request):
    """Get client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def log_honeypot_access(request, endpoint_type):
    """Log honeypot endpoint access."""
    ip = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
    method = request.method
    
    honeypot_logger.critical(
        f"API HONEYPOT TRIGGERED | Type: {endpoint_type} | "
        f"IP: {ip} | Method: {method} | "
        f"User-Agent: {user_agent} | Path: {request.path}"
    )


def get_random_response():
    """Generate a random fake response to confuse attackers."""
    import random
    
    fake_responses = [
        {"status": "error", "message": "Resource not found", "code": 404},
        {"error": "Access denied", "reason": "Insufficient permissions"},
        {"result": None, "success": False, "error": "Invalid request"},
    ]
    
    return random.choice(fake_responses)


@csrf_exempt
def honeypot_backup_endpoint(request):
    """
    Honeypot endpoint mimicking a backup file endpoint.
    
    Traps scanners looking for exposed backup files.
    Returns misleading 404 response while logging the attempt.
    """
    log_honeypot_access(request, 'backup')
    return JsonResponse(
        {"error": "Backup not found"},
        status=404
    )


@csrf_exempt
def honeypot_debug_endpoint(request):
    """
    Honeypot endpoint mimicking a debug interface.
    
    Traps scanners looking for debug endpoints.
    Returns misleading response while logging the attempt.
    """
    log_honeypot_access(request, 'debug')
    
    # Return different responses based on method
    if request.method == 'GET':
        return JsonResponse(
            {"debug": "disabled", "mode": "production"},
            status=403
        )
    else:
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405
        )


@csrf_exempt
def honeypot_admin_endpoint(request):
    """
    Honeypot endpoint mimicking an admin configuration panel.
    
    Traps privilege escalation attempts.
    Returns misleading response while logging the attempt.
    """
    log_honeypot_access(request, 'admin-config')
    
    # Return fake admin interface info
    return JsonResponse(
        {
            "admin": "unavailable",
            "configuration": "locked",
            "access_level": "denied"
        },
        status=401
    )


@csrf_exempt
def honeypot_internal_endpoint(request):
    """
    Honeypot endpoint mimicking an internal user API.
    
    Traps reconnaissance attempts for internal APIs.
    Returns misleading response while logging the attempt.
    """
    log_honeypot_access(request, 'internal-users')
    
    return JsonResponse(
        {
            "users": [],
            "count": 0,
            "error": "Internal API access denied"
        },
        status=403
    )


@csrf_exempt
def honeypot_database_endpoint(request):
    """
    Honeypot endpoint mimicking a database interface.
    
    Traps attempts to access database directly.
    Returns misleading response while logging the attempt.
    """
    log_honeypot_access(request, 'database')
    
    return JsonResponse(
        {
            "database": "connected",
            "tables": 0,
            "error": "Query execution failed"
        },
        status=500
    )


@csrf_exempt
def honeypot_status_endpoint(request):
    """
    Honeypot status endpoint.

    Returns basic honeypot system status.
    This endpoint is intentionally non-obvious to confuse scanners.
    """
    log_honeypot_access(request, 'status')

    # Return minimal info
    return JsonResponse({
        "status": "ok",
        "version": "1.0.0"
    })


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def map_data_view(request):
    """
    API endpoint for fetching live map data.
    
    Returns current flight positions, airport locations, and gate status
    for the interactive dashboard map.
    """
    from .map_service import map_service
    
    # Get optional airport filter
    airport_code = request.GET.get('airport', None)
    
    # Fetch map data
    flights = map_service.get_active_flights(airport_code)
    gates = map_service.get_gates_data()
    airports = map_service.get_airports_data()
    
    return Response({
        'flights': flights,
        'gates': gates,
        'airports': airports,
        'timestamp': timezone.now().isoformat(),
    })


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def weather_search_view(request):
    """
    API endpoint for searching weather locations.
    
    Returns matching locations for weather lookup.
    """
    from .weather_service import weather_service
    
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response({'error': 'Search query must be at least 2 characters'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    locations = weather_service.search_locations(query)
    
    return Response({
        'locations': locations,
        'count': len(locations),
    })


@api_view(['GET'])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def weather_location_view(request):
    """
    API endpoint for fetching weather by coordinates.
    
    Returns weather data for specified location.
    """
    from .weather_service import weather_service
    
    try:
        latitude = float(request.GET.get('lat', 0))
        longitude = float(request.GET.get('lng', 0))
        location_name = request.GET.get('name', 'Location')
    except (ValueError, TypeError):
        return Response({'error': 'Invalid coordinates'},
                       status=status.HTTP_400_BAD_REQUEST)

    weather = weather_service.get_weather_by_coordinates(latitude, longitude, location_name)

    return Response(weather)
