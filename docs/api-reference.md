# API Reference

Complete API reference for Django Nitro v0.6.0+

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
| `toast_enabled` | `bool \| None` | No | Enable/disable toasts (v0.4.0+) |
| `toast_position` | `str \| None` | No | Toast position: `top-right`, `top-left`, `top-center`, `bottom-right`, `bottom-left`, `bottom-center` (v0.4.0+) |
| `toast_duration` | `int \| None` | No | Toast auto-dismiss duration in ms (v0.4.0+) |
| `toast_style` | `str \| None` | No | Toast style: `default`, `minimal`, `bordered` (v0.4.0+) |
| `smart_updates` | `bool` | No | Enable state diffing for large lists (v0.4.0+, default: `False`) |

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
    """Add success message (green toast)."""
    pass

def error(self, message: str) -> None:
    """Add error message (red toast)."""
    pass

def warning(self, message: str) -> None:
    """Add warning message (yellow/orange toast) - v0.4.0+"""
    pass

def info(self, message: str) -> None:
    """Add info message (blue toast)."""
    pass
```

##### Security Helpers

```python
def require_auth(self, message: str = "Authentication required") -> bool:
    """Enforce authentication requirement."""
    pass
```

##### Field Synchronization (v0.5.0+)

```python
def _sync_field(self, field: str, value: Any) -> None:
    """
    Synchronize a single field from client to server state.

    Supports nested fields using dot notation for complex state structures.
    This is used internally for x-model bindings and can be called directly
    for programmatic state updates.

    Args:
        field: Field name, supports dot notation for nested fields
               (e.g., 'name', 'address.city', 'items.0.quantity')
        value: The value to set

    Examples:
        # Simple field
        self._sync_field('username', 'john_doe')

        # Nested field in object
        self._sync_field('profile.email', 'john@example.com')

        # Nested field in list
        self._sync_field('items.0.name', 'Updated Item')

        # Deep nesting
        self._sync_field('order.shipping.address.city', 'New York')
    """
    pass
```

##### File Upload Handling (v0.5.0+)

```python
def _handle_file_upload(self, file: UploadedFile) -> str:
    """
    Handle file upload and return the saved file path.

    Override this method to customize file storage behavior.
    By default, saves files using Django's default storage backend.

    Args:
        file: Django UploadedFile object from request.FILES

    Returns:
        str: Path or URL to the saved file

    Example:
        class DocumentComponent(NitroComponent[DocumentState]):
            def _handle_file_upload(self, file: UploadedFile) -> str:
                # Custom storage logic
                path = f"documents/{self.current_user.id}/{file.name}"
                saved_path = default_storage.save(path, file)
                return default_storage.url(saved_path)

            def upload_document(self, doc_type: str):
                # File is automatically available via self._uploaded_file
                if self._uploaded_file:
                    url = self._handle_file_upload(self._uploaded_file)
                    self.state.documents.append({
                        'type': doc_type,
                        'url': url,
                        'name': self._uploaded_file.name
                    })
                    self.success('Document uploaded successfully')
    """
    pass
```

##### Event Methods (v0.4.0+)

```python
def emit(self, event_name: str, data: dict[str, Any] | None = None) -> None:
    """
    Emit custom DOM event.

    Event name is automatically prefixed with 'nitro:' if not already present.
    Components and JavaScript can listen to these events via window.addEventListener.

    Args:
        event_name: Name of the event (e.g., 'cart-updated')
        data: Optional data payload to include with the event

    Example:
        self.emit('product-deleted', {'product_id': 123})
        # Dispatches 'nitro:product-deleted' event
    """
    pass

def refresh_component(self, component_id: str) -> None:
    """
    Emit refresh event for another component.

    Helper that emits a 'nitro:refresh-{component_id}' event that other
    components can listen to and respond by refreshing their state.

    Args:
        component_id: Name of the component to refresh (e.g., 'ProductList')

    Example:
        self.refresh_component('ProductList')
        # Dispatches 'nitro:refresh-productlist' event
    """
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

# Optional: Nitro configuration (v0.4.0+)
NITRO = {
    # Toast notifications
    'TOAST_ENABLED': True,
    'TOAST_POSITION': 'top-right',  # top-right, top-left, top-center, bottom-right, bottom-left, bottom-center
    'TOAST_DURATION': 3000,  # milliseconds
    'TOAST_STYLE': 'default',  # default, minimal, bordered

    # Debug mode
    'DEBUG': False,
}
```

### Configuration Helpers (v0.4.0+)

```python
from nitro.conf import get_setting, get_all_settings

# Get individual setting with fallback
toast_enabled = get_setting('TOAST_ENABLED')  # Returns True (default)
custom_setting = get_setting('MY_SETTING', default='fallback')

# Get all settings
settings = get_all_settings()
# Returns: {'TOAST_ENABLED': True, 'TOAST_POSITION': 'top-right', ...}
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

**Option A: Using template tag (v0.4.0+, recommended):**

```html
<!-- base.html -->
{% load nitro_tags %}
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
{% nitro_scripts %}  <!-- Loads nitro.css and nitro.js -->
```

**Option B: Manual:**

```html
<!-- base.html -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
<link rel="stylesheet" href="{% static 'nitro/nitro.css' %}">
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

## Template Tags (v0.4.0+)

### nitro_scripts

Load Nitro CSS and JavaScript files.

```html
{% load nitro_tags %}
{% nitro_scripts %}

<!-- Expands to: -->
<link rel="stylesheet" href="/static/nitro/nitro.css">
<script defer src="/static/nitro/nitro.js"></script>
```

### nitro_text

SEO-friendly text binding that renders server-side content with Alpine.js reactivity.

```html
{% load nitro_tags %}

<!-- Renders static value + x-text binding -->
<h1>{% nitro_text 'product.name' %}</h1>

<!-- Output: -->
<h1><span x-text="product.name">Gaming Laptop</span></h1>
```

**Use for:**
- Public content that needs SEO (product listings, blog posts, etc.)
- Maintains reactivity while providing static HTML to crawlers

### nitro_for

SEO-friendly loop that renders static items with Alpine.js reactivity.

```html
{% load nitro_tags %}

{% nitro_for 'products' as 'product' %}
    <div class="card">
        <h3>{% nitro_text 'product.name' %}</h3>
        <p>{% nitro_text 'product.price' %}</p>
    </div>
{% end_nitro_for %}
```

**How it works:**
1. Renders all items statically (SEO)
2. Wraps in hidden div (`x-show="false"`)
3. Adds Alpine `<template x-for>` for reactivity

**Use for:**
- Public product/content listings that need to be indexed by search engines

### nitro_input (v0.6.0+)

Renders an input field with automatic error display and validation styling.

```html
{% load nitro_tags %}

<!-- Text input -->
{% nitro_input 'name' %}

<!-- Email input -->
{% nitro_input 'email' type='email' placeholder='user@example.com' %}

<!-- Number input with attributes -->
{% nitro_input 'age' type='number' min='18' max='100' %}

<!-- Edit buffer support -->
{% nitro_input 'edit_buffer.name' %}
```

**Parameters:**
- `field` (required) - Field name or path (supports nested fields)
- `type` (optional) - Input type (default: `'text'`)
- `placeholder` (optional) - Placeholder text
- `class` (optional) - Additional CSS classes
- `disabled` (optional) - Disable input
- `**attrs` - Any other HTML attributes (e.g., `min`, `max`, `step`)

**Supported Types:**
`text`, `email`, `password`, `number`, `tel`, `url`, `date`, `time`, `datetime-local`, `search`

### nitro_select (v0.6.0+)

Renders a select dropdown with choices and error handling.

```html
{% load nitro_tags %}

<!-- Basic select -->
{% nitro_select 'status' choices=status_choices %}

<!-- With custom class -->
{% nitro_select 'category' choices=categories class='form-select-lg' %}

<!-- Edit buffer support -->
{% nitro_select 'edit_buffer.priority' choices=priority_choices %}
```

**Parameters:**
- `field` (required) - Field name or path
- `choices` (required) - List of dicts with `value` and `label` keys
- `class` (optional) - Additional CSS classes
- `disabled` (optional) - Disable select
- `**attrs` - Any other HTML attributes

**Choices Format:**
```python
choices = [
    {'value': 'option1', 'label': 'Option 1'},
    {'value': 'option2', 'label': 'Option 2'},
]
```

### nitro_textarea (v0.6.0+)

Renders a textarea with error handling.

```html
{% load nitro_tags %}

<!-- Basic textarea -->
{% nitro_textarea 'description' %}

<!-- With rows and placeholder -->
{% nitro_textarea 'notes' rows='5' placeholder='Enter notes...' %}

<!-- Edit buffer support -->
{% nitro_textarea 'edit_buffer.bio' rows='8' %}
```

**Parameters:**
- `field` (required) - Field name or path
- `rows` (optional) - Number of visible rows (default: `3`)
- `placeholder` (optional) - Placeholder text
- `class` (optional) - Additional CSS classes
- `disabled` (optional) - Disable textarea
- `**attrs` - Any other HTML attributes

### nitro_checkbox (v0.6.0+)

Renders a checkbox with label and error handling.

```html
{% load nitro_tags %}

<!-- Basic checkbox -->
{% nitro_checkbox 'is_active' label='Active' %}

<!-- Terms acceptance -->
{% nitro_checkbox 'terms_accepted' label='I agree to terms and conditions' %}

<!-- Edit buffer support -->
{% nitro_checkbox 'edit_buffer.is_featured' label='Featured' %}
```

**Parameters:**
- `field` (required) - Field name or path
- `label` (required) - Label text displayed next to checkbox
- `class` (optional) - Additional CSS classes
- `disabled` (optional) - Disable checkbox
- `**attrs` - Any other HTML attributes

**Note:** All form field tags automatically:
- Bind to Alpine.js using `x-model`
- Display validation errors using `x-show` and `:class`
- Support nested fields with optional chaining
- Use Bootstrap styling classes

---

## CLI Commands (v0.4.0+)

### startnitro

Generate Nitro component boilerplate.

```bash
# Basic component
python manage.py startnitro ComponentName --app myapp

# List component with pagination/search
python manage.py startnitro ProductList --app products --list

# CRUD component
python manage.py startnitro TaskManager --app tasks --crud
```

**Arguments:**
- `ComponentName` - Name of component (must start with uppercase)
- `--app` - Django app name (required)
- `--list` - Generate list component with pagination
- `--crud` - Generate CRUD component (implies `--list`)

**Creates:**
- `{app}/components/{component_name}.py` - Component class
- `{app}/templates/components/{component_name}.html` - Template
- `{app}/components/__init__.py` - Package file (if missing)

---

## DOM Events (v0.4.0+)

Nitro dispatches custom DOM events that you can listen to in JavaScript.

### Built-in Events

**nitro:message** - Dispatched for each message/toast
```javascript
window.addEventListener('nitro:message', (event) => {
    console.log(event.detail);
    // { component: 'MyComponent', level: 'success', text: 'Saved!' }
});
```

**nitro:action-complete** - Dispatched when action succeeds
```javascript
window.addEventListener('nitro:action-complete', (event) => {
    console.log(event.detail);
    // { component: 'MyComponent', action: 'save', state: {...} }
});
```

**nitro:error** - Dispatched when error occurs
```javascript
window.addEventListener('nitro:error', (event) => {
    console.log(event.detail);
    // { component: 'MyComponent', action: 'save', error: '...', status: 500 }
});
```

### Custom Events

Listen to events emitted from Python via `emit()`:

```python
# Python component
class MyComponent(NitroComponent[MyState]):
    def do_action(self):
        self.emit('custom-event', {'data': 'value'})
```

```javascript
// JavaScript
window.addEventListener('nitro:custom-event', (event) => {
    console.log(event.detail);
    // { component: 'MyComponent', data: 'value' }
});
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

print(nitro.__version__)  # "0.6.0"
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

### From `nitro.conf` (v0.4.0+)

```python
from nitro.conf import (
    get_setting,
    get_all_settings,
)
```

---

## See Also

- [Getting Started](getting-started/installation.md)
- [Components Guide](core-concepts/components.md)
- [State Management](core-concepts/state-management.md)
- [Actions Guide](core-concepts/actions.md)
- [Security Overview](security/overview.md)
