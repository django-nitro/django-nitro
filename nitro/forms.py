"""
Nitro 0.8 - Form utilities.

Provides NitroFormMixin, NitroModelForm, and NitroForm that automatically
apply Tailwind CSS classes to all form widgets. Also includes custom field
types for Dominican Republic-specific formats (phone, cedula, currency).

Usage:
    class PropertyForm(NitroModelForm):
        class Meta:
            model = Property
            fields = ['name', 'address', 'rent_amount']

    # All widgets automatically get Tailwind classes.
    # You only need to declare widgets for non-default widget types
    # or extra attrs (type='date', rows=3, min=0, etc.)
"""

from django import forms
from django.forms.widgets import (
    TextInput, NumberInput, EmailInput, URLInput,
    PasswordInput, Textarea, Select, SelectMultiple,
    CheckboxInput, FileInput, DateInput, DateTimeInput,
    TimeInput,
)


# Tailwind CSS classes for form widgets (Mint design system)
TAILWIND_CLASSES = {
    'input': (
        'w-full px-4 py-2.5 border border-surface-200 rounded-xl text-sm '
        'text-surface-900 placeholder-surface-400 '
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 '
        'transition-all'
    ),
    'input_error': (
        'w-full px-4 py-2.5 border border-red-300 rounded-xl text-sm '
        'text-surface-900 bg-red-50 '
        'focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500'
    ),
    'textarea': (
        'w-full px-4 py-2.5 border border-surface-200 rounded-xl text-sm '
        'text-surface-900 placeholder-surface-400 '
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 '
        'resize-none transition-all'
    ),
    'select': (
        'w-full px-4 py-2.5 border border-surface-200 rounded-xl text-sm '
        'text-surface-900 bg-white '
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 '
        'transition-all'
    ),
    'checkbox': (
        'h-4 w-4 text-primary-600 border-surface-300 rounded '
        'focus:ring-primary-500'
    ),
    'file': (
        'w-full text-sm text-surface-500 file:mr-4 file:py-2 file:px-4 '
        'file:rounded-xl file:border-0 file:text-sm file:font-medium '
        'file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100'
    ),
}


class NitroFormMixin:
    """
    Mixin that applies Tailwind classes to all form fields automatically.

    Usage:
        class PropertyForm(NitroFormMixin, forms.ModelForm):
            class Meta:
                model = Property
                fields = ['name', 'address', 'rent_amount']
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()

    def apply_tailwind_classes(self):
        """Apply Tailwind classes to all fields based on widget type."""
        for field_name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, (TextInput, NumberInput, EmailInput, URLInput,
                                   PasswordInput, DateInput, DateTimeInput, TimeInput)):
                self._add_class(widget, TAILWIND_CLASSES['input'])
            elif isinstance(widget, Textarea):
                self._add_class(widget, TAILWIND_CLASSES['textarea'])
            elif isinstance(widget, (Select, SelectMultiple)):
                self._add_class(widget, TAILWIND_CLASSES['select'])
            elif isinstance(widget, CheckboxInput):
                self._add_class(widget, TAILWIND_CLASSES['checkbox'])
            elif isinstance(widget, FileInput):
                self._add_class(widget, TAILWIND_CLASSES['file'])

            # Add placeholder from label if not already set
            if hasattr(widget, 'attrs') and 'placeholder' not in widget.attrs:
                if field.label:
                    widget.attrs['placeholder'] = field.label

    def _add_class(self, widget, css_class):
        """Add CSS class to widget, preserving any existing classes."""
        existing = widget.attrs.get('class', '')
        widget.attrs['class'] = f'{existing} {css_class}'.strip()


class NitroModelForm(NitroFormMixin, forms.ModelForm):
    """
    ModelForm with automatic Tailwind styling.

    Usage:
        class PropertyForm(NitroModelForm):
            class Meta:
                model = Property
                fields = ['name', 'address']
    """
    pass


class NitroForm(NitroFormMixin, forms.Form):
    """
    Regular Form with automatic Tailwind styling.
    """
    pass


# =============================================================================
# Custom Field Types (Dominican Republic)
# =============================================================================

class PhoneField(forms.CharField):
    """Phone number field with DR formatting."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 20)
        kwargs.setdefault('widget', TextInput(attrs={
            'type': 'tel',
            'placeholder': '(809) 555-1234',
        }))
        super().__init__(*args, **kwargs)


class CedulaField(forms.CharField):
    """Dominican cedula (ID) field with validation."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 13)
        kwargs.setdefault('widget', TextInput(attrs={
            'placeholder': '001-1234567-8',
        }))
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if value:
            digits = value.replace('-', '')
            if len(digits) != 11 or not digits.isdigit():
                raise forms.ValidationError('Formato de cédula inválido')
        return value


class CurrencyField(forms.DecimalField):
    """Currency amount field (RD$)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_digits', 12)
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('min_value', 0)
        kwargs.setdefault('widget', NumberInput(attrs={
            'step': '0.01',
            'min': '0',
        }))
        super().__init__(*args, **kwargs)
