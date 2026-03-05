"""Django REST Framework serializers for API endpoints.

This module provides serializers for all models to convert them to/from
JSON for API responses using Django REST Framework.
"""

from rest_framework import serializers
from .models import (
    Airport, Gate, Flight, Passenger, Staff, StaffAssignment,
    EventLog, FiscalAssessment, Aircraft, CrewMember, MaintenanceLog, IncidentReport,
    Report, Document
)



# MIXINS - Reusable serializer components to reduce duplication

class AuditFieldsSerializerMixin(serializers.ModelSerializer):
    """Mixin that adds standard audit fields to serializers.
    
    Usage:
        class MyModelSerializer(AuditFieldsSerializerMixin):
            class Meta:
                model = MyModel
                fields = ['id', 'name', 'created_at', 'updated_at']
    
    This mixin adds the following read-only fields:
    - created_at: Timestamp when the record was created
    - updated_at: Timestamp when the record was last updated
    """
    
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class UserAuditFieldsSerializerMixin(AuditFieldsSerializerMixin):
    """Mixin that adds audit fields including user tracking.
    
    Usage:
        class MyModelSerializer(UserAuditFieldsSerializerMixin):
            class Meta:
                model = MyModel
                fields = ['id', 'name', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    Extends AuditFieldsSerializerMixin with:
    - created_by: User who created the record
    - updated_by: User who last updated the record
    """
    
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)


class AirportSerializer(serializers.ModelSerializer):
    """Serializer for Airport model."""
    
    class Meta:
        model = Airport
        fields = [
            'id', 'code', 'name', 'city', 'timezone',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GateSerializer(AuditFieldsSerializerMixin, serializers.ModelSerializer):
    """Serializer for Gate model."""
    
    class Meta:
        model = Gate
        fields = [
            'id', 'gate_id', 'terminal', 'capacity', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FlightSerializer(serializers.ModelSerializer):
    """Serializer for Flight model."""
    
    gate_details = GateSerializer(source='gate', read_only=True)
    gate = serializers.PrimaryKeyRelatedField(queryset=Gate.objects.all(), required=False, allow_null=True)
    passengers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Flight
        fields = [
            'id', 'flight_number', 'airline', 'origin', 'destination',
            'scheduled_departure', 'actual_departure',
            'scheduled_arrival', 'actual_arrival',
            'gate', 'gate_details', 'status', 'delay_minutes',
            'aircraft_type', 'passengers_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_passengers_count(self, obj):
        """Get the number of passengers for this flight."""
        return obj.passengers.count() if hasattr(obj, 'passengers') else 0
    
    def to_representation(self, instance):
        """Customize representation to handle nullable fields."""
        # Handle both dict (already serialized) and model instances
        if isinstance(instance, dict):
            return instance
        
        data = super().to_representation(instance)
        
        # Format datetime fields
        if data.get('scheduled_departure'):
            data['scheduled_departure'] = instance.scheduled_departure.isoformat()
        if data.get('actual_departure'):
            data['actual_departure'] = instance.actual_departure.isoformat()
        if data.get('scheduled_arrival'):
            data['scheduled_arrival'] = instance.scheduled_arrival.isoformat()
        if data.get('actual_arrival'):
            data['actual_arrival'] = instance.actual_arrival.isoformat()
        
        return data


class PassengerSerializer(serializers.ModelSerializer):
    """Serializer for Passenger model."""
    
    flight_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Passenger
        fields = [
            'id', 'passenger_id', 'first_name', 'last_name',
            'passport_number', 'email', 'phone',
            'flight', 'flight_details', 'seat_number', 'status',
            'checked_bags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'passenger_id', 'created_at', 'updated_at']
    
    def get_flight_details(self, obj):
        """Get flight details for the passenger."""
        if obj.flight:
            return {
                'flight_number': obj.flight.flight_number,
                'origin': obj.flight.origin,
                'destination': obj.flight.destination,
                'scheduled_departure': obj.flight.scheduled_departure.isoformat() if obj.flight.scheduled_departure else None,
            }
        return None


class StaffSerializer(serializers.ModelSerializer):
    """Serializer for Staff model."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = [
            'id', 'staff_id', 'full_name', 'first_name', 'last_name',
            'employee_number', 'role', 'certification',
            'is_available', 'phone', 'email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'staff_id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        """Get full name of the staff member."""
        return f"{obj.first_name} {obj.last_name}"


class StaffAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for StaffAssignment model."""
    
    staff_details = StaffSerializer(source='staff', read_only=True)
    flight_details = FlightSerializer(source='flight', read_only=True)
    staff = serializers.PrimaryKeyRelatedField(queryset=Staff.objects.all(), required=True)
    flight = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all(), required=True)
    
    class Meta:
        model = StaffAssignment
        fields = [
            'id', 'staff', 'staff_details', 'flight', 'flight_details',
            'assignment_type', 'assigned_at'
        ]
        read_only_fields = ['id', 'assigned_at']


class EventLogSerializer(serializers.ModelSerializer):
    """Serializer for EventLog model."""
    
    flight_details = serializers.SerializerMethodField()
    
    class Meta:
        model = EventLog
        fields = [
            'id', 'event_id', 'timestamp', 'event_type', 'description',
            'flight', 'flight_details', 'severity', 'created_at'
        ]
        read_only_fields = ['id', 'event_id', 'created_at']
    
    def get_flight_details(self, obj):
        """Get flight details if associated."""
        if obj.flight:
            return {
                'flight_number': obj.flight.flight_number,
                'origin': obj.flight.origin,
                'destination': obj.flight.destination,
            }
        return None
    
    def to_representation(self, instance):
        """Customize representation to handle datetime fields."""
        data = super().to_representation(instance)
        
        if data.get('timestamp'):
            data['timestamp'] = instance.timestamp.isoformat()
        
        return data


class FiscalAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for FiscalAssessment model."""
    
    airport_details = AirportSerializer(source='airport', read_only=True)
    airport = serializers.PrimaryKeyRelatedField(queryset=Airport.objects.all(), required=True)
    
    class Meta:
        model = FiscalAssessment
        fields = [
            'id', 'airport', 'airport_details', 'period_type',
            'start_date', 'end_date', 'status',
            'total_revenue', 'total_expenses', 'net_profit',
            'passenger_count', 'flight_count',
            'fuel_revenue', 'parking_revenue', 'retail_revenue',
            'landing_fees', 'cargo_revenue', 'other_revenue',
            'security_costs', 'maintenance_costs', 'operational_costs',
            'staff_costs', 'utility_costs', 'other_expenses',
            'assessment_notes', 'assessed_by', 'approved_by', 'approved_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Customize representation to handle datetime fields."""
        data = super().to_representation(instance)
        
        if data.get('start_date'):
            data['start_date'] = instance.start_date.isoformat()
        if data.get('end_date'):
            data['end_date'] = instance.end_date.isoformat()
        if data.get('approved_at'):
            data['approved_at'] = instance.approved_at.isoformat()
        
        return data
    
    def create(self, validated_data):
        """Override create to calculate totals."""
        instance = super().create(validated_data)
        instance.calculate_totals()
        return instance
    
    def update(self, instance, validated_data):
        """Override update to recalculate totals."""
        instance = super().update(instance, validated_data)
        instance.calculate_totals()
        return instance


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary data."""
    
    total_airports = serializers.IntegerField()
    total_flights = serializers.IntegerField()
    flights = serializers.DictField()
    gates = serializers.DictField()
    passengers = serializers.DictField()
    staff = serializers.DictField()
    airports = serializers.DictField()
    upcoming_flights = FlightSerializer(many=True)
    recent_events = EventLogSerializer(many=True)


from .models import Aircraft, CrewMember, MaintenanceLog, IncidentReport


class AircraftSerializer(serializers.ModelSerializer):
    """Serializer for Aircraft model."""
    
    class Meta:
        model = Aircraft
        fields = [
            'id', 'tail_number', 'aircraft_type', 'model', 'manufacturer',
            'capacity_passengers', 'capacity_cargo', 'status',
            'registration_country', 'year_manufactured',
            'last_maintenance_date', 'next_maintenance_due',
            'total_flight_hours', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CrewMemberSerializer(serializers.ModelSerializer):
    """Serializer for CrewMember model."""
    
    full_name = serializers.SerializerMethodField()
    base_airport_details = AirportSerializer(source='base_airport', read_only=True)
    base_airport = serializers.PrimaryKeyRelatedField(queryset=Airport.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = CrewMember
        fields = [
            'id', 'employee_id', 'full_name', 'first_name', 'last_name',
            'crew_type', 'license_number', 'license_expiry', 'status',
            'total_flight_hours', 'rank', 'base_airport', 'base_airport_details',
            'email', 'phone', 'hire_date', 'date_of_birth',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        """Get full name of the crew member."""
        return f"{obj.first_name} {obj.last_name}"


class MaintenanceLogSerializer(serializers.ModelSerializer):
    """Serializer for MaintenanceLog model."""
    
    performed_by_details = StaffSerializer(source='performed_by', read_only=True)
    performed_by = serializers.PrimaryKeyRelatedField(queryset=Staff.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = MaintenanceLog
        fields = [
            'id', 'equipment_type', 'equipment_id', 'maintenance_type',
            'description', 'status', 'started_at', 'completed_at',
            'performed_by', 'performed_by_details', 'parts_replaced',
            'cost', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Customize representation to handle datetime fields."""
        data = super().to_representation(instance)
        
        if data.get('started_at'):
            data['started_at'] = instance.started_at.isoformat()
        if data.get('completed_at'):
            data['completed_at'] = instance.completed_at.isoformat()
        
        return data


class IncidentReportSerializer(serializers.ModelSerializer):
    """Serializer for IncidentReport model."""
    
    reported_by_details = StaffSerializer(source='reported_by', read_only=True)
    assigned_to_details = StaffSerializer(source='assigned_to', read_only=True)
    related_flight_details = FlightSerializer(source='related_flight', read_only=True)
    related_gate_details = GateSerializer(source='related_gate', read_only=True)
    
    reported_by = serializers.PrimaryKeyRelatedField(queryset=Staff.objects.all(), required=False, allow_null=True)
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=Staff.objects.all(), required=False, allow_null=True)
    related_flight = serializers.PrimaryKeyRelatedField(queryset=Flight.objects.all(), required=False, allow_null=True)
    related_gate = serializers.PrimaryKeyRelatedField(queryset=Gate.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = IncidentReport
        fields = [
            'id', 'incident_id', 'incident_type', 'severity', 'status',
            'title', 'description', 'location',
            'reported_by', 'reported_by_details',
            'assigned_to', 'assigned_to_details',
            'date_occurred', 'date_reported', 'date_resolved',
            'root_cause', 'corrective_action',
            'related_flight', 'related_flight_details',
            'related_gate', 'related_gate_details',
            'attachments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'incident_id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Customize representation to handle datetime fields."""
        data = super().to_representation(instance)
        
        if data.get('date_occurred'):
            data['date_occurred'] = instance.date_occurred.isoformat()
        if data.get('date_reported'):
            data['date_reported'] = instance.date_reported.isoformat()
        if data.get('date_resolved'):
            data['date_resolved'] = instance.date_resolved.isoformat()
        
        return data


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for Report model."""
    
    airport_details = AirportSerializer(source='airport', read_only=True)
    airport = serializers.PrimaryKeyRelatedField(queryset=Airport.objects.all(), required=True)
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_id', 'airport', 'airport_details', 'report_type',
            'title', 'description', 'period_start', 'period_end',
            'format', 'file_path', 'content', 'generated_by',
            'is_generated', 'generated_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'report_id', 'file_path', 'generated_at', 'created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model."""
    
    class Meta:
        model = Document
        fields = [
            'id', 'document_id', 'name', 'document_type', 'file',
            'content', 'status', 'uploaded_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'document_id', 'created_at', 'updated_at']
