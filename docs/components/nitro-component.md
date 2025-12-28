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
    state_class = MyComponentState

    def get_initial_state(self, **kwargs):
        return MyComponentState(
            field1=kwargs.get('field1', ''),
            field2=kwargs.get('field2', 0)
        )

    def my_action(self):
        # Your action logic
        self.state.field2 += 1
```

## Class Attributes

### Required

```python
template_name: str
```
Path to the component's HTML template.

```python
state_class: Type[BaseModel]
```
Pydantic model class defining the component's state structure.

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

### Security Helpers (v0.3.0+)

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
    state_class = ContactFormState

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
    state_class = CalculatorState
```

## See Also

- [ModelNitroComponent](model-nitro-component.md) - For single model instances
- [CrudNitroComponent](crud-nitro-component.md) - For CRUD operations
- [BaseListComponent](base-list-component.md) - For paginated lists
- [State Management](../core-concepts/state-management.md) - Managing state
- [Actions](../core-concepts/actions.md) - Defining actions
