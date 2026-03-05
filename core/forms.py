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

from .models import Airport, FiscalAssessment, AssessmentPeriod, AssessmentStatus


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


class FiscalAssessmentCreateForm(forms.Form):
    """Form for creating a new FiscalAssessment with proper validation.
    
    This form provides proper type validation for all POST data,
    addressing vulnerability #6 (Missing Input Validation).
    
    Attributes:
        airport: Required airport selection.
        period_type: Required period type selection.
        start_date: Required start date.
        end_date: Required end date.
        status: Assessment status (optional, defaults to DRAFT).
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
        """Validate the form data.
        
        Returns:
            Cleaned form data.
            
        Raises:
            ValidationError: If validation fails.
        """
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


class FiscalAssessmentUpdateForm(forms.Form):
    """Form for updating an existing FiscalAssessment with proper validation.
    
    This form provides proper type validation and explicit field allowlisting,
    addressing vulnerability #7 (Mass Assignment Vulnerability).
    
    Attributes:
        Same as FiscalAssessmentCreateForm but all fields are optional
        since we're updating an existing record.
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
        """Validate the form data.
        
        Returns:
            Cleaned form data.
            
        Raises:
            ValidationError: If validation fails.
        """
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
