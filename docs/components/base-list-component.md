# BaseListComponent

`BaseListComponent` extends `CrudNitroComponent` with built-in **pagination**, **search**, and **filtering** capabilities. It's the most feature-rich component for managing large lists of data with all CRUD operations.

## When to Use

Use `BaseListComponent` when you need:

- **Paginated lists** with large datasets
- **Full-text search** across multiple fields
- **Dynamic filtering** by various criteria
- **All CRUD operations** plus list management
- **Professional admin interfaces**

**Examples:**
- Product catalog with search and filters
- User management dashboard
- Invoice list with pagination
- Any large dataset requiring search and filters

## Key Features

-  **Pagination** - Django Paginator integration with page navigation
-  **Search** - Full-text search across configurable fields
-  **Filters** - Dynamic queryset filtering
-  **All CRUD Operations** - Inherited from CrudNitroComponent
-  **Rich Metadata** - total_count, showing_start, showing_end for UX
-  **Automatic Page Reset** - When search/filters change

## Basic Structure

```python
from pydantic import BaseModel, Field
from nitro.list import BaseListComponent, BaseListState
from nitro.registry import register_component
from typing import Optional
from myapp.models import Product

# Item schema (with id)
class ProductSchema(BaseModel):
    id: int
    name: str
    price: float
    is_active: bool

    class Config:
        from_attributes = True

# Form schema (no id)
class ProductFormSchema(BaseModel):
    name: str = ""
    price: float = 0.0

# State schema - inherits pagination fields from BaseListState
class ProductListState(BaseListState):
    items: list[ProductSchema] = []

    # IMPORTANT: Must override buffer types
    create_buffer: ProductFormSchema = Field(default_factory=ProductFormSchema)
    edit_buffer: Optional[ProductFormSchema] = None

# Component
@register_component
class ProductList(BaseListComponent[ProductListState]):
    template_name = "components/product_list.html"
    state_class = ProductListState
    model = Product

    # Configure search and pagination
    search_fields = ['name', 'description']
    per_page = 25
    order_by = '-created_at'
```

## Configuration Attributes

### `search_fields: list[str]`

Fields to search across using Django Q objects (OR logic).

```python
class ProductList(BaseListComponent[ProductListState]):
    search_fields = ['name', 'description', 'sku']
    # Searches: name LIKE %query% OR description LIKE %query% OR sku LIKE %query%
```

### `per_page: int`

Default number of items per page (default: 20).

```python
class ProductList(BaseListComponent[ProductListState]):
    per_page = 50  # Show 50 items per page
```

### `order_by: str`

Default ordering for queryset.

```python
class ProductList(BaseListComponent[ProductListState]):
    order_by = '-created_at'  # Newest first
    # order_by = 'name'  # Alphabetical
    # order_by = '-price'  # Highest price first
```

## State Structure

`BaseListState` provides built-in fields for pagination and search:

```python
from nitro.list import BaseListState

class MyListState(BaseListState):
    # Your items list (required)
    items: list[ItemSchema] = []

    # Inherited from BaseListState:
    search: str = ""              # Current search query
    page: int = 1                 # Current page number
    per_page: int = 20            # Items per page
    total_count: int = 0          # Total items (all pages)
    num_pages: int = 0            # Total number of pages
    has_next: bool = False        # Has next page?
    has_previous: bool = False    # Has previous page?
    showing_start: int = 0        # First item index on current page
    showing_end: int = 0          # Last item index on current page
    filters: dict = {}            # Active filters

    # CRUD buffers (required - must override types!)
    create_buffer: ItemFormSchema = Field(default_factory=ItemFormSchema)
    edit_buffer: Optional[ItemFormSchema] = None
    editing_id: Optional[int] = None
```

**Important:** You MUST override buffer types explicitly because `BaseListState` uses `Any`:

```python
# ❌ Wrong - type inference broken
class MyListState(BaseListState):
    items: list[ItemSchema] = []
    # Using inherited buffers (type Any)

# ✅ Correct - explicit types
class MyListState(BaseListState):
    items: list[ItemSchema] = []
    create_buffer: ItemFormSchema = Field(default_factory=ItemFormSchema)
    edit_buffer: Optional[ItemFormSchema] = None
```

## Pre-built Methods

### Pagination

#### `next_page() -> None`

Navigate to next page.

```html
<button @click="call('next_page')" :disabled="!has_next">Next</button>
```

#### `previous_page() -> None`

Navigate to previous page.

```html
<button @click="call('previous_page')" :disabled="!has_previous">Previous</button>
```

#### `go_to_page(page: int) -> None`

Navigate to specific page.

```html
<button @click="call('go_to_page', {page: 1})">First</button>
<button @click="call('go_to_page', {page: num_pages})">Last</button>
```

#### `set_per_page(per_page: int) -> None`

Change items per page.

```html
<select @change="call('set_per_page', {per_page: parseInt($event.target.value)})">
    <option value="10">10</option>
    <option value="25">25</option>
    <option value="50">50</option>
    <option value="100">100</option>
</select>
```

### Search

#### `search_items(search: str) -> None`

Performs search and resets to page 1.

```html
<input
    x-model="search"
    @input.debounce.300ms="call('search_items', {search: $event.target.value})"
    placeholder="Search..."
>
```

### Filters

#### `set_filters(**filters) -> None`

Applies filters and resets to page 1.

```html
<select @change="call('set_filters', {is_active: $event.target.value === 'true'})">
    <option value="">All</option>
    <option value="true">Active</option>
    <option value="false">Inactive</option>
</select>
```

#### `clear_filters() -> None`

Removes all filters and search.

```html
<button @click="call('clear_filters')">Clear All</button>
```

### refresh() Override

`BaseListComponent` automatically handles pagination, search, and filters in `refresh()`. You can override for custom logic:

```python
def refresh(self):
    # Custom queryset logic
    qs = self.get_base_queryset(
        search=self.state.search,
        filters=self.state.filters
    )

    # Pagination handled automatically
    # Don't need to manually paginate
```

## Customizing Queryset

### Override `get_base_queryset()`

Customize the base queryset before pagination/search/filters are applied:

```python
@register_component
class ProductList(BaseListComponent[ProductListState]):
    search_fields = ['name']
    per_page = 25
    order_by = '-created_at'

    def get_base_queryset(self, search='', filters=None):
        # Start with base queryset
        qs = self.model.objects.filter(owner=self.current_user)

        # Apply search (uses self.search_fields)
        if search:
            qs = self.apply_search(qs, search)

        # Apply filters
        if filters:
            qs = self.apply_filters(qs, filters)

        # Add optimizations
        qs = qs.select_related('category').prefetch_related('tags')

        # Apply ordering
        return qs.order_by(self.order_by)
```

## Complete Example

```python
from django.db import models
from pydantic import BaseModel, Field, validator
from nitro.list import BaseListComponent, BaseListState
from nitro.registry import register_component
from typing import Optional

# Django Model
class Company(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Companies"

# Item schema
class CompanySchema(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    is_active: bool

    class Config:
        from_attributes = True

# Form schema
class CompanyFormSchema(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""

    @validator('name')
    def name_required(cls, v):
        if not v or not v.strip():
            raise ValueError('Name is required')
        return v.strip()

# State schema
class CompanyListState(BaseListState):
    items: list[CompanySchema] = []

    # Must override buffer types
    create_buffer: CompanyFormSchema = Field(default_factory=CompanyFormSchema)
    edit_buffer: Optional[CompanyFormSchema] = None

# Component
@register_component
class CompanyList(BaseListComponent[CompanyListState]):
    template_name = "components/company_list.html"
    state_class = CompanyListState
    model = Company

    # Configuration
    search_fields = ['name', 'email', 'phone']
    per_page = 25
    order_by = '-created_at'

    def get_base_queryset(self, search='', filters=None):
        # Filter by current user
        qs = self.model.objects.filter(owner=self.current_user)

        # Apply search
        if search:
            qs = self.apply_search(qs, search)

        # Apply filters
        if filters:
            # Handle boolean filter
            if 'is_active' in filters:
                qs = qs.filter(is_active=filters['is_active'])

        return qs.order_by(self.order_by)

    # Override create to add owner
    def create_item(self):
        if not self.require_auth():
            return

        try:
            company = self.model.objects.create(
                **self.state.create_buffer.dict(),
                owner=self.current_user
            )
            self.refresh()
            self.success(f"Created {company.name}")
        except Exception as e:
            logger.exception("Create failed")
            self.error("Failed to create company")

    # Custom action: toggle active status
    def toggle_active(self, id: int):
        try:
            company = self.model.objects.get(id=id, owner=self.current_user)
            company.is_active = not company.is_active
            company.save()
            self.refresh()

            status = "activated" if company.is_active else "deactivated"
            self.success(f"{company.name} {status}")
        except self.model.DoesNotExist:
            self.error("Company not found")
```

**Template:**

```html
<div class="company-list">
    <!-- Header with search -->
    <div class="list-header">
        <h2>Companies</h2>

        <div class="search-bar">
            <input
                x-model="search"
                @input.debounce.300ms="call('search_items', {search: $el.value})"
                placeholder="Search companies..."
                type="search"
            >
            <button @click="call('clear_filters')" x-show="search || Object.keys(filters).length > 0">
                Clear
            </button>
        </div>

        <!-- Filters -->
        <div class="filters">
            <select @change="call('set_filters', {is_active: $el.value === '' ? null : $el.value === 'true'})">
                <option value="">All Companies</option>
                <option value="true">Active Only</option>
                <option value="false">Inactive Only</option>
            </select>
        </div>
    </div>

    <!-- Results info -->
    <div class="results-info" x-show="total_count > 0">
        Showing <strong x-text="showing_start"></strong>
        - <strong x-text="showing_end"></strong>
        of <strong x-text="total_count"></strong> companies
    </div>

    <!-- Create form -->
    <div class="create-form">
        <h3>Add Company</h3>
        {% nitro_input 'create_buffer.name' placeholder='Company name' %}
        {% nitro_input 'create_buffer.email' type='email' placeholder='Email' %}
        {% nitro_input 'create_buffer.phone' type='tel' placeholder='Phone' %}
        <button @click="call('create_item')" :disabled="isLoading">
            Add Company
        </button>
    </div>

    <!-- Companies table -->
    <table class="data-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <template x-for="company in items" :key="company.id">
                <tr :class="{'inactive': !company.is_active}">
                    <!-- Normal view -->
                    <template x-if="editing_id !== company.id">
                        <td x-text="company.name"></td>
                        <td x-text="company.email"></td>
                        <td x-text="company.phone"></td>
                        <td>
                            <span
                                :class="company.is_active ? 'badge-success' : 'badge-warning'"
                                x-text="company.is_active ? 'Active' : 'Inactive'"
                            ></span>
                        </td>
                        <td class="actions">
                            <button @click="call('start_edit', {id: company.id})" class="btn-sm">
                                Edit
                            </button>
                            <button @click="call('toggle_active', {id: company.id})" class="btn-sm">
                                <span x-text="company.is_active ? 'Deactivate' : 'Activate'"></span>
                            </button>
                            <button
                                @click="confirm('Delete?') && call('delete_item', {id: company.id})"
                                class="btn-sm btn-danger"
                            >
                                Delete
                            </button>
                        </td>
                    </template>

                    <!-- Edit view -->
                    <template x-if="editing_id === company.id && edit_buffer">
                        <td colspan="5">
                            <div class="inline-edit">
                                {% nitro_input 'edit_buffer.name' %}
                                {% nitro_input 'edit_buffer.email' type='email' %}
                                {% nitro_input 'edit_buffer.phone' type='tel' %}
                                <button @click="call('save_edit')">Save</button>
                                <button @click="call('cancel_edit')">Cancel</button>
                            </div>
                        </td>
                    </template>
                </tr>
            </template>
        </tbody>
    </table>

    <!-- Empty state -->
    <div x-show="items.length === 0" class="empty-state">
        <p x-show="!search && Object.keys(filters).length === 0">
            No companies yet. Add one above!
        </p>
        <p x-show="search || Object.keys(filters).length > 0">
            No companies match your search or filters.
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

        <span class="page-info">
            Page <strong x-text="page"></strong> of <strong x-text="num_pages"></strong>
        </span>

        <button
            @click="call('next_page')"
            :disabled="!has_next || isLoading"
        >
            Next
        </button>

        <!-- Items per page -->
        <select
            x-model.number="per_page"
            @change="call('set_per_page', {per_page: parseInt($el.value)})"
        >
            <option value="10">10 per page</option>
            <option value="25">25 per page</option>
            <option value="50">50 per page</option>
            <option value="100">100 per page</option>
        </select>
    </div>

    <!-- Messages -->
    <template x-for="msg in messages" :key="msg.text">
        <div :class="'alert alert-' + msg.level" x-text="msg.text"></div>
    </template>
</div>
```

## Advanced Patterns

### Custom Filtering

```python
def get_base_queryset(self, search='', filters=None):
    qs = self.model.objects.all()

    # Custom filter logic
    if filters:
        # Handle date range
        if 'date_from' in filters and filters['date_from']:
            qs = qs.filter(created_at__gte=filters['date_from'])

        if 'date_to' in filters and filters['date_to']:
            qs = qs.filter(created_at__lte=filters['date_to'])

        # Handle multi-select
        if 'categories' in filters and filters['categories']:
            qs = qs.filter(category_id__in=filters['categories'])

    # Apply search
    if search:
        qs = self.apply_search(qs, search)

    return qs.order_by(self.order_by)
```

### Annotations

```python
from django.db.models import Count, Sum

def get_base_queryset(self, search='', filters=None):
    qs = self.model.objects.annotate(
        order_count=Count('orders'),
        total_revenue=Sum('orders__total')
    )

    if search:
        qs = self.apply_search(qs, search)

    return qs.order_by(self.order_by)
```

## Performance Optimization

### 1. Use select_related and prefetch_related

```python
def get_base_queryset(self, search='', filters=None):
    qs = self.model.objects.select_related(
        'category',
        'owner'
    ).prefetch_related(
        'tags',
        'images'
    )

    # Apply search and filters...
    return qs.order_by(self.order_by)
```

### 2. Limit Search Results

```python
def search_items(self, search: str):
    self.state.search = search
    self.state.page = 1

    # Limit total results
    max_results = 1000
    # Pagination will handle the rest
```

### 3. Database Indexes

Ensure indexed fields for search and filters:

```python
class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)  # Indexed
    sku = models.CharField(max_length=50, db_index=True)    # Indexed
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['name', 'sku']),  # Composite index
        ]
```

## Best Practices

### 1. Always Override Buffer Types

```python
# ✅ Correct
class MyListState(BaseListState):
    items: list[ItemSchema] = []
    create_buffer: ItemFormSchema = Field(default_factory=ItemFormSchema)
    edit_buffer: Optional[ItemFormSchema] = None
```

### 2. Use Debouncing for Search

```html
<!-- ✅ Debounce to avoid too many requests -->
<input
    x-model="search"
    @input.debounce.300ms="call('search_items', {search: $el.value})"
>
```

### 3. Show Results Info

```html
<!-- ✅ Help users understand results -->
<div x-show="total_count > 0">
    Showing <span x-text="showing_start"></span>
    - <span x-text="showing_end"></span>
    of <span x-text="total_count"></span> results
</div>
```

### 4. Handle Empty States

```html
<!-- ✅ Different messages for empty vs no results -->
<div x-show="items.length === 0">
    <p x-show="!search">No items yet.</p>
    <p x-show="search">No items match your search.</p>
</div>
```

## See Also

- [CrudNitroComponent](crud-nitro-component.md) - Base CRUD operations
- [OwnershipMixin](../security/ownership-mixin.md) - Filter by ownership
- [State Management](../core-concepts/state-management.md) - Managing state
