# Installation

## Requirements

- Python 3.12+
- Django 5.2+

## Install via pip

```bash
pip install django-nitro
```

## Configuration

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'nitro',
]
```

### 2. Optional settings

```python
# settings.py
NITRO = {
    'DEFAULT_PAGINATION': 20,
    'TOAST_DURATION': 5000,
    'TOAST_POSITION': 'top-right',
}
```

### 3. Include static files in base template

```html
{% load nitro_tags %}
<!DOCTYPE html>
<html>
<head>
    {% nitro_scripts %}
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
    {% block content %}{% endblock %}
    {% nitro_toast %}
</body>
</html>
```

`{% nitro_scripts %}` includes:

- HTMX from CDN
- `nitro.js` - HTMX configuration and toast handling
- `alpine-components.js` - Reusable Alpine.js components

## What's Included

### Views

- `NitroView` - Base view with HTMX detection and toast helpers
- `NitroListView` - List with search, filter, sort, pagination
- `NitroModelView` - Single object detail
- `NitroFormView` - Form handling
- `NitroCreateView` / `NitroUpdateView` / `NitroDeleteView` - CRUD operations
- `NitroWizard` - Multi-step forms

### Template Tags

- HTMX action tags: `{% nitro_search %}`, `{% nitro_filter %}`, `{% nitro_pagination %}`
- Form tags: `{% nitro_field %}`, `{% nitro_select %}`
- Component tags: `{% nitro_modal %}`, `{% nitro_slideover %}`, `{% nitro_tabs %}`
- Display filters: `{{ amount|currency }}`, `{{ status|status_badge }}`

### Components

- 20+ HTML components: toast, modal, slideover, tabs, empty_state, stats_card, etc.
- 10+ Alpine.js components: fileUpload, clipboard, searchableSelect, etc.

### Utilities

- Currency formatting (multi-currency support)
- Date utilities and relative dates
- CSV/Excel export helpers
