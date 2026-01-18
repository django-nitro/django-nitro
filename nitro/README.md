# Django Nitro v0.7.0

**Reactive Components for Django with Alpine.js**

Nitro brings the simplicity of Livewire-style reactive components to Django, using Alpine.js for the frontend and Pydantic for state management.

## Features

- **Zero JavaScript Required** - Write Python, get reactive UIs
- **Pydantic State Management** - Type-safe, validated component state
- **Server-Side Rendering** - SEO-friendly with hydration
- **Alpine.js Integration** - Seamless client-side reactivity
- **Django Template Tags** - Clean, declarative syntax
- **Multi-tenant Ready** - Built-in security mixins
- **CRUD Components** - Ready-to-use list and form components

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
# components/counter.py
from pydantic import BaseModel
from nitro import NitroComponent, register_component

class CounterState(BaseModel):
    count: int = 0

@register_component
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    state_class = CounterState

    def increment(self):
        self.state.count += 1

    def decrement(self):
        self.state.count -= 1
```

### 3. Create the Template

```django
<!-- templates/components/counter.html -->
{% load nitro_tags %}

<div class="p-4 bg-white rounded shadow">
    <h2 class="text-xl font-bold">Counter: {% nitro_text 'count' %}</h2>

    <div class="flex gap-2 mt-4">
        <button {% nitro_action 'decrement' %} class="btn">-</button>
        <button {% nitro_action 'increment' %} class="btn">+</button>
    </div>
</div>
```

### 4. Use in Your Page

```django
{% load nitro_tags %}
<!DOCTYPE html>
<html>
<head>
    {% nitro_scripts %}
</head>
<body>
    {% nitro_component 'Counter' %}
</body>
</html>
```

## Template Tags

### Core Tags

| Tag | Description |
|-----|-------------|
| `{% nitro_component 'Name' %}` | Render a component |
| `{% nitro_action 'method' %}` | Button action binding |
| `{% nitro_model 'field' %}` | Two-way data binding |
| `{% nitro_text 'field' %}` | Display reactive text |
| `{% nitro_show 'condition' %}` | Conditional visibility |

### New in v0.7.0

| Tag | Description |
|-----|-------------|
| `{% nitro_class_map '...' %}` | Conditional CSS classes |
| `{% nitro_bind 'expr' %}` | Text binding for expressions |
| `{% nitro_if 'cond' %}...{% end_nitro_if %}` | Conditional blocks |
| `{% nitro_for 'list' as 'item' %}...{% end_nitro_for %}` | Loop with reactivity |

### Form Tags

| Tag | Description |
|-----|-------------|
| `{% nitro_input %}` | Text input with validation |
| `{% nitro_select %}` | Dropdown select |
| `{% nitro_textarea %}` | Text area |
| `{% nitro_checkbox %}` | Checkbox input |
| `{% nitro_file %}` | File upload |

## Component Types

### NitroComponent

Base component for custom reactive UIs.

```python
from nitro import NitroComponent, register_component

@register_component
class MyComponent(NitroComponent[MyState]):
    template_name = "my_component.html"
    state_class = MyState
```

### BaseListComponent

Pre-built CRUD list with pagination, search, and filtering.

```python
from nitro import BaseListComponent, register_component

@register_component
class PropertyList(BaseListComponent):
    model = Property
    template_name = "properties/list.html"
    per_page = 10
```

## Security Mixins

```python
from nitro.security import OwnershipMixin, TenantScopedMixin

class MyComponent(TenantScopedMixin, NitroComponent):
    # Automatically filters by tenant/company
    pass
```

## Configuration

```python
# settings.py
NITRO = {
    'DEBUG': True,  # Enable debug mode
    'CSRF_CHECK': True,  # Enable CSRF validation
    'TEMPLATE_DIR': 'nitro/templates',
}
```

## Documentation

- [Components Documentation](./COMPONENTS.md)
- [Changelog](./CHANGELOG.md)

## License

MIT License
