"""Utility functions for Django Nitro framework.

This module contains shared utility functions used across the Nitro framework
to reduce code duplication and improve maintainability.
"""

import os
import re
from typing import Optional
from django.utils.text import slugify


# =============================================================================
# FILE UPLOAD SECURITY UTILITIES
# =============================================================================

# Default allowed MIME types (safe for most applications)
DEFAULT_ALLOWED_TYPES = {
    # Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    # Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    # Text
    'text/plain',
    'text/csv',
}

# Default max file size: 10MB
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    """
    Safely sanitize an uploaded filename to prevent path traversal and injection.

    This function:
    1. Removes any path components (prevents path traversal like ../../etc/passwd)
    2. Slugifies the name part (removes special characters)
    3. Preserves the extension (lowercased)
    4. Handles edge cases (no name, no extension, etc.)

    Args:
        filename: Original filename from upload

    Returns:
        Safe filename string

    Example:
        >>> sanitize_filename('../../../etc/passwd')
        'etc-passwd'
        >>> sanitize_filename('My Document (1).PDF')
        'my-document-1.pdf'
        >>> sanitize_filename('image.jpg')
        'image.jpg'
    """
    if not filename:
        return 'unnamed_file'

    # Remove any path components (security critical)
    filename = os.path.basename(filename)

    # Split name and extension
    name, ext = os.path.splitext(filename)

    # Slugify the name (removes special chars, lowercases)
    safe_name = slugify(name) if name else 'file'

    # Clean extension (lowercase, remove any weird chars)
    safe_ext = ext.lower() if ext else ''
    # Only allow alphanumeric extensions
    if safe_ext and not re.match(r'^\.[a-z0-9]+$', safe_ext):
        safe_ext = ''

    return f"{safe_name}{safe_ext}" if safe_name else f"file{safe_ext}"


def validate_file_upload(
    uploaded_file,
    max_size: int = DEFAULT_MAX_FILE_SIZE,
    allowed_types: Optional[set] = None,
    allowed_extensions: Optional[set] = None,
) -> tuple[bool, str]:
    """
    Validate an uploaded file for security.

    Performs server-side validation of:
    1. File size (prevents DoS via large uploads)
    2. MIME type (content_type check)
    3. Extension whitelist (optional additional check)

    Args:
        uploaded_file: Django UploadedFile object
        max_size: Maximum file size in bytes (default: 10MB)
        allowed_types: Set of allowed MIME types (default: common safe types)
        allowed_extensions: Optional set of allowed extensions (e.g., {'.jpg', '.pdf'})

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Example:
        >>> is_valid, error = validate_file_upload(request.FILES['document'])
        >>> if not is_valid:
        ...     return JsonResponse({'error': error}, status=400)
    """
    if uploaded_file is None:
        return False, "No file provided"

    # Use defaults if not specified
    if allowed_types is None:
        allowed_types = DEFAULT_ALLOWED_TYPES

    # 1. Check file size
    if uploaded_file.size > max_size:
        max_mb = max_size / (1024 * 1024)
        file_mb = uploaded_file.size / (1024 * 1024)
        return False, f"File too large ({file_mb:.1f}MB). Maximum size: {max_mb:.0f}MB"

    # 2. Check MIME type
    content_type = getattr(uploaded_file, 'content_type', None)
    if content_type and content_type not in allowed_types:
        return False, f"File type '{content_type}' not allowed"

    # 3. Check extension (optional)
    if allowed_extensions:
        _, ext = os.path.splitext(uploaded_file.name)
        ext = ext.lower()
        if ext not in allowed_extensions:
            return False, f"File extension '{ext}' not allowed"

    return True, ""


def get_safe_upload_path(base_dir: str, filename: str, add_timestamp: bool = True) -> str:
    """
    Generate a safe upload path for a file.

    Combines sanitization with optional timestamp to prevent overwrites.

    Args:
        base_dir: Base directory for uploads (e.g., 'documents/tenant/')
        filename: Original filename
        add_timestamp: If True, adds timestamp to prevent overwrites

    Returns:
        Safe relative path for storage

    Example:
        >>> get_safe_upload_path('documents/tenant/', 'Contract.pdf')
        'documents/tenant/1705123456_contract.pdf'
    """
    import time

    safe_name = sanitize_filename(filename)

    if add_timestamp:
        timestamp = int(time.time())
        name, ext = os.path.splitext(safe_name)
        safe_name = f"{timestamp}_{name}{ext}"

    # Ensure base_dir doesn't have leading/trailing issues
    base_dir = base_dir.strip('/').replace('..', '')

    return f"{base_dir}/{safe_name}"


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
    if "." in field:
        parts = field.split(".")
        return "errors?." + "?.".join(parts)
    return f"errors?.{field}"


def build_safe_field(field: str, edit_buffer_name: str = "edit_buffer") -> tuple[str, bool]:
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
    safe_field = field.replace(".", "?.") if is_edit_buffer else field
    return safe_field, is_edit_buffer
