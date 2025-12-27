# Django Nitro Example Project

This is a complete example application demonstrating Django Nitro's capabilities.

## Features

- **Property Management**: CRUD operations for properties with search functionality
- **Tenant Management**: Nested component for managing tenants within properties
- **Inline Editing**: Edit properties and tenants without page refresh
- **Real-time Validation**: Pydantic-based validation with error messages
- **Success/Error Messages**: User-friendly notifications
- **Optimized Updates**: No full page refreshes, smooth UI updates

## Project Structure

```
example/
├── app/                    # Django project settings
│   ├── settings.py
│   └── urls.py
├── properties/             # Example app
│   ├── models.py          # Property and Tenant models
│   ├── schemas.py         # Pydantic schemas
│   ├── views.py           # Django views
│   └── components/        # Nitro components
│       ├── property_list.py
│       └── tenant_manager.py
└── templates/             # HTML templates
    ├── base.html
    ├── components/        # Component templates
    └── pages/             # Page templates
```

## Setup

### 1. Install Django Nitro

From the parent directory:

```bash
pip install -e ..
```

Or install from PyPI (when published):

```bash
pip install django-nitro
```

### 2. Install Example Dependencies

```bash
cd example
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 5. Run the Development Server

```bash
python manage.py runserver
```

Visit **http://localhost:8000** to see the example in action.

## What to Explore

### Property List Component (`properties/components/property_list.py`)

Demonstrates:
- **CrudNitroComponent** usage
- Search functionality with debouncing
- Create, edit, delete operations
- Inline editing UI
- Custom `refresh()` logic to preserve filters

**Try:**
- Create a new property
- Search for properties
- Edit a property inline
- Delete a property

### Tenant Manager Component (`properties/components/tenant_manager.py`)

Demonstrates:
- **CrudNitroComponent** for nested data
- Optimized CRUD without full refreshes
- Custom validation
- Error handling

**Try:**
- Click on a property to view its tenants
- Add a new tenant
- Edit tenant information
- Delete a tenant

## Code Highlights

### Component with Pre-built CRUD

```python
# properties/components/property_list.py
@register_component
class PropertyList(CrudNitroComponent[PropertyListState]):
    model = Property

    # create_item(), delete_item(), start_edit(), save_edit()
    # are already implemented! ✅

    # Just add custom actions:
    def search(self):
        self.refresh()  # Custom refresh with search query
```

### Optimized Updates (No Visual Flash)

```python
# properties/components/tenant_manager.py
def create_item(self):
    # Create in DB
    tenant = Tenant.objects.create(...)

    # Add to state directly (no refresh)
    self.state.tenants.insert(0, TenantSchema.model_validate(tenant))

    # Result: Instant UI update, no flash! ⚡
```

### AlpineJS Template Integration

```html
<!-- templates/components/property_list.html -->

<!-- Two-way binding -->
<input x-model="create_buffer.name">

<!-- Call component actions -->
<button @click="call('create_item')">Create</button>

<!-- Debounced search -->
<input @input.debounce.300ms="call('search')">

<!-- Conditional rendering -->
<template x-if="editing_id === prop.id">
    <!-- Edit form -->
</template>
```

## Learning Path

1. **Start with Property List**: See how `CrudNitroComponent` works
2. **Explore Templates**: Understand Alpine + Django integration
3. **Check Schemas**: Learn Pydantic validation patterns
4. **Customize Actions**: Add your own methods to components
5. **Optimize UI**: See how we avoid page reloads

## Next Steps

- Try adding a new field to `Property` model
- Create a new component for a different model
- Add custom validation to tenant creation
- Implement filtering or pagination
- Add user authentication

## Questions?

Check the [main README](../README.md) for full documentation.
