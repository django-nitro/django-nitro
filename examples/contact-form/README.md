# Contact Form Example (v0.6.0)

This example demonstrates the new **Form Field Template Tags** introduced in Django Nitro v0.6.0.

## Features Demonstrated

- `{% nitro_input %}` - Text, email, and tel inputs
- `{% nitro_select %}` - Dropdown with choices
- `{% nitro_textarea %}` - Multi-line text input
- `{% nitro_checkbox %}` - Checkbox for terms acceptance
- Automatic error handling and validation
- Bootstrap styling integration

## Setup

1. Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'nitro',
]
```

2. Include Nitro URLs in your `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('nitro/', include('nitro.urls')),
    path('', contact_form_view, name='contact_form'),
]
```

3. Run the example:

```bash
python manage.py runserver
```

## Key Concepts

### Form Field Template Tags

All form field tags provide:
- Automatic Alpine.js binding
- Built-in error display
- Bootstrap styling
- Optional chaining support for nested fields

### Validation

The component uses Pydantic for validation:
- Required fields
- Email format validation
- Phone number format validation
- Minimum length validation

### Default Debounce (200ms)

All `nitro_model` bindings now include a default 200ms debounce to reduce server load. To disable:

```django
{% nitro_model 'field' no_debounce=True %}
```

## File Structure

```
contact-form/
├── README.md           # This file
├── component.py        # ContactForm component
└── template.html       # Template with form field tags
```
