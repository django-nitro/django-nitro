"""Utility functions for Django Nitro framework.

This module contains shared utility functions used across the Nitro framework
to reduce code duplication and improve maintainability.
"""


def build_error_path(field: str) -> str:
    """Build Alpine.js error path with optional chaining for nested fields.

    Converts field paths to error paths that work with Alpine.js optional chaining:
    - 'name' -> 'errors?.name'
    - 'address.street' -> 'errors?.address?.street'

    Args:
        field: Field path (e.g., 'name', 'address.street')

    Returns:
        Error path string with optional chaining

    Example:
        >>> build_error_path('name')
        'errors?.name'
        >>> build_error_path('address.street')
        'errors?.address?.street'
    """
    if '.' in field:
        parts = field.split('.')
        return 'errors?.' + '?.'.join(parts)
    return f'errors?.{field}'


def build_safe_field(field: str, edit_buffer_name: str = 'edit_buffer') -> tuple[str, bool]:
    """Build safe field path with optional chaining for edit buffers.

    When working with edit buffers (fields that may be null), we need optional
    chaining to prevent JavaScript errors. This function detects edit buffers
    and adds optional chaining automatically.

    Args:
        field: Field path (e.g., 'create_buffer.name', 'edit_buffer.email')
        edit_buffer_name: Name of the edit buffer field (default: 'edit_buffer')

    Returns:
        Tuple of (safe_field_path, is_edit_buffer)

    Example:
        >>> build_safe_field('create_buffer.name')
        ('create_buffer.name', False)
        >>> build_safe_field('edit_buffer.email')
        ('edit_buffer?.email', True)
    """
    is_edit_buffer = edit_buffer_name in field
    safe_field = field.replace('.', '?.') if is_edit_buffer else field
    return safe_field, is_edit_buffer
