"""
Honeypot form protection module.

This module provides form-based honeypot protection to detect and prevent
automated bot submissions. It includes:
- Hidden honeypot fields that bots may fill out
- Time-based submission validation (fast submissions = bots)
- Token-based validation

Security features:
- Fields are visually hidden but exist in HTML (bots often fill all fields)
- Time-based detection catches automated scripts that submit too fast
- Token validation ensures forms were loaded properly before submission
"""

import hashlib
import hmac
import time
import secrets
import logging
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

# Logger for honeypot events
logger = logging.getLogger('honeypot')


def generate_form_token():
    """Generate a secure random token for form validation."""
    return secrets.token_urlsafe(32)


def get_time_secret():
    """Get or create a secret for time-based validation."""
    secret = getattr(settings, 'HONEYPOT_FORM_SECRET', None)
    if secret is None:
        # Generate a persistent secret based on SECRET_KEY
        secret = hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest()[:32]
    return secret


def create_time_token(form_id):
    """Create a time-based token for form submission validation."""
    secret = get_time_secret()
    timestamp = int(time.time())
    message = f"{form_id}:{timestamp}:{secret}"
    token = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"{timestamp}:{token}"


def validate_time_token(form_id, token_str):
    """
    Validate a time-based token.
    
    Returns:
        tuple: (is_valid, is_too_fast, error_message)
    """
    try:
        timestamp_str, token = token_str.split(':')
        timestamp = int(timestamp_str)
    except (ValueError, AttributeError):
        return False, False, "Invalid token format"
    
    # Check token validity
    secret = get_time_secret()
    expected_message = f"{form_id}:{timestamp}:{secret}"
    expected_token = hmac.new(secret.encode(), expected_message.encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(token, expected_token):
        return False, False, "Invalid token"
    
    # Check if submission was too fast (less than 2 seconds)
    current_time = int(time.time())
    time_diff = current_time - timestamp
    
    if time_diff < getattr(settings, 'HONEYPOT_MIN_SUBMIT_TIME', 2):
        return False, True, "Submission too fast - possible bot"
    
    # Check if token is expired (more than 1 hour)
    if time_diff > 3600:
        return False, False, "Token expired"
    
    return True, False, None


class HoneypotFieldMixin:
    """
    Mixin that adds honeypot fields to any form.
    
    This creates hidden fields that:
    - Are hidden via CSS (not visible to human users)
    - Bots may fill out (automated attacks)
    - Are validated on submission
    
    The field names are designed to look enticing to bots.
    """
    
    # Configuration for honeypot fields
    HONEYPOT_FIELD_NAME = getattr(settings, 'HONEYPOT_FIELD_NAME', 'website_url')
    HONEYPOT_EMAIL_NAME = getattr(settings, 'HONEYPOT_EMAIL_NAME', 'contact_email')
    HONEYPOT_PHONE_NAME = getattr(settings, 'HONEYPOT_PHONE_NAME', 'phone_number')
    
    # Time-based token field (hidden, validates legitimate form loading)
    FORM_TIMESTAMP_NAME = '_form_ts'
    FORM_TOKEN_NAME = '_form_tk'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._honeypot_field_names = []
        self._form_id = self.__class__.__name__
        self._create_honeypot_fields()
    
    def _create_honeypot_fields(self):
        """Create honeypot fields for the form."""
        # Website URL field - common spam target
        self.fields[self.HONEYPOT_FIELD_NAME] = forms.CharField(
            required=False,
            label='',
            widget=forms.HiddenInput(attrs={
                'class': 'hp-field hp-website',
                'autocomplete': 'off',
                'tabindex': '-1',
                'aria-hidden': 'true',
            }),
            help_text='Leave this field empty',
        )
        self._honeypot_field_names.append(self.HONEYPOT_FIELD_NAME)
        
        # Email field - another common spam target
        self.fields[self.HONEYPOT_EMAIL_NAME] = forms.EmailField(
            required=False,
            label='',
            widget=forms.HiddenInput(attrs={
                'class': 'hp-field hp-email',
                'autocomplete': 'off',
                'tabindex': '-1',
                'aria-hidden': 'true',
            }),
            help_text='Leave this field empty',
        )
        self._honeypot_field_names.append(self.HONEYPOT_EMAIL_NAME)
        
        # Phone field - yet another spam target
        self.fields[self.HONEYPOT_PHONE_NAME] = forms.CharField(
            required=False,
            label='',
            widget=forms.HiddenInput(attrs={
                'class': 'hp-field hp-phone',
                'autocomplete': 'off',
                'tabindex': '-1',
                'aria-hidden': 'true',
            }),
            help_text='Leave this field empty',
        )
        self._honeypot_field_names.append(self.HONEYPOT_PHONE_NAME)
        
        # Time-based token fields (for legitimate validation)
        self.fields[self.FORM_TIMESTAMP_NAME] = forms.CharField(
            required=False,
            widget=forms.HiddenInput(attrs={'class': 'hp-timestamp'}),
        )
        
        self.fields[self.FORM_TOKEN_NAME] = forms.CharField(
            required=False,
            widget=forms.HiddenInput(attrs={'class': 'hp-token'}),
        )
    
    def clean_honeypot_fields(self):
        """
        Validate honeypot fields.
        
        Raises ValidationError if:
        - Any honeypot field is filled out (bot detected)
        - Time token is invalid or expired
        - Submission was too fast (possible bot)
        """
        cleaned_data = self.cleaned_data
        
        # Check honeypot fields
        for field_name in self._honeypot_field_names:
            value = cleaned_data.get(field_name, '')
            if value and value.strip():
                # Honeypot field was filled - likely a bot
                logger.warning(
                    f"Honeypot field triggered | Form: {self._form_id} | "
                    f"Field: {field_name} | Value length: {len(value)}"
                )
                raise ValidationError(
                    "Form submission rejected. Please try again.",
                    code='honeypot_detected'
                )
        
        # Validate time-based token
        timestamp = cleaned_data.get(self.FORM_TIMESTAMP_NAME, '')
        token = cleaned_data.get(self.FORM_TOKEN_NAME, '')
        
        if timestamp or token:
            token_str = f"{timestamp}:{token}"
            is_valid, is_too_fast, error_msg = validate_time_token(
                self._form_id, token_str
            )
            
            if not is_valid:
                if is_too_fast:
                    logger.warning(
                        f"Fast submission detected | Form: {self._form_id} | "
                        f"Possible automated submission"
                    )
                else:
                    logger.warning(
                        f"Invalid form token | Form: {self._form_id} | "
                        f"Error: {error_msg}"
                    )
                raise ValidationError(
                    "Form validation failed. Please refresh the page and try again.",
                    code='invalid_token'
                )
        
        return cleaned_data
    
    def clean(self):
        """Override clean to include honeypot validation."""
        cleaned_data = super().clean()
        self._create_honeypot_fields()
        self.clean_honeypot_fields()
        return cleaned_data
    
    def get_honeypot_context(self):
        """
        Get context for rendering honeypot fields.
        
        Returns a dict with:
        - honeypot_fields: list of field names
        - timestamp_token: time-based token for form
        - form_token: validation token
        """
        if not hasattr(self, '_honeypot_initialized'):
            self._create_honeypot_fields()
            self._honeypot_initialized = True
        
        timestamp = int(time.time())
        time_token = create_time_token(self._form_id)
        timestamp_val, token_val = time_token.split(':')
        
        return {
            'honeypot_fields': self._honeypot_field_names,
            'timestamp_name': self.FORM_TIMESTAMP_NAME,
            'token_name': self.FORM_TOKEN_NAME,
            'timestamp_value': timestamp_val,
            'token_value': token_val,
            'form_id': self._form_id,
        }


class HoneypotFormMixin:
    """
    Alternative mixin for forms that need simpler honeypot protection.
    
    Use this for forms where you want basic protection without
    the complexity of time-based tokens.
    """
    
    # Single honeypot field configuration
    HONEYPOT_FIELD = getattr(settings, 'HONEYPOT_FIELD', 'hp_email')
    HONEYPOT_VALUE = getattr(settings, 'HONEYPOT_VALUE', '')  # Expected empty value
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add honeypot field
        self.fields[self.HONEYPOT_FIELD] = forms.CharField(
            required=False,
            widget=forms.HiddenInput(attrs={
                'style': 'display:none;',
                'tabindex': '-1',
                'autocomplete': 'off',
            }),
        )
    
    def clean_honeypot_field(self):
        """Validate the honeypot field is empty."""
        value = self.cleaned_data.get(self.HONEYPOT_FIELD, '')
        if value:
            logger.warning(f"Simple honeypot triggered | Form: {self.__class__.__name__}")
            raise ValidationError("Invalid submission", code='honeypot')
        return ''


# CSS to hide honeypot fields - add to your forms CSS
HONEYPOT_CSS = """
/* Honeypot field hiding */
.hp-field {
    position: absolute !important;
    left: -9999px !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

/* Alternative hiding method for extra security */
input[name="website_url"],
input[name="contact_email"],
input[name="phone_number"],
input[class*="hp-"] {
    position: absolute;
    top: -9999px;
    left: -9999px;
}
"""
