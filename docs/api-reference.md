# API Reference

Complete API reference for Django Nitro v0.3.0+

## Core Components

### NitroComponent

Base class for all Django Nitro components.

```python
from nitro.base import NitroComponent
```

#### Class Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_name` | `str` | Yes | Path to component template |
| `state_class` | `Type[BaseModel]` | Yes | Pydantic state model |
| `secure_fields` | `list[str]` | No | Fields protected from tampering |
| `model` | `Type[Model]` | No | Django model (for ModelNitroComponent) |

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `request` | `HttpRequest` | Django request object |
| `state` | `BaseModel` | Current component state |
| `current_user` | `User \| None` | Authenticated user or None |
| `is_authenticated` | `bool` | True if user is authenticated |

#### Methods

##### Lifecycle Methods

```python
def get_initial_state(self, **kwargs) -> BaseModel:
    """Create and return initial state."""
    pass

def refresh(self) -> None:
    """Reload component state."""
    pass

def render(self) -> str:
    """Render component as HTML."""
    pass
```

##### Message Methods

```python
def success(self, message: str) -> None:
    """Add success message."""
    pass

def error(self, message: str) -> None:
    """Add error message."""
    pass

def info(self, message: str) -> None:
    """Add info message."""
    pass
```

##### Security Helpers

```python
def require_auth(self, message: str = "Authentication required") -> bool:
    """Enforce authentication requirement."""
    pass
```

---

### ModelNitroComponent

Extends `NitroComponent` with Django ORM integration.

```python
from nitro.base import ModelNitroComponent
```

#### Additional Class Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | `Type[Model]` | Yes | Django model class |

#### Additional Methods

```python
def get_object(self, pk: int) -> Model:
    """Get model instance by primary key."""
    pass

def refresh(self) -> None:
    """Reload state from database using current id."""
    pass
```

---

### CrudNitroComponent

Extends `ModelNitroComponent` with CRUD operations.

```python
from nitro.base import CrudNitroComponent
```

#### State Requirements

Your state class should include:

```python
class MyState(BaseModel):
    items: list[ItemSchema] = []
    create_buffer: ItemFormSchema = Field(default_factory=ItemFormSchema)
    edit_buffer: Optional[ItemFormSchema] = None
    editing_id: Optional[int] = None
```

#### Pre-built Methods

```python
def create_item(self) -> None:
    """Create item from create_buffer."""
    pass

def start_edit(self, id: int) -> None:
    """Start editing item."""
    pass

def save_edit(self) -> None:
    """Save changes from edit_buffer."""
    pass

def cancel_edit(self) -> None:
    """Cancel editing mode."""
    pass

def delete_item(self, id: int) -> None:
    """Delete item by ID."""
    pass
```

---

### BaseListComponent

Extends `CrudNitroComponent` with pagination, search, and filters.

```python
from nitro.list import BaseListComponent
```

#### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_fields` | `list[str]` | `[]` | Fields to search across |
| `per_page` | `int` | `20` | Items per page |
| `order_by` | `str` | `'-id'` | Default ordering |

#### State Requirements

```python
from nitro.list import BaseListState

class MyListState(BaseListState):
    items: list[ItemSchema] = []
    # Inherited: search, page, per_page, total_count, num_pages,
    #            has_next, has_previous, showing_start, showing_end, filters

    # REQUIRED: Override buffer types
    create_buffer: ItemFormSchema = Field(default_factory=ItemFormSchema)
    edit_buffer: Optional[ItemFormSchema] = None
```

#### Methods

##### Pagination

```python
def next_page(self) -> None:
    """Go to next page."""
    pass

def previous_page(self) -> None:
    """Go to previous page."""
    pass

def go_to_page(self, page: int) -> None:
    """Go to specific page."""
    pass

def set_per_page(self, per_page: int) -> None:
    """Change items per page."""
    pass
```

##### Search & Filters

```python
def search_items(self, search: str) -> None:
    """Search and reset to page 1."""
    pass

def set_filters(self, **filters) -> None:
    """Apply filters and reset to page 1."""
    pass

def clear_filters(self) -> None:
    """Clear all filters and search."""
    pass
```

##### Query Building

```python
def get_base_queryset(self, search='', filters=None) -> QuerySet:
    """Override for custom queryset logic."""
    pass

def apply_search(self, queryset: QuerySet, search: str) -> QuerySet:
    """Apply search across search_fields."""
    pass

def apply_filters(self, queryset: QuerySet, filters: dict) -> QuerySet:
    """Apply filter dict to queryset."""
    pass
```

---

## Security Mixins

### OwnershipMixin

Filter querysets to current user's data.

```python
from nitro.security import OwnershipMixin
```

#### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `owner_field` | `str` | `'user'` | ForeignKey field linking to User |

#### Methods

```python
def filter_by_owner(self, queryset: QuerySet) -> QuerySet:
    """Filter to current user's items."""
    pass
```

---

### TenantScopedMixin

Multi-tenant data isolation.

```python
from nitro.security import TenantScopedMixin
```

#### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `tenant_field` | `str` | `'organization'` | ForeignKey field linking to tenant |

#### Methods

```python
def get_user_tenant(self) -> Model:
    """REQUIRED: Return current user's tenant."""
    raise NotImplementedError

def filter_by_tenant(self, queryset: QuerySet) -> QuerySet:
    """Filter to current tenant's items."""
    pass
```

---

### PermissionMixin

Custom permission logic framework.

```python
from nitro.security import PermissionMixin
```

#### Methods

```python
def check_permission(self, action: str) -> bool:
    """REQUIRED: Return True if action allowed."""
    raise NotImplementedError

def enforce_permission(
    self,
    action: str,
    error_message: Optional[str] = None
) -> bool:
    """Check permission and show error if denied."""
    pass
```

---

## Mixins

### PaginationMixin

Django Paginator integration.

```python
from nitro.list import PaginationMixin
```

#### Methods

```python
def paginate_queryset(
    self,
    queryset: QuerySet,
    page: int = 1,
    per_page: int = 20
) -> dict:
    """
    Paginate queryset.

    Returns:
        {
            'items': [...],
            'page': 1,
            'per_page': 20,
            'total_count': 100,
            'num_pages': 5,
            'has_next': True,
            'has_previous': False,
            'showing_start': 1,
            'showing_end': 20
        }
    """
    pass
```

---

### SearchMixin

Full-text search across fields.

```python
from nitro.list import SearchMixin
```

#### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `search_fields` | `list[str]` | `[]` | Fields to search |

#### Methods

```python
def apply_search(self, queryset: QuerySet, search_query: str) -> QuerySet:
    """Apply OR search across search_fields."""
    pass
```

---

### FilterMixin

Dynamic queryset filtering.

```python
from nitro.list import FilterMixin
```

#### Methods

```python
def apply_filters(self, queryset: QuerySet, filters: dict) -> QuerySet:
    """
    Apply filters to queryset.
    Removes empty values and applies remaining filters.
    """
    pass
```

---

## State Classes

### BaseListState

Pre-built state for list components with pagination.

```python
from nitro.list import BaseListState
```

#### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `items` | `list[Any]` | `[]` | Override with specific type |
| `search` | `str` | `""` | Current search query |
| `page` | `int` | `1` | Current page number |
| `per_page` | `int` | `20` | Items per page |
| `total_count` | `int` | `0` | Total items (all pages) |
| `num_pages` | `int` | `0` | Total number of pages |
| `has_next` | `bool` | `False` | Has next page |
| `has_previous` | `bool` | `False` | Has previous page |
| `showing_start` | `int` | `0` | First item index |
| `showing_end` | `int` | `0` | Last item index |
| `filters` | `dict` | `{}` | Active filters |
| `create_buffer` | `Any` | `None` | Override with specific type |
| `edit_buffer` | `Optional[Any]` | `None` | Override with specific type |
| `editing_id` | `Optional[int]` | `None` | ID being edited |

---

## Registry

### register_component

Decorator to register components.

```python
from nitro.registry import register_component

@register_component
class MyComponent(NitroComponent[MyState]):
    pass
```

---

## Template Variables

All component templates have access to:

### State Properties

All fields from your state class:

```html
<div x-text="field_name"></div>
```

### Built-in Properties

| Variable | Type | Description |
|----------|------|-------------|
| `isLoading` | `bool` | True during action calls |
| `errors` | `object` | Validation errors per field |
| `messages` | `array` | Success/error/info messages |

### Message Structure

```javascript
{
  text: "Message text",
  level: "success" | "error" | "info"
}
```

### Error Structure

```javascript
{
  field_name: "Error message for this field"
}
```

---

## Template Methods

### call()

Call a component action.

```javascript
call(actionName: string, params?: object, file?: File)
```

**Examples:**

```html
<!-- Simple call -->
<button @click="call('increment')">+</button>

<!-- With parameters -->
<button @click="call('add', {amount: 5})">+5</button>

<!-- With file upload -->
<input
  type="file"
  @change="call('upload', {doc_id: 123}, $event.target.files[0])"
>
```

---

## AlpineJS Integration

### Directives Used

| Directive | Purpose | Example |
|-----------|---------|---------|
| `x-text` | Display text | `<div x-text="count"></div>` |
| `x-html` | Display HTML | `<div x-html="content"></div>` |
| `x-model` | Two-way binding | `<input x-model="name">` |
| `x-show` | Toggle visibility | `<div x-show="isLoading">` |
| `x-if` | Conditional render | `<template x-if="count > 0">` |
| `x-for` | Loop | `<template x-for="item in items">` |
| `@click` | Click handler | `<button @click="call('action')">` |
| `:disabled` | Bind attribute | `<button :disabled="isLoading">` |
| `:class` | Bind classes | `<div :class="{'active': isActive}">` |

### Event Modifiers

```html
<!-- Prevent default -->
<form @submit.prevent="call('submit')">

<!-- Debounce -->
<input @input.debounce.300ms="call('search')">

<!-- Key modifiers -->
<input @keyup.enter="call('submit')">
<input @keyup.escape="call('cancel')">

<!-- Stop propagation -->
<button @click.stop="call('action')">
```

---

## Configuration

### Settings

Add to Django settings:

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'nitro',
]

# Optional: Debug mode for Nitro
NITRO_DEBUG = DEBUG
```

### URLs

```python
# urls.py
from nitro.api import api

urlpatterns = [
    # ...
    path("api/nitro/", api.urls),
]
```

### Static Files

```html
<!-- base.html -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
<script src="{% static 'nitro/nitro.js' %}"></script>
```

### Debug Mode

```html
<!-- Enable debug logging -->
<script>
    window.NITRO_DEBUG = true;
</script>
<script src="{% static 'nitro/nitro.js' %}"></script>
```

---

## Type Hints

### Generic Types

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class MyComponent(NitroComponent[T]):
    state_class: Type[T]
```

### State Type Hints

```python
from typing import Optional, List
from pydantic import BaseModel, Field

class MyState(BaseModel):
    items: List[ItemSchema] = Field(default_factory=list)
    selected_id: Optional[int] = None
    is_loading: bool = False
```

---

## Version Information

```python
import nitro

print(nitro.__version__)  # "0.3.0"
```

---

## Exports

### From `nitro.base`

```python
from nitro.base import (
    NitroComponent,
    ModelNitroComponent,
    CrudNitroComponent,
)
```

### From `nitro.list`

```python
from nitro.list import (
    BaseListComponent,
    BaseListState,
    PaginationMixin,
    SearchMixin,
    FilterMixin,
)
```

### From `nitro.security`

```python
from nitro.security import (
    OwnershipMixin,
    TenantScopedMixin,
    PermissionMixin,
)
```

### From `nitro.registry`

```python
from nitro.registry import (
    register_component,
)
```

---

## See Also

- [Getting Started](getting-started/installation.md)
- [Components Guide](core-concepts/components.md)
- [State Management](core-concepts/state-management.md)
- [Actions Guide](core-concepts/actions.md)
- [Security Overview](security/overview.md)
