"""Custom template filters for core templates."""

import json
from django import template

register = template.Library()


@register.filter
def replace_underscore(value):
    """Replace underscores with spaces in a string."""
    if value:
        return str(value).replace('_', ' ')
    return value


@register.filter
def jsonify(value):
    """Convert a Python object to JSON string."""
    if value is None:
        return '{}'
    return json.dumps(value, indent=2)


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    return dictionary.get(key)
