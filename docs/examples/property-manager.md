# Property Manager Example

The Property Manager example is a comprehensive demonstration of Django Nitro's capabilities for building real-world CRUD applications with database integration, relationships, and advanced features.

## Location

```
examples/property-manager/
├── config/                    # Django project settings
├── properties/
│   ├── models.py             # Property and Tenant models
│   ├── schemas.py            # Pydantic schemas
│   ├── components/
│   │   ├── property_list.py
│   │   └── tenant_list.py
│   └── templates/
│       └── components/
│           ├── property_list.html
│           └── tenant_list.html
├── manage.py
└── README.md
```

## What It Demonstrates

-  **Django ORM Integration** - Working with Django models
-  **BaseListComponent** - Pagination, search, and filters
-  **CRUD Operations** - Create, read, update, delete
-  **Related Models** - Foreign keys and relationships
-  **Annotations** - Database aggregations
-  **Inline Editing** - Edit items without page reload
-  **Nested Components** - Property → Tenants relationship
-  **Search & Filters** - Multi-field search
-  **Real-world patterns** - Production-ready code

## Database Models

### Property Model

```python
from django.db import models

class Property(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    units = models.IntegerField(default=1)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']

    def __str__(self):
        return self.name
```

### Tenant Model

```python
class Tenant(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='tenants'
    )
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    move_in_date = models.DateField()
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} @ {self.property.name}"
```

## Pydantic Schemas

### Property Schemas

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

class PropertySchema(BaseModel):
    """Schema for displaying a property."""
    id: int
    name: str
    address: str
    units: int
    monthly_rent: Decimal
    is_active: bool
    tenant_count: int = 0  # From annotation

    class Config:
        from_attributes = True

class PropertyFormSchema(BaseModel):
    """Schema for creating/editing properties."""
    name: str = ""
    address: str = ""
    units: int = 1
    monthly_rent: Decimal = Decimal('0.00')

    @validator('name')
    def name_required(cls, v):
        if not v or not v.strip():
            raise ValueError('Name is required')
        return v.strip()

    @validator('units')
    def units_positive(cls, v):
        if v < 1:
            raise ValueError('Units must be at least 1')
        return v

    @validator('monthly_rent')
    def rent_positive(cls, v):
        if v < 0:
            raise ValueError('Rent cannot be negative')
        return v

class PropertyListState(BaseListState):
    """State for property list component."""
    items: list[PropertySchema] = []

    # Must override buffer types explicitly
    create_buffer: PropertyFormSchema = Field(default_factory=PropertyFormSchema)
    edit_buffer: Optional[PropertyFormSchema] = None
```

## Property List Component

```python
from django.db.models import Count
from nitro.list import BaseListComponent
from nitro.registry import register_component

@register_component
class PropertyList(BaseListComponent[PropertyListState]):
    template_name = "components/property_list.html"
    model = Property
    # state_class auto-inferred from Generic (v0.7.0)

    # Configuration
    search_fields = ['name', 'address']
    per_page = 20
    order_by = '-created_at'

    def get_base_queryset(self, search='', filters=None):
        """Custom queryset with annotations."""
        qs = self.model.objects.annotate(
            tenant_count=Count('tenants')
        )

        # Apply search
        if search:
            qs = self.apply_search(qs, search)

        # Apply filters
        if filters:
            if 'is_active' in filters and filters['is_active'] is not None:
                qs = qs.filter(is_active=filters['is_active'])

        return qs.order_by(self.order_by)

    def toggle_active(self, id: int):
        """Toggle property active status."""
        try:
            prop = self.model.objects.get(id=id)
            prop.is_active = not prop.is_active
            prop.save()

            self.refresh()

            status = "activated" if prop.is_active else "deactivated"
            self.success(f"{prop.name} {status}")
        except self.model.DoesNotExist:
            self.error("Property not found")
```

## Property List Template

```html
<div class="property-list">
    <!-- Search and Filters -->
    <div class="list-header">
        <h2>Properties</h2>

        <div class="search-bar">
            <input
                x-model="search"
                @input.debounce.300ms="call('search_items', {search: $el.value})"
                placeholder="Search properties..."
                type="search"
            >
        </div>

        <div class="filters">
            <select @change="call('set_filters', {
                is_active: $el.value === '' ? null : $el.value === 'true'
            })">
                <option value="">All Properties</option>
                <option value="true">Active Only</option>
                <option value="false">Inactive Only</option>
            </select>

            <button @click="call('clear_filters')" x-show="search || Object.keys(filters).length > 0">
                Clear Filters
            </button>
        </div>
    </div>

    <!-- Results Info -->
    <div class="results-info" x-show="total_count > 0">
        Showing <strong x-text="showing_start"></strong>
        - <strong x-text="showing_end"></strong>
        of <strong x-text="total_count"></strong> properties
    </div>

    <!-- Create Form -->
    <div class="create-form">
        <h3>Add Property</h3>

        <input
            x-model="create_buffer.name"
            placeholder="Property name"
            type="text"
        >

        <textarea
            x-model="create_buffer.address"
            placeholder="Address"
            rows="2"
        ></textarea>

        <input
            x-model.number="create_buffer.units"
            placeholder="Units"
            type="number"
            min="1"
        >

        <input
            x-model.number="create_buffer.monthly_rent"
            placeholder="Monthly rent"
            type="number"
            step="0.01"
            min="0"
        >

        <button @click="call('create_item')" :disabled="isLoading">
            Add Property
        </button>
    </div>

    <!-- Properties Table -->
    <table class="data-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Address</th>
                <th>Units</th>
                <th>Rent</th>
                <th>Tenants</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <template x-for="property in items" :key="property.id">
                <tr>
                    <!-- Normal View -->
                    <template x-if="editing_id !== property.id">
                        <td x-text="property.name"></td>
                        <td x-text="property.address"></td>
                        <td x-text="property.units"></td>
                        <td x-text="'$' + property.monthly_rent"></td>
                        <td x-text="property.tenant_count"></td>
                        <td>
                            <span
                                :class="property.is_active ? 'badge-success' : 'badge-secondary'"
                                x-text="property.is_active ? 'Active' : 'Inactive'"
                            ></span>
                        </td>
                        <td class="actions">
                            <button @click="call('start_edit', {id: property.id})" class="btn-sm">
                                Edit
                            </button>
                            <button @click="call('toggle_active', {id: property.id})" class="btn-sm">
                                <span x-text="property.is_active ? 'Deactivate' : 'Activate'"></span>
                            </button>
                            <button
                                @click="confirm('Delete this property?') && call('delete_item', {id: property.id})"
                                class="btn-sm btn-danger"
                            >
                                Delete
                            </button>
                        </td>
                    </template>

                    <!-- Edit View -->
                    <template x-if="editing_id === property.id && edit_buffer">
                        <td colspan="7">
                            <div class="inline-edit">
                                <input x-model="edit_buffer.name" type="text">
                                <textarea x-model="edit_buffer.address" rows="2"></textarea>
                                <input x-model.number="edit_buffer.units" type="number">
                                <input x-model.number="edit_buffer.monthly_rent" type="number" step="0.01">

                                <button @click="call('save_edit')">Save</button>
                                <button @click="call('cancel_edit')">Cancel</button>
                            </div>
                        </td>
                    </template>
                </tr>
            </template>
        </tbody>
    </table>

    <!-- Empty State -->
    <div x-show="items.length === 0" class="empty-state">
        <p x-show="!search && Object.keys(filters).length === 0">
            No properties yet. Add one above!
        </p>
        <p x-show="search || Object.keys(filters).length > 0">
            No properties match your search or filters.
        </p>
    </div>

    <!-- Pagination -->
    <div class="pagination" x-show="num_pages > 1">
        <button
            @click="call('previous_page')"
            :disabled="!has_previous || isLoading"
        >
            Previous
        </button>

        <span>
            Page <strong x-text="page"></strong>
            of <strong x-text="num_pages"></strong>
        </span>

        <button
            @click="call('next_page')"
            :disabled="!has_next || isLoading"
        >
            Next
        </button>

        <select
            x-model.number="per_page"
            @change="call('set_per_page', {per_page: parseInt($el.value)})"
        >
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
        </select>
    </div>

    <!-- Messages -->
    <template x-for="msg in messages" :key="msg.text">
        <div :class="'alert alert-' + msg.level" x-text="msg.text"></div>
    </template>
</div>
```

## Tenant List Component

Demonstrates nested components - listing tenants for a specific property.

```python
@register_component
class TenantList(BaseListComponent[TenantListState]):
    template_name = "components/tenant_list.html"
    model = Tenant
    # state_class auto-inferred from Generic (v0.7.0)

    search_fields = ['name', 'email', 'phone']
    per_page = 10
    order_by = 'name'

    def get_base_queryset(self, search='', filters=None):
        """Filter tenants by property."""
        property_id = self.kwargs.get('property_id')
        qs = self.model.objects.filter(property_id=property_id)

        # Apply search
        if search:
            qs = self.apply_search(qs, search)

        # Apply filters
        if filters:
            if 'is_active' in filters and filters['is_active'] is not None:
                qs = qs.filter(is_active=filters['is_active'])

        return qs.select_related('property').order_by(self.order_by)

    def create_item(self):
        """Create tenant with property association."""
        property_id = self.kwargs.get('property_id')
        if not property_id:
            self.error("No property specified")
            return

        try:
            tenant = self.model.objects.create(
                **self.state.create_buffer.dict(),
                property_id=property_id
            )
            self.refresh()
            self.success(f"Added tenant: {tenant.name}")
        except Exception as e:
            logger.exception("Create tenant failed")
            self.error("Failed to create tenant")
```

## Key Features

### 1. Database Annotations

```python
def get_base_queryset(self, search='', filters=None):
    # Add computed field
    qs = self.model.objects.annotate(
        tenant_count=Count('tenants')
    )
    return qs
```

Access in template:

```html
<td x-text="property.tenant_count"></td>
```

### 2. Multi-Field Search

```python
search_fields = ['name', 'address']
```

Searches across multiple fields with OR logic.

### 3. Dynamic Filtering

```python
if filters:
    if 'is_active' in filters:
        qs = qs.filter(is_active=filters['is_active'])
```

### 4. Inline Editing

```html
<template x-if="editing_id === property.id && edit_buffer">
    <!-- Editable inputs -->
    <input x-model="edit_buffer.name">
    <button @click="call('save_edit')">Save</button>
</template>
```

### 5. Pagination

```html
<div class="pagination" x-show="num_pages > 1">
    <button @click="call('previous_page')">Previous</button>
    <span>Page <span x-text="page"></span> of <span x-text="num_pages"></span></span>
    <button @click="call('next_page')">Next</button>
</div>
```

### 6. Nested Components

```python
def property_detail(request, pk):
    property_comp = PropertyDetail(request=request, pk=pk)
    tenant_list = TenantList(request=request, property_id=pk)

    return render(request, 'property_detail.html', {
        'property': property_comp,
        'tenants': tenant_list
    })
```

## Running the Example

### Setup

```bash
cd examples/property-manager

# Create virtual environment
python -m venv env
source env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create sample data (optional)
python manage.py loaddata sample_data.json

# Start server
python manage.py runserver
```

### Access

Visit: `http://localhost:8000/`

## Production Patterns

### Validation

```python
@validator('name')
def name_required(cls, v):
    if not v or not v.strip():
        raise ValueError('Name is required')
    return v.strip()
```

### Error Handling

```python
try:
    property = self.model.objects.create(...)
    self.success("Property created")
except ValidationError as e:
    self.error(f"Validation error: {e}")
except Exception:
    logger.exception("Create failed")
    self.error("An error occurred")
```

### Query Optimization

```python
def get_base_queryset(self, search='', filters=None):
    qs = self.model.objects.select_related(
        'property'
    ).prefetch_related(
        'tenants'
    )
    return qs
```

## Learn From This Example

1. **Start Simple** - Begin with basic CRUD, add features incrementally
2. **Use BaseListComponent** - Don't reinvent pagination/search
3. **Validate Everything** - Server-side validation is critical
4. **Optimize Queries** - Use select_related and prefetch_related
5. **Handle Errors** - Always use try/except and show helpful messages
6. **Test Thoroughly** - Write tests for all CRUD operations

## What's Next?

After exploring this example:

1. **Add Authentication** - Use [OwnershipMixin](../security/ownership-mixin.md)
2. **Add Permissions** - Use [PermissionMixin](../security/permission-mixin.md)
3. **Add Multi-Tenancy** - Use [TenantScopedMixin](../security/tenant-scoped-mixin.md)
4. **Add File Uploads** - Use `{% nitro_file %}` tag (see [API Reference](../api-reference.md#template-tags-v040))

## Complete Code

The full working example is available in:

```
examples/property-manager/
```

## Learn More

- [BaseListComponent Reference](../components/base-list-component.md)
- [CrudNitroComponent Reference](../components/crud-nitro-component.md)
- [State Management Guide](../core-concepts/state-management.md)
