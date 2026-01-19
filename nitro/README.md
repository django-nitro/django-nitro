# Django Nitro v0.7.0

**True Zero-JavaScript Reactive Components for Django**

Nitro brings Livewire-style reactive components to Django. Write Python, get reactive UIs - **without ever writing JavaScript**.

## The Zero-JS Philosophy

Unlike other frameworks that wrap JavaScript in template tags, Nitro is **truly Zero-JS**:

```django
{# OLD WAY (requires JavaScript knowledge) - DEPRECATED #}
{% nitro_bind "item.status === 'active' ? 'Activo' : 'Inactivo'" %}
{% nitro_class_map "{'bg-green-100': item.status === 'active'}" %}

{# NEW WAY (Pure Python, Zero-JS) #}
{% nitro_switch 'item.status' active='Activo' expired='Vencido' default='Borrador' %}
{% nitro_css 'item.status' active='bg-green-100 text-green-700' expired='bg-red-100' %}
```

**You define mappings in Python. Nitro handles the rest.**

## Features

- **True Zero JavaScript** - No JS ternaries, no Alpine expressions
- **Python-First** - All logic defined in Python kwargs or component methods
- **Pydantic State** - Type-safe, validated component state
- **Django Ninja API** - Modern, fast, type-safe API layer with OpenAPI docs
- **Server-Side Rendering** - SEO-friendly with hydration
- **Django Native** - Works with Django templates, no build step
- **Auto-infer `state_class`** - No redundant declarations when using Generics
- **CacheMixin** - Built-in state and HTML caching for performance
- **Unaccent Search** - Accent-insensitive search out of the box (PostgreSQL)

## Django Ninja Integration

Nitro is built on [Django Ninja](https://django-ninja.dev/), providing a modern, high-performance API layer:

### What You Get

- **Automatic Request Validation** - Pydantic schemas validate all incoming requests
- **OpenAPI Documentation** - Interactive API docs at `/api/nitro/docs`
- **Type-Safe File Uploads** - Using `Form[Schema]` + `File[UploadedFile]`
- **Exception Handlers** - Consistent error responses across your app
- **Fast** - Async-ready with minimal overhead

### API Endpoints

```python
# Nitro exposes two endpoints:

# 1. JSON dispatch (standard actions)
POST /api/nitro/dispatch
{
    "component_name": "TaskList",
    "action": "toggle_task",
    "state": {...},
    "payload": {"task_id": "123"},
    "integrity": "hmac_signature"
}

# 2. File upload dispatch (multipart/form-data)
POST /api/nitro/dispatch-file
# Form fields + file attachment
```

### Request/Response Schemas

```python
from ninja import Schema

class ActionPayload(Schema):
    """Validated automatically by Django Ninja."""
    component_name: str
    action: str
    state: dict
    payload: dict = {}
    integrity: str | None = None

class NitroResponse(Schema):
    """Type-safe response structure."""
    html: str | None = None
    state: dict | None = None
    redirect: str | None = None
    error: str | None = None
```

### Exception Handling

```python
# Global exception handlers provide consistent error responses
@api.exception_handler(PermissionDenied)
def permission_denied_handler(request, exc):
    return api.create_response(
        request,
        {"error": "Permission denied"},
        status=403
    )
```

### Why Django Ninja?

| Feature | Django REST Framework | Django Ninja |
|---------|----------------------|--------------|
| Performance | Slower | **2-3x faster** |
| Type hints | Optional | **Native** |
| Pydantic | Separate serializers | **Built-in** |
| OpenAPI | django-yasg needed | **Automatic** |
| Async | Limited | **Full support** |

Nitro chose Django Ninja for its modern Python approach and seamless Pydantic integration.

## Quick Start

### 1. Installation

```bash
pip install django-nitro
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'nitro',
]
```

### 2. Create a Component

```python
# components/task_list.py
from pydantic import BaseModel
from nitro import NitroComponent, register_component

class Task(BaseModel):
    id: str
    title: str
    status: str  # 'pending', 'done'

class TaskListState(BaseModel):
    tasks: list[Task] = []

@register_component
class TaskList(NitroComponent[TaskListState]):
    template_name = "components/task_list.html"
    # state_class inferred from Generic - no need to declare!

    def toggle_task(self, task_id: str):
        for task in self.state.tasks:
            if task.id == task_id:
                task.status = 'done' if task.status == 'pending' else 'pending'
```

### 3. Create the Template (Zero-JS!)

```django
{% load nitro_tags %}

<div class="task-list">
    <h2>Tasks: {% nitro_count 'tasks.length' singular='task' plural='tasks' %}</h2>

    {% nitro_for 'tasks' as 'task' %}
        <div class="task"
             {% nitro_css 'task.status' done='bg-green-50 line-through' pending='bg-white' %}>

            {# Display status with Python-defined mappings #}
            {% nitro_switch 'task.status' done='Completado' pending='Pendiente' %}

            <span>{% nitro_text 'task.title' %}</span>

            <button {% nitro_action 'toggle_task' task_id='task.id' %}>
                Toggle
            </button>
        </div>
    {% end_nitro_for %}
</div>
```

**Notice: No JavaScript anywhere!** All the conditional logic is defined in Python kwargs.

## Zero-JS Template Tags

### Conditional Text

```django
{# Display different text based on field value #}
{% nitro_switch 'item.status' active='Activo' expired='Vencido' default='Borrador' %}

{# With emoji #}
{% nitro_switch 'priority' high='Alta' medium='Media' low='Baja' %}
```

### Conditional CSS Classes

```django
{# Apply different classes based on field value #}
<div {% nitro_css 'item.status' active='bg-green-100' expired='bg-red-100' default='bg-gray-100' %}>
```

### Status Badges (Text + Classes Combined)

```django
{# Render a complete badge with text and styling #}
{% nitro_badge 'item.status'
   active='Activo:bg-green-100 text-green-700'
   expired='Vencido:bg-red-100 text-red-700'
   default_class='bg-gray-100' %}
```

### Visibility

```django
{# Show/hide based on boolean - no JS expressions #}
<div {% nitro_visible 'item.is_active' %}>Visible when active</div>
<div {% nitro_visible 'item.is_deleted' negate=True %}>Hidden when deleted</div>
```

### Pluralization

```django
{# Automatic singular/plural #}
{% nitro_plural 'count' singular='item' plural='items' zero='No items' %}

{# Count with label: "5 items", "1 item", "No items" #}
{% nitro_count 'items.length' singular='propiedad' plural='propiedades' %}
```

### Formatting

```django
{# Currency #}
{% nitro_format 'item.price' format_type='currency' prefix='$' %}

{# With empty state #}
{% nitro_format 'item.date' empty='Sin fecha' %}

{# Date formatting #}
{% nitro_date 'item.created_at' empty='N/A' %}
```

### Iteration

```django
{# Loop with server-side rendering + Alpine reactivity #}
{% nitro_for 'items' as 'item' %}
    <div>{% nitro_text 'item.name' %}</div>
{% end_nitro_for %}
```

## Comparison: Old vs New

### Before (Required JavaScript Knowledge)

```django
{# Developer had to know JS ternary syntax #}
<span {% nitro_bind "item.status === 'active' ? 'Activo' : item.status === 'expired' ? 'Vencido' : 'Borrador'" %}></span>

{# Developer had to know Alpine :class syntax #}
<div {% nitro_class_map "{'bg-green-100 text-green-700': item.status === 'active', 'bg-red-100': item.status === 'expired'}" %}></div>
```

### After (True Zero-JS)

```django
{# Pure Python kwargs - no JS knowledge needed #}
{% nitro_switch 'item.status' active='Activo' expired='Vencido' default='Borrador' %}

{# Same for classes #}
<div {% nitro_css 'item.status' active='bg-green-100 text-green-700' expired='bg-red-100' %}></div>
```

## Advanced: Component Methods

For complex logic that can't be expressed with simple mappings:

```python
# In your component
class LeaseList(NitroComponent):
    def get_status_display(self, item):
        if item.expiring_soon:
            return "Por Vencer"
        return {'active': 'Activo', 'expired': 'Vencido'}.get(item.status, 'Borrador')
```

```django
{# In template - call Python method #}
{% nitro_call 'get_status_display' item %}
```

## Migration Guide

If you're upgrading from pre-0.7.0:

| Old Tag (Deprecated) | New Tag (Zero-JS) |
|---------------------|-------------------|
| `{% nitro_bind "x ? 'A' : 'B'" %}` | `{% nitro_switch 'x' true='A' false='B' %}` |
| `{% nitro_class_map "{'cls': cond}" %}` | `{% nitro_css 'field' value='cls' %}` |
| `{% nitro_for 'items' as 'item' %}` | `{% nitro_for 'items' as 'item' %}` |

The old tags still work but are deprecated and will be removed in v1.0.

## Performance: CacheMixin

Add caching to any component for improved performance:

```python
from nitro import CacheMixin, NitroComponent

class ProductList(CacheMixin, NitroComponent[ProductListState]):
    cache_enabled = True
    cache_ttl = 300  # 5 minutes
    cache_html = True  # Also cache rendered HTML

    def get_cache_key_parts(self):
        # Customize cache key (default: component name + user id)
        return [self.request.user.id, self.state.category_filter]
```

For expensive actions:

```python
from nitro.cache import cache_action

class Dashboard(NitroComponent[DashboardState]):
    @cache_action(ttl=120)
    def load_analytics(self):
        # Cached for 2 minutes
        return expensive_analytics_query()
```

## Documentation

- [Component Patterns](./COMPONENTS.md)
- [Changelog](./CHANGELOG.md)

## License

MIT License
