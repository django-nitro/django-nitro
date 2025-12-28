# Actions

Actions are methods on your component that can be called from the template. They handle user interactions, modify state, and trigger server-side logic.

## How Actions Work

```
┌─────────────┐
│   User      │ 1. Click button
│  (Browser)  │
└──────┬──────┘
       │
       ↓ 2. call('action_name', {params})
┌─────────────┐
│  AlpineJS   │ 3. Collect current state
│   (Client)  │
└──────┬──────┘
       │
       ↓ 4. POST /api/nitro/dispatch
┌─────────────┐
│ Django Ninja│ 5. Validate state
│    (API)    │ 6. Reconstruct component
└──────┬──────┘
       │
       ↓ 7. Call action method
┌─────────────┐
│  Component  │ 8. Modify state
│   (Python)  │ 9. Add messages
└──────┬──────┘
       │
       ↓ 10. Serialize updated state
┌─────────────┐
│  Response   │ 11. Return JSON
│   (JSON)    │
└──────┬──────┘
       │
       ↓ 12. Update reactive state
┌─────────────┐
│  AlpineJS   │ 13. UI updates automatically
│   (Client)  │
└─────────────┘
```

## Defining Actions

Any public method (not starting with `_`) can be called as an action:

```python
from nitro.base import NitroComponent
from nitro.registry import register_component

@register_component
class Counter(NitroComponent[CounterState]):
    # ✅ Public method - can be called from template
    def increment(self):
        self.state.count += 1

    # ✅ Public method with parameters
    def add(self, amount: int):
        self.state.count += amount

    # ✅ Public method with optional parameters
    def set_value(self, value: int = 0):
        self.state.count = value

    # ❌ Private method - cannot be called from template
    def _calculate_something(self):
        return self.state.count * 2
```

## Calling Actions from Templates

### Basic Action Call

```html
<button @click="call('increment')">+1</button>
```

### Action with Parameters

```html
<!-- Single parameter -->
<button @click="call('add', {amount: 5})">+5</button>

<!-- Multiple parameters -->
<button @click="call('create_user', {name: 'John', email: 'john@example.com'})">
    Create
</button>

<!-- Using state values -->
<button @click="call('delete_item', {id: item.id})">Delete</button>
```

### Action with Event Modifiers

```html
<!-- Prevent default form submission -->
<form @submit.prevent="call('submit_form')">
    <button type="submit">Submit</button>
</form>

<!-- Debounce for search -->
<input
    x-model="search"
    @input.debounce.300ms="call('search')"
    placeholder="Search..."
>

<!-- Only on Enter key -->
<input
    x-model="name"
    @keyup.enter="call('create_item')"
    placeholder="Type and press Enter"
>

<!-- Stop propagation -->
<div @click.stop="call('select_item', {id: item.id})">
    Item content
</div>
```

## Action Parameters

### Type Hints

Use type hints for automatic validation:

```python
def update_quantity(self, item_id: int, quantity: int):
    """Parameters are validated automatically."""
    if quantity < 1:
        self.error("Quantity must be positive")
        return

    # Update logic...
```

### Optional Parameters

```python
def search(self, query: str = ""):
    """Optional parameters with defaults."""
    if not query:
        self.state.results = []
        return

    self.state.results = self.model.objects.filter(
        name__icontains=query
    )
```

### Complex Parameter Types

```python
from typing import List, Optional

def bulk_update(self, ids: List[int], status: str):
    """Accept lists and complex types."""
    items = self.model.objects.filter(id__in=ids)
    items.update(status=status)
    self.refresh()
```

## Common Action Patterns

### Create

```python
def create_item(self):
    """Create new item from create_buffer."""
    try:
        # Validate
        if not self.state.create_buffer.name:
            self.error("Name is required")
            return

        # Create
        obj = self.model.objects.create(
            **self.state.create_buffer.dict()
        )

        # Refresh and notify
        self.refresh()
        self.success(f"Created {obj.name}")

    except Exception as e:
        logger.exception("Create failed")
        self.error("Failed to create item")
```

### Update

```python
def save_edit(self):
    """Save changes from edit_buffer."""
    if not self.state.editing_id or not self.state.edit_buffer:
        return

    try:
        obj = self.model.objects.get(id=self.state.editing_id)

        # Update fields
        for field, value in self.state.edit_buffer.dict().items():
            setattr(obj, field, value)

        obj.save()

        # Clear edit mode
        self.state.editing_id = None
        self.state.edit_buffer = None

        self.refresh()
        self.success("Changes saved")

    except self.model.DoesNotExist:
        self.error("Item not found")
```

### Delete

```python
def delete_item(self, id: int):
    """Delete item by ID."""
    try:
        obj = self.model.objects.get(id=id)

        # Optional: Check permissions
        if obj.owner != self.request.user:
            self.error("Permission denied")
            return

        obj.delete()
        self.refresh()
        self.success("Item deleted")

    except self.model.DoesNotExist:
        self.error("Item not found")
```

### Toggle

```python
def toggle_active(self, id: int):
    """Toggle boolean field."""
    try:
        obj = self.model.objects.get(id=id)
        obj.is_active = not obj.is_active
        obj.save()

        self.refresh()
        status = "activated" if obj.is_active else "deactivated"
        self.success(f"Item {status}")

    except self.model.DoesNotExist:
        self.error("Item not found")
```

### Search

```python
def search(self, query: str = ""):
    """Search items by query."""
    self.state.search = query
    self.state.page = 1  # Reset to first page

    if not query:
        self.state.items = []
        return

    # Apply search
    results = self.model.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    )

    self.state.items = [
        ItemSchema.model_validate(item)
        for item in results
    ]
```

## Action Return Values

Actions **do not** use return values for client updates. State changes are automatic:

```python
# ✅ Good - modify state directly
def increment(self):
    self.state.count += 1
    # State automatically synced to client

# ❌ Wrong - return value ignored
def increment(self):
    return {"count": self.state.count + 1}
    # This does nothing!
```

## Action Messages

Use built-in message methods for user feedback:

```python
def save_profile(self):
    try:
        # Validation
        if not self.state.name:
            self.error("Name is required")
            return

        # Save
        profile = self.request.user.profile
        profile.name = self.state.name
        profile.save()

        # Success message
        self.success("Profile saved successfully!")

    except Exception as e:
        logger.exception("Profile save failed")
        self.error("An error occurred. Please try again.")
```

### Message Methods

```python
self.success("Operation successful")  # Green/success
self.error("Something went wrong")    # Red/error
self.info("FYI: Something happened")  # Blue/info
```

### Displaying Messages

```html
<template x-for="msg in messages" :key="msg.text">
    <div
        :class="{
            'alert-success': msg.level === 'success',
            'alert-error': msg.level === 'error',
            'alert-info': msg.level === 'info'
        }"
        x-text="msg.text"
    ></div>
</template>
```

## Action Security

### Authentication

Always check authentication when needed:

```python
def delete_account(self):
    # Check authentication
    if not self.is_authenticated:
        self.error("Authentication required")
        return

    # Or use helper
    if not self.require_auth("Please log in to delete your account"):
        return  # Stops execution if not authenticated

    # Delete logic...
```

### Authorization

Check permissions before sensitive operations:

```python
def delete_document(self, id: int):
    # Check permission
    if not self.request.user.has_perm('documents.delete_document'):
        self.error("Permission denied")
        return

    # Check ownership
    doc = Document.objects.get(id=id)
    if doc.owner != self.request.user:
        self.error("You don't own this document")
        return

    # Delete
    doc.delete()
    self.refresh()
```

### Input Validation

Never trust client-side data:

```python
def update_price(self, product_id: int, new_price: float):
    # Validate input
    if new_price < 0:
        self.error("Price cannot be negative")
        return

    if new_price > 1000000:
        self.error("Price exceeds maximum")
        return

    # Additional checks
    product = Product.objects.get(id=product_id)
    if product.owner != self.request.user:
        self.error("Permission denied")
        return

    # Update after validation
    product.price = new_price
    product.save()
    self.success("Price updated")
```

## Action Error Handling

### Try-Except Blocks

```python
def save_item(self):
    try:
        obj = self.model.objects.create(
            **self.state.create_buffer.dict()
        )
        self.success("Created successfully")

    except ValidationError as e:
        self.error(f"Validation error: {e}")

    except IntegrityError:
        self.error("Item already exists")

    except Exception as e:
        logger.exception("Unexpected error")
        self.error("An error occurred")
```

### Validation Errors

```python
from pydantic import ValidationError

def update_email(self, new_email: str):
    try:
        # Validate using Pydantic
        validated = EmailSchema(email=new_email)

        # Update
        self.request.user.email = validated.email
        self.request.user.save()
        self.success("Email updated")

    except ValidationError as e:
        # Show validation errors
        for error in e.errors():
            field = error['loc'][0]
            message = error['msg']
            self.error(f"{field}: {message}")
```

## Advanced Action Patterns

### Optimistic Updates

Update UI immediately, then sync with server:

```python
def toggle_completed(self, task_id: int):
    # Update state immediately (optimistic)
    for task in self.state.tasks:
        if task.id == task_id:
            task.completed = not task.completed
            break

    # Then sync to database
    try:
        task_obj = Task.objects.get(id=task_id)
        task_obj.completed = not task_obj.completed
        task_obj.save()

    except Exception:
        # If it fails, refresh to revert
        self.refresh()
        self.error("Failed to update task")
```

### Batch Operations

```python
def bulk_delete(self, ids: List[int]):
    """Delete multiple items at once."""
    if not ids:
        self.error("No items selected")
        return

    try:
        count = self.model.objects.filter(id__in=ids).delete()[0]
        self.refresh()
        self.success(f"Deleted {count} items")

    except Exception as e:
        logger.exception("Bulk delete failed")
        self.error("Failed to delete items")
```

### Action Chaining

```python
def save_and_publish(self):
    """Chain multiple operations."""
    # Save first
    if not self.save_draft():
        return  # Stop if save failed

    # Then publish
    self.publish()

def save_draft(self) -> bool:
    """Returns True if successful."""
    try:
        # Save logic...
        self.success("Draft saved")
        return True
    except Exception:
        self.error("Save failed")
        return False

def publish(self):
    """Assumes draft was saved."""
    obj = self.get_object(self.state.id)
    obj.published = True
    obj.save()
    self.success("Published!")
```

### Conditional Actions

```python
def submit_form(self):
    """Different logic based on state."""
    if self.state.mode == 'create':
        self.create_item()
    elif self.state.mode == 'edit':
        self.save_edit()
    else:
        self.error("Invalid mode")
```

## Action Performance

### Database Optimization

```python
# ✅ Good - optimized query
def load_products(self):
    products = Product.objects.select_related('category').prefetch_related('tags')
    self.state.products = [
        ProductSchema.model_validate(p) for p in products
    ]

# ❌ Avoid - N+1 queries
def load_products(self):
    products = Product.objects.all()
    for product in products:
        _ = product.category  # Separate query each time!
```

### Limiting Data

```python
def search(self, query: str):
    # Limit results to prevent huge payloads
    results = Product.objects.filter(
        name__icontains=query
    )[:50]  # Max 50 results

    self.state.results = [
        ProductSchema.model_validate(p) for p in results
    ]
```

### Caching

```python
from django.core.cache import cache

def get_statistics(self):
    """Cache expensive calculations."""
    cache_key = f"stats_{self.request.user.id}"

    stats = cache.get(cache_key)
    if not stats:
        # Expensive calculation
        stats = calculate_statistics(self.request.user)
        cache.set(cache_key, stats, 300)  # 5 minutes

    self.state.statistics = stats
```

## Best Practices

### 1. Keep Actions Small

```python
# ✅ Good - focused actions
def increment(self):
    self.state.count += 1

def decrement(self):
    self.state.count -= 1

# ❌ Avoid - too much in one action
def manage_counter(self, operation: str, amount: int):
    if operation == 'increment':
        self.state.count += amount
    elif operation == 'decrement':
        self.state.count -= amount
    # ... too complex
```

### 2. Validate Early

```python
def create_order(self, product_id: int, quantity: int):
    # Validate first
    if quantity < 1:
        self.error("Invalid quantity")
        return

    if not self.is_authenticated:
        self.error("Please log in")
        return

    # Then proceed with logic
    # ...
```

### 3. Use Descriptive Names

```python
# ✅ Good - clear intent
def mark_as_complete(self):
    ...

def send_reminder_email(self):
    ...

# ❌ Avoid - vague names
def do_thing(self):
    ...

def process(self):
    ...
```

### 4. Handle Errors Gracefully

```python
def save(self):
    try:
        # Logic
        self.success("Saved")
    except Exception as e:
        logger.exception("Save failed")  # Log for debugging
        self.error("An error occurred")  # Show user-friendly message
```

## Next Steps

- [State Management](state-management.md) - Managing component state
- [Components](components.md) - Component architecture
- [Security Overview](../security/overview.md) - Securing actions
