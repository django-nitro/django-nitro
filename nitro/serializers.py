"""
Django Nitro 0.8 - Lightweight serialization utilities.

For edge cases where you need to serialize model data to JSON
(e.g., Alpine x-data initialization, API responses).

In Nitro 0.8, templates access model instances directly via context,
so this module is rarely needed.
"""

import uuid
from datetime import date, datetime, time
from decimal import Decimal


def serialize_value(value):
    """Convert a Python value to a JSON-safe representation."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def serialize_model(instance, fields=None, extra=None):
    """
    Serialize a Django model instance to a dict.

    Args:
        instance: Django model instance
        fields: List of field names to include (None = all)
        extra: Dict of additional key-value pairs to include

    Returns:
        Dict with JSON-safe values
    """
    if instance is None:
        return None

    data = {}

    if fields is None:
        # Get all concrete field names
        fields = [f.name for f in instance._meta.concrete_fields]

    for field_name in fields:
        value = getattr(instance, field_name, None)
        data[field_name] = serialize_value(value)

    if extra:
        data.update(extra)

    return data
