# CLI Tools

Django Nitro provides command-line tools to accelerate component development.

## startnitro Command

Generate Nitro component boilerplate with a single command.

### Basic Usage

```bash
python manage.py startnitro ComponentName --app myapp
```

### Options

| Argument | Required | Description |
|----------|----------|-------------|
| `ComponentName` | Yes | Name of the component (must start with uppercase) |
| `--app` | Yes | Django app where component will be created |
| `--list` | No | Generate list component with pagination and search |
| `--crud` | No | Generate CRUD component (implies `--list`) |

### Examples

#### 1. Simple Component

Generate a basic component with minimal boilerplate:

```bash
python manage.py startnitro Counter --app dashboard
```

**Creates:**
- `dashboard/components/counter.py` - Component class
- `dashboard/templates/components/counter.html` - Template
- `dashboard/components/__init__.py` - Package file (if missing)

**Generated Component:**

```python
# dashboard/components/counter.py
from pydantic import BaseModel
from nitro import NitroComponent, register_component


class CounterState(BaseModel):
    """State schema for Counter component."""
    message: str = ""


@register_component
class Counter(NitroComponent[CounterState]):
    """
    Counter component.

    Usage:
        {% nitro_component 'Counter' %}
    """
    template_name = "components/counter.html"
    # state_class auto-inferred from Generic (v0.7.0)

    def get_initial_state(self, **kwargs):
        """Initialize component state."""
        return CounterState(
            message=kwargs.get('message', 'Hello from Counter!')
        )

    def example_action(self):
        """Example action method."""
        self.state.message = "Action executed!"
        self.success("Action completed successfully")
```

**Generated Template:**

```html
<!-- dashboard/templates/components/counter.html -->
<div>
    <h2>Counter</h2>

    <p x-text="message"></p>

    <button
        @click="call('example_action')"
        :disabled="isLoading"
        class="btn"
    >
        <span x-show="!isLoading">Execute Action</span>
        <span x-show="isLoading">Loading...</span>
    </button>
</div>
```

#### 2. List Component

Generate a component with pagination and search:

```bash
python manage.py startnitro ProductList --app products --list
```

**Creates a component with:**
- Pagination support
- Search functionality
- Item list display
- Pre-configured for Django models

**Generated Component:**

```python
# products/components/product_list.py
from pydantic import BaseModel, ConfigDict, Field
from nitro import BaseListComponent, BaseListState, register_component
# from products.models import Product


class ProductSchema(BaseModel):
    """Schema for Product item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    # TODO: Add more fields


class ProductFormSchema(BaseModel):
    """Form schema for creating/editing Product."""
    name: str = ""
    # TODO: Add more fields


class ProductListState(BaseListState):
    """State schema for ProductList component."""
    items: list[ProductSchema] = []
    create_buffer: ProductFormSchema = Field(default_factory=ProductFormSchema)
    edit_buffer: ProductFormSchema | None = None


@register_component
class ProductList(BaseListComponent[ProductListState]):
    """
    ProductList component with pagination, search, and CRUD.

    Usage:
        {% nitro_component 'ProductList' %}
    """
    template_name = "components/product_list.html"
    # state_class auto-inferred from Generic (v0.7.0)
    # model = Product  # TODO: Uncomment and import model

    # Configure search and pagination
    search_fields = ['name']  # TODO: Adjust search fields
    per_page = 20
    order_by = '-id'

    def get_base_queryset(self, search='', filters=None):
        """Override to add custom filtering or annotations."""
        qs = self.model.objects.all()

        if search:
            qs = self.apply_search(qs, search)

        if filters:
            qs = self.apply_filters(qs, filters)

        return qs.order_by(self.order_by)
```

**Generated Template:**

```html
<!-- products/templates/components/product_list.html -->
<div>
    <h2>ProductList</h2>

    <!-- Search bar -->
    <div class="mb-4">
        <input
            type="text"
            x-model="search"
            @input.debounce.300ms="call('search_items', {search: $el.value})"
            placeholder="Search..."
            class="border rounded px-4 py-2 w-full"
        >
    </div>

    <!-- Items list -->
    <div class="space-y-2">
        <template x-for="item in items" :key="item.id">
            <div class="border rounded p-4 flex justify-between items-center">
                <div>
                    <span x-text="item.name"></span>
                </div>
            </div>
        </template>
    </div>

    <!-- Pagination -->
    <div class="mt-4 flex justify-between items-center" x-show="num_pages > 1">
        <div>
            Page <span x-text="page"></span> of <span x-text="num_pages"></span>
        </div>
        <div class="space-x-2">
            <button
                @click="call('previous_page')"
                :disabled="!has_previous || isLoading"
                class="px-4 py-2 border rounded"
            >
                Previous
            </button>
            <button
                @click="call('next_page')"
                :disabled="!has_next || isLoading"
                class="px-4 py-2 border rounded"
            >
                Next
            </button>
        </div>
    </div>
</div>
```

#### 3. CRUD Component

Generate a full CRUD component with create, edit, delete:

```bash
python manage.py startnitro TaskManager --app tasks --crud
```

**Creates a component with:**
- All list features (pagination, search)
- Create form (create_buffer)
- Edit form (edit_buffer)
- Delete action
- Pre-built CRUD methods

**Additional Features in Template:**

```html
<!-- Create form -->
<div class="mb-4 p-4 bg-gray-50 rounded">
    <h3>Add New Item</h3>
    <input
        type="text"
        x-model="create_buffer.name"
        placeholder="Name"
        class="border rounded px-4 py-2 w-full mb-2"
    >
    <!-- TODO: Add more form fields -->

    <button
        @click="call('create_item')"
        :disabled="isLoading"
        class="bg-blue-500 text-white px-4 py-2 rounded"
    >
        Create
    </button>
</div>

<!-- Items with edit/delete buttons -->
<template x-for="item in items" :key="item.id">
    <div class="border rounded p-4 flex justify-between items-center">
        <div>
            <span x-text="item.name"></span>
        </div>
        <div class="space-x-2">
            <button
                @click="call('start_edit', {id: item.id})"
                class="text-blue-500"
            >
                Edit
            </button>
            <button
                @click="confirm('Delete?') && call('delete_item', {id: item.id})"
                class="text-red-500"
            >
                Delete
            </button>
        </div>
    </div>
</template>
```

## Next Steps After Generation

### 1. Import and Configure Model

```python
# Uncomment the model import
from tasks.models import Task

@register_component
class TaskManager(BaseListComponent[TaskManagerState]):
    # Uncomment the model
    model = Task

    # Adjust search fields to match your model
    search_fields = ['title', 'description', 'status']
```

### 2. Add Model Fields to Schemas

```python
class TaskSchema(BaseModel):
    """Schema for Task item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str = ""
    description: str = ""
    status: str = "pending"
    due_date: str | None = None
    created_at: str | None = None


class TaskFormSchema(BaseModel):
    """Form schema for creating/editing Task."""
    title: str = ""
    description: str = ""
    status: str = "pending"
    due_date: str = ""
```

### 3. Update Template with New Fields

```html
<div class="card">
    <h3 x-text="item.title"></h3>
    <p x-text="item.description"></p>
    <span x-text="item.status" class="badge"></span>
    <small x-text="item.due_date"></small>
</div>
```

### 4. Add Custom Actions

```python
@register_component
class TaskManager(BaseListComponent[TaskManagerState]):
    # ... existing code ...

    def toggle_status(self, id: int):
        """Toggle task status between pending and completed."""
        task = self.model.objects.get(id=id)
        task.status = 'completed' if task.status == 'pending' else 'pending'
        task.save()

        # Update state
        for item in self.state.items:
            if item.id == id:
                item.status = task.status
                break

        self.success(f"Task marked as {task.status}")
```

## Validation and Requirements

### Component Name Rules

```bash
# ✅ Valid names (must start with uppercase)
python manage.py startnitro ProductList --app products
python manage.py startnitro UserProfile --app accounts
python manage.py startnitro APIManager --app api

# ❌ Invalid names (lowercase start)
python manage.py startnitro productList --app products
# Error: Component name must start with an uppercase letter
```

### App Must Exist

```bash
# ✅ App exists in INSTALLED_APPS
python manage.py startnitro TaskList --app tasks

# ❌ App doesn't exist
python manage.py startnitro TaskList --app nonexistent
# Error: App "nonexistent" not found
```

### File Must Not Exist

```bash
# ❌ Component file already exists
python manage.py startnitro TaskList --app tasks
# Error: Component file already exists: tasks/components/task_list.py
```

## Tips and Best Practices

### 1. Start with CRUD for Most Use Cases

Most components benefit from CRUD operations:

```bash
# Start with --crud for data management components
python manage.py startnitro CompanyList --app companies --crud
python manage.py startnitro InvoiceManager --app billing --crud
```

### 2. Use Descriptive Names

```bash
# ✅ Good - Clear and specific
python manage.py startnitro ProductCatalog --app products --crud
python manage.py startnitro UserDashboard --app dashboard
python manage.py startnitro PaymentHistory --app billing --list

# ❌ Bad - Too generic
python manage.py startnitro List --app products
python manage.py startnitro Manager --app tasks
```

### 3. Organize by Feature

Group related components in the same app:

```bash
# E-commerce app structure
python manage.py startnitro ProductList --app shop --crud
python manage.py startnitro CategoryManager --app shop --crud
python manage.py startnitro ShoppingCart --app shop

# User management
python manage.py startnitro UserList --app accounts --crud
python manage.py startnitro ProfileEditor --app accounts
```

### 4. Customize After Generation

The generated code is a starting point. Always:

1. ✅ Add proper field validation
2. ✅ Implement custom actions
3. ✅ Add permission checks
4. ✅ Customize templates for your design
5. ✅ Add proper error handling

## Common Patterns

### Pattern 1: Master-Detail Components

Generate both list and detail components:

```bash
# Master list
python manage.py startnitro PropertyList --app properties --crud

# Detail view
python manage.py startnitro PropertyDetail --app properties
```

### Pattern 2: Nested Components

Create parent and child components:

```bash
# Parent (property)
python manage.py startnitro PropertyDetail --app properties

# Child (tenants for that property)
python manage.py startnitro TenantList --app properties --crud
```

### Pattern 3: Wizard Components

Create step-by-step components:

```bash
python manage.py startnitro OnboardingStep1 --app onboarding
python manage.py startnitro OnboardingStep2 --app onboarding
python manage.py startnitro OnboardingStep3 --app onboarding
```

## Troubleshooting

### "App not found" Error

```bash
# Check your INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    # ...
    'tasks',  # Make sure your app is listed
]
```

### "Component already exists" Error

```bash
# Rename or delete the existing component first
rm myapp/components/my_component.py
rm myapp/templates/components/my_component.html

# Or choose a different name
python manage.py startnitro MyComponentV2 --app myapp
```

### Import Errors

```python
# Make sure to import the component in your app's apps.py or views
# Option 1: In apps.py
from django.apps import AppConfig

class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        import tasks.components.task_manager  # Import component

# Option 2: In views.py
from tasks.components.task_manager import TaskManager
```

## See Also

- [API Reference: CLI Commands](../api-reference.md#cli-commands-v040)
- [Components Guide](components.md)
- [BaseListComponent](../components/base-list-component.md)
- [CrudNitroComponent](../components/crud-nitro-component.md)
