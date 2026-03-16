"""Django Forms for input validation in the Airport Operations Management System.

This module provides form classes for validating POST data in views,
preventing mass assignment and ensuring proper type validation.

Rules compliance: PEP8, type hints, docstrings.
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Airport, FiscalAssessment, AssessmentPeriod, AssessmentStatus, ReportType, ReportFormat, Document, ReportSchedule
from .honeypot import HoneypotFieldMixin


# Fields allowed for mass assignment - explicit allowlist for security
FISCAL_ASSESSMENT_CREATE_FIELDS: List[str] = [
    'airport',
    'period_type',
    'start_date',
    'end_date',
    'status',
    'fuel_revenue',
    'parking_revenue',
    'retail_revenue',
    'landing_fees',
    'cargo_revenue',
    'other_revenue',
    'security_costs',
    'maintenance_costs',
    'operational_costs',
    'staff_costs',
    'utility_costs',
    'other_expenses',
    'passenger_count',
    'flight_count',
    'assessment_notes',
    'assessed_by',
]

FISCAL_ASSESSMENT_UPDATE_FIELDS: List[str] = [
    'airport',
    'period_type',
    'start_date',
    'end_date',
    'status',
    'fuel_revenue',
    'parking_revenue',
    'retail_revenue',
    'landing_fees',
    'cargo_revenue',
    'other_revenue',
    'security_costs',
    'maintenance_costs',
    'operational_costs',
    'staff_costs',
    'utility_costs',
    'other_expenses',
    'passenger_count',
    'flight_count',
    'assessment_notes',
    'assessed_by',
]


def validate_positive_decimal(value: Any) -> Decimal:
    """Validate that a value can be converted to a positive Decimal.
    
    Args:
        value: The value to validate.
        
    Returns:
        Decimal value.
        
    Raises:
        ValidationError: If value cannot be converted or is negative.
    """
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError('Must be a valid number.')
    
    if decimal_value < 0:
        raise ValidationError('Value cannot be negative.')
    
    return decimal_value


def validate_positive_integer(value: Any) -> int:
    """Validate that a value can be converted to a positive integer.
    
    Args:
        value: The value to validate.
        
    Returns:
        Integer value.
        
    Raises:
        ValidationError: If value cannot be converted or is negative.
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError('Must be a valid integer.')
    
    if int_value < 0:
        raise ValidationError('Value cannot be negative.')
    
    return int_value


class FiscalAssessmentCreateForm(HoneypotFieldMixin, forms.Form):
    """Form for creating a new FiscalAssessment with proper validation.
    
    This form provides proper type validation for all POST data,
    addressing vulnerability #6 (Missing Input Validation).
    """
    
    # Required fields
    airport = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_active=True),
        required=True,
        error_messages={'required': 'Airport is required.'}
    )
    period_type = forms.ChoiceField(
        choices=[(p.value, p.name) for p in AssessmentPeriod],
        required=True,
        error_messages={'required': 'Period type is required.'}
    )
    start_date = forms.DateField(
        required=True,
        error_messages={'required': 'Start date is required.', 'invalid': 'Invalid date format.'}
    )
    end_date = forms.DateField(
        required=True,
        error_messages={'required': 'End date is required.', 'invalid': 'Invalid date format.'}
    )
    
    # Optional status (defaults to DRAFT)
    status = forms.ChoiceField(
        choices=[(s.value, s.name) for s in AssessmentStatus],
        required=False,
        initial=AssessmentStatus.DRAFT.value
    )
    
    # Financial fields - validated as positive decimals
    fuel_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    parking_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    retail_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    landing_fees = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    cargo_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    other_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    
    # Expense fields - validated as positive decimals
    security_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    maintenance_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    operational_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    staff_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    utility_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    other_expenses = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False,
        min_value=0, initial=0
    )
    
    # Operational metrics - validated as positive integers
    passenger_count = forms.IntegerField(
        required=False, min_value=0, initial=0
    )
    flight_count = forms.IntegerField(
        required=False, min_value=0, initial=0
    )
    
    # Additional fields
    assessment_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'rows': 3}),
        max_length=2000
    )
    assessed_by = forms.CharField(
        required=False, max_length=100
    )
    
    def clean(self) -> Dict[str, Any]:
        """Validate the form data."""
        cleaned_data = super().clean()
        
        # Validate date range
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': 'End date must be after start date.'
                })
        
        return cleaned_data


class FiscalAssessmentUpdateForm(HoneypotFieldMixin, forms.Form):
    """Form for updating an existing FiscalAssessment with proper validation.
    
    This form provides proper type validation and explicit field allowlisting,
    addressing vulnerability #7 (Mass Assignment Vulnerability).
    """
    
    # All fields are optional for updates
    airport = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_active=True),
        required=False
    )
    period_type = forms.ChoiceField(
        choices=[(p.value, p.name) for p in AssessmentPeriod],
        required=False
    )
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    status = forms.ChoiceField(
        choices=[(s.value, s.name) for s in AssessmentStatus],
        required=False
    )
    
    # Financial fields
    fuel_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    parking_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    retail_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    landing_fees = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    cargo_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    other_revenue = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    
    # Expense fields
    security_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    maintenance_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    operational_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    staff_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    utility_costs = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    other_expenses = forms.DecimalField(
        max_digits=15, decimal_places=2, required=False, min_value=0
    )
    
    # Operational metrics
    passenger_count = forms.IntegerField(required=False, min_value=0)
    flight_count = forms.IntegerField(required=False, min_value=0)
    
    # Additional fields
    assessment_notes = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'rows': 3}),
        max_length=2000
    )
    assessed_by = forms.CharField(required=False, max_length=100)
    
    def clean(self) -> Dict[str, Any]:
        """Validate the form data."""
        cleaned_data = super().clean()
        
        # Validate date range
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError({
                    'end_date': 'End date must be after start date.'
                })
        
        return cleaned_data


class FiscalAssessmentApprovalForm(forms.Form):
    """Form for approving a FiscalAssessment"""
    
    assessment_id = forms.IntegerField(required=True)
    approved = forms.BooleanField(required=True)
    comments = forms.CharField(required=False, max_length=500)


class ReportCreateForm(HoneypotFieldMixin, forms.Form):
    """Form for creating a new report with proper validation."""
    
    airport = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_active=True),
        required=True
    )
    report_type = forms.ChoiceField(
        choices=[(rt.value, rt.name) for rt in ReportType],
        required=True
    )
    title = forms.CharField(max_length=200, required=True)
    description = forms.CharField(required=False, widget=forms.Textarea, max_length=1000)
    period_start = forms.DateField(required=True)
    period_end = forms.DateField(required=True)
    format = forms.ChoiceField(
        choices=[(fmt.value, fmt.name) for fmt in ReportFormat],
        initial=ReportFormat.HTML.value,
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('period_start')
        end = cleaned_data.get('period_end')

        if start and end and end < start:
            raise ValidationError("End date cannot be before start date.")
        return cleaned_data


class ReportScheduleForm(HoneypotFieldMixin, forms.ModelForm):
    """Form for creating and editing report schedules."""

    class Meta:
        model = ReportSchedule
        fields = [
            'name',
            'report_type',
            'airport',
            'frequency',
            'day_of_week',
            'day_of_month',
            'hour',
            'recipients',
            'format',
            'is_active',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up field widgets and choices
        self.fields['report_type'].choices = [
            (rt.value, rt.name.replace('_', ' ').title())
            for rt in ReportType
        ]
        self.fields['frequency'].choices = [
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ]
        self.fields['day_of_week'].choices = [
            (0, 'Monday'),
            (1, 'Tuesday'),
            (2, 'Wednesday'),
            (3, 'Thursday'),
            (4, 'Friday'),
            (5, 'Saturday'),
            (6, 'Sunday'),
        ]
        self.fields['day_of_month'].choices = [
            (i, f'{i}{"th" if 11 <= i <= 13 else "st" if i % 10 == 1 else "nd" if i % 10 == 2 else "rd" if i % 10 == 3 else "th"}')
            for i in range(1, 32)
        ]
        self.fields['hour'].choices = [
            (i, f'{i:02d}:00') for i in range(24)
        ]
        self.fields['format'].choices = [
            (fmt.value, fmt.name) for fmt in ReportFormat
        ]

        # Add help text
        self.fields['recipients'].help_text = 'Comma-separated list of email addresses'
        self.fields['day_of_week'].help_text = 'Select day for weekly reports'
        self.fields['day_of_month'].help_text = 'Select day for monthly reports'
        self.fields['hour'].help_text = 'Time of day to generate report (24-hour format)'

    def clean_recipients(self):
        """Validate email addresses."""
        recipients = self.cleaned_data.get('recipients', '')
        if not recipients:
            raise ValidationError("At least one recipient is required.")

        emails = [e.strip() for e in recipients.split(',')]
        from django.core.validators import validate_email
        for email in emails:
            try:
                validate_email(email)
            except:
                raise ValidationError(f"Invalid email address: {email}")

        return recipients

    def clean(self):
        cleaned_data = super().clean()
        frequency = cleaned_data.get('frequency')
        day_of_week = cleaned_data.get('day_of_week')
        day_of_month = cleaned_data.get('day_of_month')

        if frequency == 'weekly' and not day_of_week:
            raise ValidationError("Please select a day of week for weekly reports.")

        if frequency == 'monthly' and not day_of_month:
            raise ValidationError("Please select a day of month for monthly reports.")

        return cleaned_data


class DocumentCreateForm(HoneypotFieldMixin, forms.Form):
    """Form for creating a new document with JSON validation."""

    name = forms.CharField(max_length=200, required=True)
    document_type = forms.ChoiceField(
        choices=[(dt.value, dt.name) for dt in Document.DocumentType],
        required=True
    )
    airport = forms.ModelChoiceField(
        queryset=Airport.objects.filter(is_active=True),
        required=False
    )
    content = forms.CharField(widget=forms.Textarea, required=False, initial='{}')
    is_template = forms.BooleanField(required=False)

    def clean_content(self):
        content_str = self.cleaned_data.get('content', '{}')
        if not content_str:
            return {}
        try:
            import json
            content = json.loads(content_str)
            if not isinstance(content, dict):
                raise ValidationError("Content must be a JSON object.")
            return content
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format.")
