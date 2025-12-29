"""
Django Nitro Configuration System

Provides centralized configuration management with Django settings integration.
Components can override global settings with instance-level configuration.

Usage:
    # In Django settings.py
    NITRO = {
        'TOAST_ENABLED': True,
        'TOAST_POSITION': 'top-right',
        'TOAST_DURATION': 3000,
        'TOAST_STYLE': 'default',
        'DEBUG': False,
    }

    # In component
    from nitro.conf import get_setting

    toast_enabled = get_setting('TOAST_ENABLED')
"""

from typing import Any

from django.conf import settings

# Default configuration values
DEFAULTS = {
    "TOAST_ENABLED": True,
    "TOAST_POSITION": "top-right",  # top-right, top-left, top-center, bottom-right, bottom-left, bottom-center
    "TOAST_DURATION": 3000,  # milliseconds
    "TOAST_STYLE": "default",  # default, minimal, bordered
    "DEBUG": False,  # Enable debug logging in nitro.js
}


def get_setting(name: str, default: Any = None) -> Any:
    """
    Get a Nitro configuration setting.

    Looks for setting in the following order:
    1. Django settings.NITRO dict
    2. Built-in DEFAULTS dict
    3. Provided default parameter

    Args:
        name: Setting name (e.g., 'TOAST_ENABLED')
        default: Fallback value if setting not found

    Returns:
        Setting value

    Example:
        toast_position = get_setting('TOAST_POSITION', 'top-right')
    """
    # Try Django settings first
    nitro_settings = getattr(settings, "NITRO", {})
    if name in nitro_settings:
        return nitro_settings[name]

    # Fall back to built-in defaults
    if name in DEFAULTS:
        return DEFAULTS[name]

    # Return provided default
    return default


def get_all_settings() -> dict[str, Any]:
    """
    Get all Nitro settings merged from defaults and Django settings.

    Returns:
        Dictionary with all configuration values

    Example:
        settings = get_all_settings()
        print(settings['TOAST_ENABLED'])
    """
    # Start with built-in defaults
    merged = DEFAULTS.copy()

    # Merge Django settings
    nitro_settings = getattr(settings, "NITRO", {})
    merged.update(nitro_settings)

    return merged
