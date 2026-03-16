"""Custom template filters for core templates."""

import json
from decimal import Decimal
from django import template

register = template.Library()


class DjangoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Django-specific types."""
    
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


@register.filter
def replace_underscore(value):
    """Replace underscores with spaces in a string."""
    if value:
        return str(value).replace('_', ' ')
    return value


@register.filter
def intcomma(value):
    """Format an integer or float with comma separators for thousands.

    Can be used alone or after floatformat filter.

    Examples:
        1000 -> 1,000
        1000000 -> 1,000,000
        "1000000.50" -> 1,000,000.50 (when used after floatformat)
        1000.5 -> 1,000.5
    """
    try:
        # If value is a string (e.g., from floatformat), parse it
        if isinstance(value, str):
            if '.' in value:
                # Has decimal part
                int_part, dec_part = value.split('.')
                return f"{int(int_part):,}.{dec_part}"
            else:
                return f"{int(value):,}"
        # Handle numeric values directly
        float_val = float(value)
        int_part = int(float_val)
        if float_val == int_part:
            # No decimal part
            return f"{int_part:,}"
        else:
            # Has decimal part - preserve original decimal representation
            return f"{int_part:,}{str(float_val)[len(str(int_part)):]}"
    except (ValueError, TypeError):
        return value


@register.filter
def jsonify(value):
    """Convert a Python object to JSON string."""
    if value is None:
        return '{}'
    return json.dumps(value, cls=DjangoJSONEncoder)


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    return dictionary.get(key)


@register.filter
def sum_attr(list_of_dicts, attr):
    """Sum an attribute across a list of dictionaries.
    
    Usage: {{ my_list|sum_attr:'attribute_name' }}
    """
    if not list_of_dicts:
        return 0
    total = 0
    for item in list_of_dicts:
        if isinstance(item, dict):
            total += item.get(attr, 0) or 0
    return total


@register.filter
def avg_attr(list_of_dicts, attr):
    """Calculate average of an attribute across a list of dictionaries.
    
    Usage: {{ my_list|avg_attr:'attribute_name' }}
    """
    if not list_of_dicts:
        return 0
    total = 0
    count = 0
    for item in list_of_dicts:
        if isinstance(item, dict):
            value = item.get(attr, 0) or 0
            total += value
            count += 1
    return total / count if count > 0 else 0
