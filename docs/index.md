# Django Nitro

**Server-rendered Django views with HTMX + Alpine.js - No JavaScript required**

Django Nitro is a library of views, template tags, and components for building reactive Django applications. Server renders HTML, HTMX swaps it, Alpine handles local UI.

---

## Why Django Nitro?

- **Zero JavaScript** - Build reactive UIs with Python views and template tags
- **Standard Django** - Uses Django views, forms, and templates (no custom runtime)
- **HTMX powered** - Server-rendered HTML swaps for reactive interactions
- **Lightweight** - HTMX (~14KB) + Alpine.js (~15KB) via CDN
- **Batteries included** - Search, filters, pagination, modals, slideovers, toasts, file uploads, wizards
- **Multi-tenant ready** - Generic `OrganizationMixin` for multi-tenant apps

---

## Quick Start

### 1. Install

```bash
pip install django-nitro
```

### 2. Add to settings

```python
INSTALLED_APPS = [
    # ...
    'nitro',
]
```

### 3. Include scripts in base template

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

### 4. Create a view

```python
from nitro.views import NitroListView
from nitro.mixins import OrganizationMixin

class PropertyListView(OrganizationMixin, NitroListView):
    model = Property
    template_name = 'properties/list.html'
    partial_template = 'properties/partials/list_content.html'
    search_fields = ['name', 'address']
    filter_fields = ['status']
    paginate_by = 20
```

### 5. Create template

```html
{% extends "base.html" %}
{% load nitro_tags %}

{% block content %}
<div class="flex gap-4 mb-4">
    {% nitro_search target='#list-content' %}
    {% nitro_filter field='status' options=filter_options.status %}
</div>

<div id="list-content">
    {% include "properties/partials/list_content.html" %}
</div>
{% endblock %}
```

Search, filters, and pagination work via HTMX - no JavaScript needed.

---

## Requirements

- Python 3.12+
- Django 5.2+
- HTMX and Alpine.js (loaded via CDN)

---

## License

MIT License
