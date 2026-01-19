# State Management

State is the heart of Django Nitro components. It defines the data structure, validation rules, and synchronization between server and client.

## How State Works

Django Nitro uses Pydantic models for state, providing:

1. **Type Safety** - Full type hints and validation
2. **Automatic Serialization** - Python ↔ JSON conversion
3. **Client-Server Sync** - Automatic state synchronization
4. **Security** - Integrity verification for sensitive fields

### State Flow

```
┌─────────────┐
│   Server    │ 1. Create state (Pydantic model)
│   (Python)  │
└──────┬──────┘
       │
       ↓ 2. Serialize to JSON
┌─────────────┐
│  Template   │ 3. Embed in HTML
│   (Django)  │
└──────┬──────┘
       │
       ↓ 4. Parse and make reactive
┌─────────────┐
│   Client    │ 5. User interacts
│  (AlpineJS) │
└──────┬──────┘
       │
       ↓ 6. Send updated state
┌─────────────┐
│  API Call   │ 7. Validate and process
│   (Ninja)   │
└──────┬──────┘
       │
       ↓ 8. Return updated state
┌─────────────┐
│   Client    │ 9. Update UI reactively
│  (AlpineJS) │
└─────────────┘
```

## Defining State

### Basic State Schema

```python
from pydantic import BaseModel

class CounterState(BaseModel):
    count: int = 0
    step: int = 1
```

### State with Validation

```python
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional

class UserFormState(BaseModel):
    name: str = Field("", min_length=2, max_length=100)
    email: EmailStr = ""
    age: int = Field(0, ge=0, le=150)
    bio: Optional[str] = None

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name is required')
        return v.strip()

    @validator('bio')
    def bio_max_length(cls, v):
        if v and len(v) > 500:
            raise ValueError('Bio too long (max 500 characters)')
        return v
```

### State with Django Models

Use `from_attributes=True` (formerly `orm_mode`) to load from Django models:

```python
from pydantic import BaseModel
from typing import Optional

class ProductSchema(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True  # Enable ORM model loading
```

Now you can:

```python
product = Product.objects.get(pk=1)
state = ProductSchema.model_validate(product)  # Converts Django model to Pydantic
```

## Complex State Structures

### Nested Models

```python
from pydantic import BaseModel
from typing import List

class AddressSchema(BaseModel):
    street: str
    city: str
    zip_code: str

class UserProfileState(BaseModel):
    name: str
    email: str
    addresses: List[AddressSchema] = []
```

### State with Enums

```python
from enum import Enum
from pydantic import BaseModel

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskState(BaseModel):
    title: str
    priority: Priority = Priority.MEDIUM
    completed: bool = False
```

### Optional and Nullable Fields

```python
from typing import Optional
from pydantic import BaseModel

class FormState(BaseModel):
    # Optional with default
    description: str = ""

    # Nullable (can be None)
    selected_id: Optional[int] = None

    # Both optional and nullable
    notes: Optional[str] = None
```

## State in Component Classes

### Initializing State

```python
@register_component
class MyComponent(NitroComponent[MyState]):
    # state_class auto-inferred from Generic (v0.7.0)

    def get_initial_state(self, **kwargs):
        """Called when component is created."""
        return MyState(
            field1=kwargs.get('field1', 'default'),
            field2=kwargs.get('field2', 0)
        )
```

### Accessing State

```python
class MyComponent(NitroComponent[MyState]):
    def my_action(self):
        # Read state
        current_count = self.state.count

        # Modify state
        self.state.count += 1

        # State is automatically synced back to client
```

### State Persistence

State is **not persistent** by default. It resets on page reload.

For persistence, save to database or session:

```python
class ShoppingCart(NitroComponent[CartState]):
    def add_item(self, product_id: int):
        # Add to state
        self.state.items.append(product_id)

        # Persist to session
        self.request.session['cart'] = self.state.items

    def get_initial_state(self, **kwargs):
        # Restore from session
        items = self.request.session.get('cart', [])
        return CartState(items=items)
```

## List Components State

List components use special state classes with built-in fields:

### BaseListState

```python
from nitro.list import BaseListState
from pydantic import Field
from typing import Optional

class ProductListState(BaseListState):
    # Items in current page
    items: list[ProductSchema] = []

    # Inherited from BaseListState:
    # - search: str = ""
    # - page: int = 1
    # - per_page: int = 20
    # - total_count: int = 0
    # - num_pages: int = 0
    # - has_next: bool = False
    # - has_previous: bool = False
    # - showing_start: int = 0
    # - showing_end: int = 0
    # - filters: dict = {}

    # IMPORTANT: Must override buffer types
    create_buffer: ProductFormSchema = Field(default_factory=ProductFormSchema)
    edit_buffer: Optional[ProductFormSchema] = None
```

### Why Override Buffer Types?

`BaseListState` uses `Any` for buffers, which breaks type inference:

```python
# ❌ Will fail - type inference broken
class MyListState(BaseListState):
    items: list[ItemSchema] = []
    # Using inherited buffers with type Any

# ✅ Correct - explicit types
class MyListState(BaseListState):
    items: list[ItemSchema] = []
    create_buffer: ItemFormSchema = Field(default_factory=ItemFormSchema)
    edit_buffer: Optional[ItemFormSchema] = None
```

## State Validation

### Client-Side (Automatic)

AlpineJS provides instant feedback through reactive bindings:

```html
<input
    x-model="email"
    :class="{'error': errors.email}"
    type="email"
>
<span x-show="errors.email" x-text="errors.email"></span>
```

### Server-Side (Pydantic)

Validation happens automatically when state is updated:

```python
class UserState(BaseModel):
    email: EmailStr  # Validates email format
    age: int = Field(ge=18, le=100)  # Age between 18-100

    @validator('email')
    def email_must_be_company(cls, v):
        if not v.endswith('@company.com'):
            raise ValueError('Must use company email')
        return v
```

If validation fails:
- Pydantic raises `ValidationError`
- Error details are sent to client
- Errors appear in `errors` object in template

### Custom Validation in Actions

```python
def save_profile(self):
    # Additional validation beyond Pydantic
    if self.state.age < 18:
        self.error("Must be 18 or older")
        return

    if contains_profanity(self.state.bio):
        self.error("Bio contains inappropriate content")
        return

    # Save after validation
    profile = self.request.user.profile
    profile.bio = self.state.bio
    profile.save()
    self.success("Profile updated")
```

## State Security

### Secure Fields

Prevent client-side tampering with sensitive fields:

```python
class PricingComponent(NitroComponent[PricingState]):
    secure_fields = ['price', 'discount_percent', 'user_id']
```

Secure fields are:
- Protected with HMAC integrity tokens
- Verified on every action call
- Tampering triggers 403 Forbidden error

### Automatic Security (ModelNitroComponent)

`ModelNitroComponent` automatically secures:
- `id` field
- Any field ending with `_id` (foreign keys)

```python
class ProductEditor(ModelNitroComponent[ProductSchema]):
    model = Product
    # Automatically secured: id, category_id, owner_id
```

## State and Templates

### Accessing State in Templates

State properties are directly available in Alpine:

```html
<!-- Direct access -->
<div x-text="count"></div>
<div x-text="email"></div>

<!-- Conditional rendering -->
<div x-show="is_active">Active</div>
<div x-show="!is_active">Inactive</div>

<!-- Loops -->
<template x-for="item in items" :key="item.id">
    <div x-text="item.name"></div>
</template>

<!-- Computed values -->
<div x-text="`Total: ${items.length}`"></div>
```

### Two-Way Binding

Use `x-model` for automatic synchronization:

```html
<!-- Text input -->
<input x-model="name" type="text">

<!-- Number input -->
<input x-model.number="age" type="number">

<!-- Checkbox -->
<input x-model="is_active" type="checkbox">

<!-- Select -->
<select x-model="category">
    <option value="1">Category 1</option>
    <option value="2">Category 2</option>
</select>

<!-- Textarea -->
<textarea x-model="description"></textarea>
```

Changes are **local only** until you call an action:

```html
<input x-model="name" type="text">
<button @click="call('save')">Save</button>
```

## State Best Practices

### 1. Use Proper Types

```python
# ✅ Good - specific types
class TaskState(BaseModel):
    title: str
    due_date: Optional[date] = None
    priority: Priority = Priority.MEDIUM

# ❌ Avoid - vague types
class TaskState(BaseModel):
    title: Any
    due_date: Any
    priority: Any
```

### 2. Provide Sensible Defaults

```python
# ✅ Good - clear defaults
class FormState(BaseModel):
    name: str = ""
    is_active: bool = True
    items: list[str] = Field(default_factory=list)

# ❌ Avoid - no defaults (hard to initialize)
class FormState(BaseModel):
    name: str
    is_active: bool
    items: list[str]
```

### 3. Use Validators for Business Logic

```python
class OrderState(BaseModel):
    quantity: int = 1
    unit_price: float = 0.0

    @validator('quantity')
    def quantity_positive(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        return v

    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price
```

### 4. Keep State Flat When Possible

```python
# ✅ Good - flat structure
class UserFormState(BaseModel):
    name: str
    email: str
    street: str
    city: str

# ⚠️ Use nesting only when necessary
class UserFormState(BaseModel):
    name: str
    email: str
    address: AddressSchema  # OK if address is reused
```

### 5. Document State Fields

```python
class ProductState(BaseModel):
    """State for product management component."""

    id: int
    """Product primary key (secured)."""

    name: str = Field("", min_length=1, max_length=200)
    """Product name (required, max 200 chars)."""

    price: float = Field(0.0, ge=0)
    """Product price in USD (must be non-negative)."""
```

## Next Steps

- [Actions](actions.md) - Learn how to modify state through actions
- [Components](components.md) - Understanding component architecture
- [Security Overview](../security/overview.md) - Securing your state
