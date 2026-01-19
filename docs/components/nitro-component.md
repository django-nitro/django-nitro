# NitroComponent

`NitroComponent` is the base class for all Django Nitro components. It provides the foundation for creating reactive, stateful components with full control over state and actions.

## When to Use

Use `NitroComponent` when you need:

- **Full control** over state structure and initialization
- **Custom components** that don't map directly to Django models
- **Complex forms** with custom validation logic
- **Widgets** like counters, calculators, or interactive UI elements

## Basic Structure

```python
from pydantic import BaseModel
from nitro.base import NitroComponent
from nitro.registry import register_component

# 1. Define state schema
class MyComponentState(BaseModel):
    field1: str = ""
    field2: int = 0

# 2. Create component class
@register_component
class MyComponent(NitroComponent[MyComponentState]):
    template_name = "components/my_component.html"
    # state_class auto-inferred from Generic type (v0.7.0)

    def get_initial_state(self, **kwargs):
        return MyComponentState(
            field1=kwargs.get('field1', ''),
            field2=kwargs.get('field2', 0)
        )

    def my_action(self):
        # Your action logic
        self.state.field2 += 1
```

## v0.7.0 DX Improvements

Version 0.7.0 introduces several developer experience improvements that reduce boilerplate and make components more concise.

### Auto-Infer `state_class`

The `state_class` is now automatically inferred from the Generic type parameter:

```python
# Before v0.7.0 - REDUNDANT declaration
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    state_class = CounterState  # Had to repeat the type!

# v0.7.0+ - Auto-inferred
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    # state_class is automatically set to CounterState
```

**When you still need explicit `state_class`:**

```python
# 1. Without Generic type parameter
class LegacyComponent(NitroComponent):
    state_class = LegacyState  # Required - no Generic to infer from

# 2. Override inferred type (rare - for subclass usage)
class SpecialComponent(NitroComponent[BaseState]):
    state_class = ExtendedState  # Use ExtendedState instead of BaseState
```

### Auto-Infer `template_name`

Template names can be auto-inferred by convention:

```python
# File: leasing/components/tenant_list.py
class TenantList(NitroComponent[TenantState]):
    # template_name auto-inferred: leasing/components/tenant_list.html
    pass

# Convention: {app_name}/components/{class_name_snake_case}.html
# Examples:
#   properties.components.PropertyDetail -> properties/components/property_detail.html
#   myapp.components.UserProfileEditor -> myapp/components/user_profile_editor.html
```

**Note:** Explicit `template_name` always takes precedence over the inferred value.

### Optional `get_initial_state()`

If your state class has sensible defaults, you can skip `get_initial_state()` entirely:

```python
class CounterState(BaseModel):
    count: int = 0
    step: int = 1

@register_component
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    # No get_initial_state() needed!
    # Automatically creates CounterState(count=0, step=1)

    def increment(self):
        self.state.count += self.state.step
```

**When you still need `get_initial_state()`:**

```python
class Counter(NitroComponent[CounterState]):
    def get_initial_state(self, **kwargs):
        # Use kwargs from component initialization
        return CounterState(
            count=kwargs.get('initial', 0),
            step=kwargs.get('step', 1)
        )

# Usage: Counter(request=request, initial=10, step=5)
```

### `as_view()` - Direct URL Routing

Create Django views directly from components without separate view functions:

```python
# urls.py
from django.urls import path
from myapp.components import Counter, ContactForm, Dashboard

urlpatterns = [
    # Standard usage - component renders in default template
    path('counter/', Counter.as_view(), name='counter'),

    # Custom template wrapper
    path('contact/', ContactForm.as_view(
        template_name='pages/contact.html'
    ), name='contact'),

    # Pass initialization kwargs
    path('dashboard/', Dashboard.as_view(
        initial_tab='analytics',
        show_sidebar=True
    ), name='dashboard'),
]
```

**Default template (`nitro/component_page.html`):**

```html
{% extends "base.html" %}
{% block content %}
    {{ component.render }}
{% endblock %}
```

### Lifecycle Hooks

Intercept field updates with `updating()` and `updated()` hooks:

#### `updating(field, value) -> bool`

Called **before** a field is updated via `x-model` or `_sync_field`. Return `False` to cancel the update.

```python
class PriceEditor(NitroComponent[PriceState]):
    def updating(self, field: str, value) -> bool:
        """Validate before update. Return False to cancel."""
        if field == 'price':
            if value < 0:
                self.error("Price cannot be negative")
                return False
            if value > 1000000:
                self.error("Price exceeds maximum allowed")
                return False

        if field == 'discount_percent':
            if value < 0 or value > 100:
                self.error("Discount must be between 0-100%")
                return False

        return True  # Allow update
```

#### `updated(field, value) -> None`

Called **after** a field is successfully updated. Use for side effects, logging, or emitting events.

```python
class OrderEditor(NitroComponent[OrderState]):
    def updated(self, field: str, value) -> None:
        """React to successful field updates."""
        if field == 'status':
            # Emit event for other components
            self.emit('order-status-changed', {
                'order_id': self.state.id,
                'new_status': value
            })

            # Log the change
            logger.info(f"Order {self.state.id} status changed to {value}")

        if field == 'quantity':
            # Recalculate totals
            self.state.total = self.state.quantity * self.state.unit_price
```

#### Combined Example

```python
class InventoryItem(NitroComponent[InventoryState]):
    def updating(self, field: str, value) -> bool:
        if field == 'quantity':
            if value < 0:
                self.error("Quantity cannot be negative")
                return False
            if value > self.state.max_stock:
                self.error(f"Cannot exceed max stock of {self.state.max_stock}")
                return False
        return True

    def updated(self, field: str, value) -> None:
        if field == 'quantity':
            # Check low stock warning
            if value <= self.state.reorder_point:
                self.info(f"Low stock alert: {value} units remaining")
                self.emit('low-stock', {'sku': self.state.sku, 'quantity': value})
```

### Minimal Component Example

With all v0.7.0 improvements, a component can be extremely concise:

```python
from pydantic import BaseModel
from nitro import NitroComponent, register_component

class CounterState(BaseModel):
    count: int = 0

@register_component
class Counter(NitroComponent[CounterState]):
    # template_name inferred: {app}/components/counter.html
    # state_class inferred: CounterState
    # get_initial_state() not needed - uses defaults

    def increment(self):
        self.state.count += 1

    def decrement(self):
        self.state.count -= 1
```

That's a fully functional reactive component in just 12 lines of Python!

## Class Attributes

### Required (Pre-v0.7.0) / Optional (v0.7.0+)

```python
template_name: str = ""
```
Path to the component's HTML template.

**v0.7.0+**: Auto-inferred from module path and class name if not specified. See [Auto-Infer `template_name`](#auto-infer-template_name) above.

```python
state_class: Type[BaseModel] = None
```
Pydantic model class defining the component's state structure.

**v0.7.0+**: Auto-inferred from the Generic type parameter. See [Auto-Infer `state_class`](#auto-infer-state_class) above.

### Optional

```python
secure_fields: list[str] = []
```
List of field names to protect from client-side tampering using integrity verification.

```python
model: Type[Model] = None
```
Django model class (used by `ModelNitroComponent` and its subclasses).

## Methods

### Lifecycle Methods

#### `get_initial_state(**kwargs) -> BaseModel`

Creates and returns the initial state for the component.

**Parameters:**
- `**kwargs` - Arguments passed during component initialization

**Returns:**
- Instance of `state_class`

**Example:**
```python
def get_initial_state(self, **kwargs):
    return MyComponentState(
        name=kwargs.get('name', ''),
        count=kwargs.get('initial_count', 0),
        mode=kwargs.get('mode', 'view')
    )
```

#### `refresh() -> None`

Reloads component state (e.g., from database). Override for custom refresh logic.

**Default behavior:**
- Does nothing in base `NitroComponent`
- Subclasses override for specific refresh logic

**Example:**
```python
def refresh(self):
    # Reload data from external API
    data = fetch_from_api(self.state.api_key)
    self.state.data = data
```

### Message Methods

#### `success(message: str) -> None`

Adds a success message to be displayed to the user.

```python
self.success("Operation completed successfully!")
```

#### `error(message: str) -> None`

Adds an error message to be displayed to the user.

```python
self.error("Something went wrong. Please try again.")
```

#### `info(message: str) -> None`

Adds an informational message to be displayed to the user.

```python
self.info("Your session will expire in 5 minutes.")
```

### Security Helpers

#### `current_user -> User | None`

Property that returns the current authenticated user or `None`.

```python
@property
def current_user(self):
    if self.request and self.request.user.is_authenticated:
        return self.request.user
    return None
```

**Usage:**
```python
def my_action(self):
    user = self.current_user
    if user:
        # Do something with authenticated user
        pass
```

#### `is_authenticated -> bool`

Property that returns `True` if the user is authenticated.

```python
@property
def is_authenticated(self):
    return self.request and self.request.user.is_authenticated
```

**Usage:**
```python
def delete_account(self):
    if not self.is_authenticated:
        self.error("Authentication required")
        return
```

#### `require_auth(message: str = "Authentication required") -> bool`

Enforces authentication requirement. Shows error message and returns `False` if not authenticated.

```python
def require_auth(self, message: str = "Authentication required") -> bool:
    if not self.is_authenticated:
        self.error(message)
        return False
    return True
```

**Usage:**
```python
def save_profile(self):
    if not self.require_auth("Please log in to save your profile"):
        return  # Stops execution

    # Continue with authenticated user
    self.current_user.profile.save()
```

### Rendering Methods

#### `render() -> str`

Renders the component as HTML with embedded state.

**Returns:**
- HTML string with AlpineJS bindings

**Usage in templates:**
```django
{{ component.render }}
```

### Internal Methods

These methods are used internally and rarely need to be overridden:

#### `_get_secure_fields() -> list[str]`

Returns list of fields to protect with integrity verification.

#### `_compute_integrity() -> str`

Computes HMAC integrity token for secure fields.

#### `_verify_integrity(integrity: str) -> bool`

Verifies integrity token matches current secure field values.

## Properties

### `request: HttpRequest`

Django request object, available in all methods.

```python
def my_action(self):
    user = self.request.user
    session = self.request.session
    get_params = self.request.GET
```

### `state: BaseModel`

Current component state (instance of `state_class`).

```python
def increment(self):
    self.state.count += 1
```

## Complete Example

Here's a complete example of a contact form component:

```python
from pydantic import BaseModel, EmailStr, validator
from nitro.base import NitroComponent
from nitro.registry import register_component
from typing import Optional

# State schema
class ContactFormState(BaseModel):
    name: str = ""
    email: EmailStr | str = ""
    subject: str = ""
    message: str = ""
    submitted: bool = False

    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name is required')
        return v.strip()

    @validator('message')
    def message_min_length(cls, v):
        if len(v) < 10:
            raise ValueError('Message too short (min 10 characters)')
        return v

# Component
@register_component
class ContactForm(NitroComponent[ContactFormState]):
    template_name = "components/contact_form.html"
    # state_class auto-inferred from Generic (v0.7.0)

    def get_initial_state(self, **kwargs):
        return ContactFormState()

    def submit(self):
        """Handle form submission."""
        # Check authentication (optional)
        if not self.is_authenticated:
            self.error("Please log in to send a message")
            return

        # Validate
        if not self.state.name or not self.state.message:
            self.error("Please fill in all required fields")
            return

        # Send email
        try:
            send_contact_email(
                name=self.state.name,
                email=self.state.email,
                subject=self.state.subject,
                message=self.state.message,
                user=self.current_user
            )

            # Mark as submitted
            self.state.submitted = True
            self.success("Message sent successfully! We'll get back to you soon.")

        except Exception as e:
            logger.exception("Contact form submission failed")
            self.error("Failed to send message. Please try again later.")

    def reset(self):
        """Reset form to initial state."""
        self.state.name = ""
        self.state.email = ""
        self.state.subject = ""
        self.state.message = ""
        self.state.submitted = False
        self.info("Form cleared")
```

**Template (`components/contact_form.html`):**

```html
<div class="contact-form">
    <!-- Show form if not submitted -->
    <form x-show="!submitted" @submit.prevent="call('submit')">
        <div class="form-group">
            <label for="name">Name *</label>
            <input
                id="name"
                x-model="name"
                type="text"
                :class="{'error': errors.name}"
                required
            >
            <span x-show="errors.name" x-text="errors.name" class="error-text"></span>
        </div>

        <div class="form-group">
            <label for="email">Email *</label>
            <input
                id="email"
                x-model="email"
                type="email"
                :class="{'error': errors.email}"
                required
            >
            <span x-show="errors.email" x-text="errors.email" class="error-text"></span>
        </div>

        <div class="form-group">
            <label for="subject">Subject</label>
            <input
                id="subject"
                x-model="subject"
                type="text"
            >
        </div>

        <div class="form-group">
            <label for="message">Message *</label>
            <textarea
                id="message"
                x-model="message"
                rows="5"
                :class="{'error': errors.message}"
                required
            ></textarea>
            <span x-show="errors.message" x-text="errors.message" class="error-text"></span>
        </div>

        <div class="form-actions">
            <button type="submit" :disabled="isLoading">
                <span x-show="!isLoading">Send Message</span>
                <span x-show="isLoading">Sending...</span>
            </button>
            <button type="button" @click="call('reset')" :disabled="isLoading">
                Reset
            </button>
        </div>
    </form>

    <!-- Success message -->
    <div x-show="submitted" class="success-panel">
        <h3>Thank you!</h3>
        <p>Your message has been sent. We'll respond as soon as possible.</p>
        <button @click="call('reset')">Send Another Message</button>
    </div>

    <!-- Messages -->
    <template x-for="msg in messages" :key="msg.text">
        <div
            :class="'alert alert-' + msg.level"
            x-text="msg.text"
        ></div>
    </template>
</div>
```

**Usage in view:**

```python
from django.shortcuts import render
from myapp.components import ContactForm

def contact_page(request):
    form = ContactForm(request=request)
    return render(request, 'contact.html', {'form': form})
```

## Best Practices

### 1. Use Type Hints

```python
from typing import Optional

def update_field(self, value: str) -> None:
    self.state.field = value
```

### 2. Validate Input

```python
def set_age(self, age: int):
    if age < 0 or age > 150:
        self.error("Invalid age")
        return

    self.state.age = age
```

### 3. Handle Errors

```python
def save(self):
    try:
        # Save logic
        self.success("Saved")
    except ValidationError as e:
        self.error(f"Validation error: {e}")
    except Exception:
        logger.exception("Save failed")
        self.error("An error occurred")
```

### 4. Keep Actions Small

```python
# ✅ Good - focused actions
def increment(self):
    self.state.count += 1

def decrement(self):
    self.state.count -= 1

# ❌ Avoid - too complex
def manage_counter(self, operation: str):
    if operation == 'inc':
        # ...
    elif operation == 'dec':
        # ...
    # Too much logic in one action
```

### 5. Document Your Component

```python
@register_component
class Calculator(NitroComponent[CalculatorState]):
    """
    Interactive calculator component.

    Supports basic arithmetic operations: +, -, *, /

    Usage:
        calculator = Calculator(request=request, initial=0)
    """
    template_name = "components/calculator.html"
    # state_class auto-inferred from Generic type (v0.7.0)
```

---

## CacheMixin (v0.7.0)

Add component-level caching to improve performance for frequently accessed components.

### Basic Usage

```python
from nitro import CacheMixin, NitroComponent, register_component

@register_component
class ProductList(CacheMixin, NitroComponent[ProductListState]):
    template_name = "components/product_list.html"

    # Cache configuration
    cache_enabled = True
    cache_ttl = 300  # 5 minutes
    cache_html = True  # Also cache rendered HTML
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cache_enabled` | bool | False | Enable/disable caching |
| `cache_ttl` | int | 300 | Cache time-to-live in seconds |
| `cache_html` | bool | False | Cache rendered HTML in addition to state |

### Custom Cache Keys

Override `get_cache_key_parts()` to customize the cache key:

```python
class ProductList(CacheMixin, NitroComponent[ProductListState]):
    cache_enabled = True

    def get_cache_key_parts(self):
        """Default: component name + user id."""
        return [
            self.request.user.id,
            self.state.category_filter,
            self.state.page,
        ]
```

### @cache_action Decorator

Cache expensive action results:

```python
from nitro.cache import cache_action

class Dashboard(NitroComponent[DashboardState]):
    @cache_action(ttl=120)  # Cache for 2 minutes
    def load_analytics(self):
        # This result is cached per-user
        return expensive_analytics_query()

    @cache_action(ttl=60, vary_on=['category'])
    def load_category_stats(self, category: str):
        # Cache varies by category parameter
        return get_stats_for_category(category)
```

---

## See Also

- [ModelNitroComponent](model-nitro-component.md) - For single model instances
- [CrudNitroComponent](crud-nitro-component.md) - For CRUD operations
- [BaseListComponent](base-list-component.md) - For paginated lists
- [State Management](../core-concepts/state-management.md) - Managing state
- [Actions](../core-concepts/actions.md) - Defining actions
