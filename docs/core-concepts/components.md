# Components

Components are the building blocks of Django Nitro applications. A component combines server-side Python logic with client-side reactivity using AlpineJS.

## Component Hierarchy

Django Nitro provides three base component classes, each building on the previous one:

```
NitroComponent (Basic)
    ↓
ModelNitroComponent (ORM Integration)
    ↓
CrudNitroComponent (Full CRUD)
    ↓
BaseListComponent (Pagination + Search + Filters)
```

### Choosing the Right Component

| Component | Use When | Features |
|-----------|----------|----------|
| **NitroComponent** | Custom components, forms | Full control over state and actions |
| **ModelNitroComponent** | Single model instance | Automatic model loading, `refresh()` |
| **CrudNitroComponent** | List with CRUD operations | Pre-built create, edit, delete methods |
| **BaseListComponent** | Paginated lists | Pagination, search, filters + CRUD |

## Component Anatomy

Every Nitro component consists of:

### 1. State Class (Pydantic Model)

Defines the component's data structure with type safety:

```python
from pydantic import BaseModel

class CounterState(BaseModel):
    count: int = 0
    step: int = 1
```

### 2. Component Class

The Python logic that handles state and actions:

```python
from nitro.base import NitroComponent
from nitro.registry import register_component

@register_component
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    # state_class auto-inferred from Generic (v0.7.0)

    def get_initial_state(self, **kwargs):
        return CounterState(
            count=kwargs.get('initial', 0),
            step=kwargs.get('step', 1)
        )

    def increment(self):
        self.state.count += self.state.step
```

### 3. Template

HTML with Nitro template tags and AlpineJS directives for reactivity:

```html
{% load nitro_tags %}

<div class="counter">
    <h2>Count: {% nitro_text 'count' %}</h2>
    <button @click="call('increment')">+</button>
</div>
```

## Component Registration

Components must be registered to be accessible:

```python
from nitro.registry import register_component

@register_component
class MyComponent(NitroComponent[MyState]):
    # ...
```

The `@register_component` decorator:
- Makes the component discoverable by the API
- Uses the class name as the component identifier
- Must be applied to all components

## Component Lifecycle

1. **Initialization**: `__init__(request, **kwargs)`
   - Component is instantiated
   - Request object is attached
   - Kwargs are stored

2. **State Creation**: `get_initial_state(**kwargs)`
   - Called to create initial state
   - Receives the kwargs from initialization
   - Returns a Pydantic model instance

3. **Rendering**: `render()`
   - State is serialized to JSON
   - Template is rendered with state
   - AlpineJS makes it reactive

4. **Action Calls**: `call('action_name', params)`
   - User triggers action from template
   - State is sent to server
   - Action method is executed
   - Updated state is returned
   - AlpineJS updates the UI

## Component Properties

### Required Properties

```python
class MyComponent(NitroComponent[MyState]):
    template_name = "components/my_component.html"  # Required
    # state_class auto-inferred from Generic[MyState] (v0.7.0)
```

### Optional Properties

```python
class MyComponent(NitroComponent[MyState]):
    secure_fields = ['id', 'price']  # Fields protected from tampering
    model = MyModel  # Django model (for ModelNitroComponent)
```

## Component Methods

### Standard Methods

```python
def get_initial_state(self, **kwargs):
    """Create and return the initial state."""
    return MyState(**kwargs)

def refresh(self):
    """Reload state from database (override as needed)."""
    # Custom refresh logic
```

### Message Methods

```python
def success(self, message: str):
    """Add success message."""

def error(self, message: str):
    """Add error message."""

def info(self, message: str):
    """Add info message."""
```

### Utility Methods

```python
def get_object(self, pk):
    """Get model instance by primary key (ModelNitroComponent)."""
    return self.model.objects.get(pk=pk)
```

## Component Context

Every component has access to:

```python
class MyComponent(NitroComponent[MyState]):
    def my_action(self):
        # Request object
        self.request.user
        self.request.GET
        self.request.POST

        # Current state
        self.state.field_name

        # Component methods
        self.success("Message")
        self.refresh()

        # Security helpers (v0.3.0+)
        self.current_user
        self.is_authenticated
        self.require_auth("Please log in")
```

## Component Initialization

### In Django Views

```python
from django.shortcuts import render
from myapp.components import MyComponent

def my_view(request):
    component = MyComponent(
        request=request,
        initial_value=10,
        mode="edit"
    )
    return render(request, 'page.html', {'component': component})
```

### In Templates

```django
{% extends "base.html" %}

{% block content %}
    <h1>My Page</h1>
    {{ component.render }}
{% endblock %}
```

## Nested Components

Components can be nested for complex UIs:

```python
def property_detail(request, pk):
    property_comp = PropertyDetail(request=request, pk=pk)
    tenant_list = TenantList(request=request, property_id=pk)

    return render(request, 'property_detail.html', {
        'property': property_comp,
        'tenants': tenant_list
    })
```

```django
<div class="property-detail">
    {{ property.render }}

    <div class="tenants">
        {{ tenants.render }}
    </div>
</div>
```

## Best Practices

### 1. Keep Components Focused

Each component should have a single responsibility:

```python
# ✅ Good - focused component
class TaskList(CrudNitroComponent[TaskListState]):
    model = Task
    # Handles task CRUD only

# ❌ Avoid - too much responsibility
class Dashboard(NitroComponent[DashboardState]):
    # Handles tasks, users, analytics, settings...
```

### 2. Use Appropriate Base Class

Choose the simplest component that meets your needs:

```python
# ✅ Good - using BaseListComponent for lists
class ProductList(BaseListComponent[ProductListState]):
    model = Product
    search_fields = ['name']

# ❌ Avoid - reinventing pagination in NitroComponent
class ProductList(NitroComponent[ProductListState]):
    def next_page(self):
        # Implementing pagination from scratch...
```

### 3. Validate Input

Always validate user input in action methods:

```python
def update_price(self, new_price: float):
    if new_price < 0:
        self.error("Price cannot be negative")
        return

    if new_price > 1000000:
        self.error("Price too high")
        return

    # Update price...
```

### 4. Handle Errors Gracefully

```python
def save_item(self):
    try:
        # Save logic...
        self.success("Saved successfully")
    except ValidationError as e:
        self.error(f"Validation error: {e}")
    except Exception as e:
        logger.exception("Save failed")
        self.error("An error occurred. Please try again.")
```

## Next Steps

- [State Management](state-management.md) - Learn about managing component state
- [Actions](actions.md) - Deep dive into component actions
- [Component Reference](../components/nitro-component.md) - Detailed API documentation
