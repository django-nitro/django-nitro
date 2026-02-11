# Migration from v0.7

v0.8.0 is a complete architecture rewrite. The component-based system has been replaced with standard Django views + HTMX.

## What Changed

| v0.7 | v0.8 |
|------|------|
| `NitroComponent` classes | Django views (`NitroListView`, `NitroFormView`) |
| Pydantic `BaseModel` state | Django forms and template context |
| Django Ninja JSON API | Server-rendered HTML + HTMX swaps |
| `@register_component` | Standard Django URL routing |
| `call('action')` in templates | `hx-post`/`hx-get` HTMX attributes |
| `nitro_model` two-way binding | Alpine `x-model` (local) + form submit |
| `nitro_action` template tag | HTMX attributes via template tags |
| `requirements: pydantic, django-ninja` | `requirements: Django only` |

## Why the Change

The component system added complexity (Pydantic state sync, JSON API, client-side rendering) that wasn't necessary for most Django apps. HTMX achieves the same reactive UX with standard Django patterns, is easier to debug, and has zero additional Python dependencies.

---

## Migration Steps

### 1. Remove Old Dependencies

```bash
pip uninstall pydantic django-ninja
pip install django-nitro==0.8.0
```

### 2. Convert Components to Views

**Before (v0.7):**
```python
from nitro import NitroComponent, register_component
from pydantic import BaseModel

class PropertyListState(BaseModel):
    properties: list = []
    search: str = ""

@register_component('property-list')
class PropertyListComponent(NitroComponent):
    template = 'components/property_list.html'

    def mount(self):
        self.state = PropertyListState(
            properties=list(Property.objects.all())
        )

    def action_search(self, query: str):
        self.state.search = query
        self.state.properties = list(
            Property.objects.filter(name__icontains=query)
        )
```

**After (v0.8):**
```python
from nitro.views import NitroListView

class PropertyListView(NitroListView):
    model = Property
    template_name = 'properties/list.html'
    partial_template = 'properties/partials/list_content.html'
    search_fields = ['name', 'address']
    paginate_by = 20
```

### 3. Convert Templates

**Before (v0.7):**
```html
{% load nitro_tags %}
<div nitro-component="property-list">
    <input nitro-model="search" placeholder="Search...">

    {% for property in state.properties %}
    <div>{{ property.name }}</div>
    {% endfor %}
</div>
```

**After (v0.8):**
```html
{% load nitro_tags %}
{% extends "base.html" %}

{% block content %}
<div>
    {% nitro_search target='#list-content' %}

    <div id="list-content">
        {% include "properties/partials/list_content.html" %}
    </div>
</div>
{% endblock %}
```

```html
<!-- partials/list_content.html -->
{% load nitro_tags %}
{% for property in object_list %}
<div>{{ property.name }}</div>
{% endfor %}
{% nitro_pagination page_obj target='#list-content' %}
```

### 4. Convert Actions to Forms/HTMX

**Before (v0.7):**
```html
<button nitro-action="delete" nitro-args='{"id": {{ property.id }}}'>
    Delete
</button>
```

**After (v0.8):**
```html
<button
    hx-post="{% url 'property_delete' property.pk %}"
    hx-target="#list-content"
    hx-confirm="¿Eliminar?"
>
    Delete
</button>
```

### 5. Update URLs

**Before (v0.7):**
```python
# Components auto-registered via @register_component
urlpatterns = [
    path('nitro/', include('nitro.urls')),
]
```

**After (v0.8):**
```python
from .views import PropertyListView, PropertyCreateView

urlpatterns = [
    path('properties/', PropertyListView.as_view(), name='property_list'),
    path('properties/create/', PropertyCreateView.as_view(), name='property_create'),
]
```

---

## Common Patterns

### Two-Way Binding → Form Submit

**v0.7:** Automatic state sync via `nitro-model`
**v0.8:** Standard form submission + HTMX

```html
<form hx-post="{% url 'property_update' pk %}" hx-target="#list-content">
    {% csrf_token %}
    {% nitro_field form.name %}
    <button type="submit">Save</button>
</form>
```

### Component Actions → HTMX Actions

**v0.7:** `nitro-action="save"`
**v0.8:** `hx-post="/save/"`

### State Management → Context Variables

**v0.7:** `self.state.properties`
**v0.8:** `context['object_list']`

---

## Removed Features

These v0.7 features have been removed:

- `NitroComponent` base class
- `@register_component` decorator
- Pydantic state classes
- Django Ninja JSON API
- `nitro-model` directive
- `nitro-action` directive
- Client-side state synchronization
- `nitro.api` module
- `nitro.registry` module

---

## New Features in v0.8

- `NitroListView` with built-in search, filter, sort, pagination
- `NitroWizard` for multi-step forms
- `NitroTable` declarative tables
- `NitroFilterSet` faceted filters
- `ExportMixin` for CSV/Excel
- 20+ HTML components
- 10+ Alpine.js components
- Comprehensive template tags

---

## Getting Help

If you encounter issues migrating:

1. Check this documentation
2. Review the [Quick Start](../getting-started/quick-start.md)
3. Open an issue on GitHub
