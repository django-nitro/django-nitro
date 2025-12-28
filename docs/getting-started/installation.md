# Installation

## Requirements

- Python 3.12+
- Django 5.2+
- django-ninja 1.4.0+
- pydantic 2.0+

## Install from PyPI

```bash
pip install django-nitro
```

## Install from Source

```bash
git clone https://github.com/django-nitro/django-nitro.git
cd django-nitro
pip install -e .
```

## Setup

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'nitro',
    # your apps here
]
```

### 2. Include Nitro API URLs

```python
# urls.py
from django.urls import path
from nitro.api import api

urlpatterns = [
    # ...
    path("api/nitro/", api.urls),  # Important: must be under /api/nitro/
]
```

### 3. Add Alpine and Nitro JS to your base template

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>My App</title>
    <!-- Alpine JS (required) -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body>
    {% block content %}{% endblock %}

    <!-- Nitro JS (load AFTER Alpine) -->
    {% load static %}
    <script src="{% static 'nitro/nitro.js' %}"></script>
</body>
</html>
```

### 4. Run collectstatic (production)

```bash
python manage.py collectstatic
```

## Next Steps

- [Quick Start Tutorial](quick-start.md)
- [Core Concepts](../core-concepts/components.md)
- [Examples](../examples/counter.md)
