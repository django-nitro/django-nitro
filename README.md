# Django Nitro 🚀

**Build reactive Django components with AlpineJS - No JavaScript required**

Django Nitro is a modern library for building reactive, stateful components in Django applications. Inspired by Django Unicorn and Laravel Livewire, but built on top of AlpineJS and Django Ninja for a lightweight, performant experience.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2+](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)

---

## What's New in v0.6.0 (Latest)

**Performance & Code Quality Improvements:**
- ⚡ **TypeAdapter Caching** - 1-5ms performance boost per request by caching Pydantic TypeAdapters at class level
- 🎯 **Default Debounce** - `nitro_model` now has 200ms debounce by default, reducing server load by ~80% on text inputs
- 🧹 **Code Deduplication** - New `nitro.utils` module eliminates 50+ lines of repetitive code
- 🔧 **Django 5.2 Compatibility** - Added `django-template-partials` as optional dependency for Django 5.2 users (Django 6.0+ has built-in partials)
- 📋 **Form Field Template Tags (v0.6.0)** - Complete form abstractions: `{% nitro_input %}`, `{% nitro_select %}`, `{% nitro_checkbox %}`, `{% nitro_textarea %}`
- 🚀 **Moved to Beta** - Framework is now stable and production-ready

**Installation for Django 5.2:**
```bash
pip install django-nitro[django52]
```

**Installation for Django 6.0+:**
```bash
pip install django-nitro  # No extras needed
```

## What's New in v0.5.0

- **Advanced Template Tags** - New `nitro_attr`, `nitro_if`, `nitro_disabled`, and `nitro_file` tags for cleaner, more expressive templates
- **Nested Fields Support** - Access nested state with dot notation (`user.profile.name`)
- **File Upload System** - Streamlined file uploads with the `nitro_file` template tag
- **Debugging Tools** - `NITRO_DEBUG` mode and Django Debug Toolbar integration panel

---

## Why Django Nitro?

- ✅ **Zero JavaScript** - Write reactive UIs entirely in Python
- ✅ **Type-Safe** - Full Pydantic integration with generics for bulletproof state management
- ✅ **Secure by Default** - Built-in integrity verification prevents client-side tampering
- ✅ **Lightweight** - AlpineJS (~15KB) vs Morphdom (~50KB)
- ✅ **Fast** - Django Ninja API layer for optimal performance
- ✅ **DRY** - Pre-built CRUD operations like Django REST Framework's ViewSets

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
  - [NitroComponent (Basic)](#nitrocomponent-basic)
  - [ModelNitroComponent (ORM Integration)](#modelnitrocomponent-orm-integration)
  - [CrudNitroComponent (Full CRUD)](#crudnitrocomponent-full-crud)
  - [BaseListComponent (Pagination + Search + Filters)](#baselistcomponent-pagination--search--filters)
- [Security Mixins & Authentication](#security-mixins--authentication)
  - [Request User Helpers](#request-user-helpers)
  - [OwnershipMixin](#ownershipmixin)
  - [TenantScopedMixin](#tenantscopedmixin)
  - [PermissionMixin](#permissionmixin)
- [State Management](#state-management)
  - [Nested Fields (Dot Notation)](#nested-fields-dot-notation-v050)
- [Actions & Methods](#actions--methods)
- [Template Integration](#template-integration)
  - [Advanced Template Tags (v0.5.0)](#advanced-template-tags-v050)
  - [Form Field Template Tags (v0.6.0)](#form-field-template-tags-v060)
- [Security & Integrity](#security--integrity)
- [Messages & Notifications](#messages--notifications)
- [Events & Inter-Component Communication](#events--inter-component-communication-v040)
- [CLI Tools](#cli-tools-v040)
- [SEO-Friendly Template Tags](#seo-friendly-template-tags-v040)
- [Performance Optimization](#performance-optimization-v040)
- [File Uploads](#file-uploads)
- [Debugging](#debugging)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)
- [Comparison to Alternatives](#comparison-to-alternatives)

---

## Installation

```bash
pip install django-nitro
```

### Requirements

- Python 3.12+
- Django 5.2+
- django-ninja 1.4.0+
- pydantic 2.0+

### Setup

**1. Add to INSTALLED_APPS**

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'nitro',
    # your apps here
]
```

**2. Include Nitro API URLs**

```python
# urls.py
from django.urls import path
from nitro.api import api

urlpatterns = [
    # ...
    path("api/nitro/", api.urls),  # Important: must be under /api/nitro/
]
```

**3. Add Alpine and Nitro JS to your base template**

**Option A: Modern (v0.4.0+) - Recommended**

```html
<!-- templates/base.html -->
{% load nitro_tags %}
<!DOCTYPE html>
<html>
<head>
    <title>My App</title>
    <!-- Alpine JS (required) -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <!-- Nitro CSS and JS (includes toast styles) -->
    {% nitro_scripts %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

**Option B: Manual**

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>My App</title>
    <!-- Alpine JS (required) -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body>
    {% block content %}{% endblock %}

    <!-- Nitro JS (load AFTER Alpine) -->
    <link rel="stylesheet" href="{% static 'nitro/nitro.css' %}">
    <script src="{% static 'nitro/nitro.js' %}"></script>
</body>
</html>
```

**4. (Optional) Configure Nitro Settings (v0.4.0+)**

```python
# settings.py
NITRO = {
    'TOAST_ENABLED': True,
    'TOAST_POSITION': 'top-right',  # top-right, top-left, top-center, bottom-right, bottom-left, bottom-center
    'TOAST_DURATION': 3000,  # milliseconds
    'TOAST_STYLE': 'default',  # default, minimal, bordered
}
```

**5. Run collectstatic (if in production)**

```bash
python manage.py collectstatic
```

---

## Quick Start

Let's build a simple counter component to understand the basics.

### 1. Define the Component

```python
# myapp/components/counter.py
from pydantic import BaseModel
from nitro.base import NitroComponent
from nitro.registry import register_component


class CounterState(BaseModel):
    """State schema for the counter component."""
    count: int = 0
    step: int = 1


@register_component
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    state_class = CounterState

    def get_initial_state(self, **kwargs):
        """Initialize the component state."""
        return CounterState(
            count=kwargs.get('initial', 0),
            step=kwargs.get('step', 1)
        )

    def increment(self):
        """Action: increment the counter."""
        self.state.count += self.state.step
        self.success(f"Count increased to {self.state.count}")

    def decrement(self):
        """Action: decrement the counter."""
        self.state.count -= self.state.step

    def reset(self):
        """Action: reset to zero."""
        self.state.count = 0
```

### 2. Create the Template

```html
<!-- templates/components/counter.html -->
<div class="counter-widget">
    <h2>Counter: <span x-text="count"></span></h2>

    <div class="controls">
        <button @click="call('decrement')" :disabled="isLoading">-</button>
        <button @click="call('reset')" :disabled="isLoading">Reset</button>
        <button @click="call('increment')" :disabled="isLoading">+</button>
    </div>

    <!-- Show loading state -->
    <div x-show="isLoading" class="loading">Updating...</div>

    <!-- Show messages -->
    <template x-for="msg in messages" :key="msg.text">
        <div class="alert" x-text="msg.text"></div>
    </template>
</div>
```

### 3. Use in Your View

```python
# myapp/views.py
from django.shortcuts import render
from myapp.components.counter import Counter

def counter_page(request):
    # Initialize the component with custom values
    component = Counter(request=request, initial=10, step=5)
    return render(request, 'counter_page.html', {'counter': component})
```

```html
<!-- templates/counter_page.html -->
{% extends "base.html" %}

{% block content %}
    <h1>Counter Demo</h1>
    {{ counter.render }}
{% endblock %}
```

**That's it!** You now have a fully reactive counter component without writing any JavaScript.

---

## Core Concepts

Django Nitro provides three base classes for different use cases. Choose the one that fits your needs.

### NitroComponent (Basic)

**Use when:** You need full control over state and actions.

**Best for:** Custom components, widgets, forms that don't map to Django models.

```python
from pydantic import BaseModel, EmailStr
from nitro.base import NitroComponent
from nitro.registry import register_component


class ContactFormState(BaseModel):
    name: str = ""
    email: EmailStr | str = ""
    message: str = ""
    submitted: bool = False


@register_component
class ContactForm(NitroComponent[ContactFormState]):
    template_name = "components/contact_form.html"
    state_class = ContactFormState

    def get_initial_state(self, **kwargs):
        return ContactFormState()

    def submit(self):
        """Custom action to handle form submission."""
        if not self.state.name or not self.state.message:
            self.error("Name and message are required")
            return

        # Send email, save to DB, etc.
        send_contact_email(
            name=self.state.name,
            email=self.state.email,
            message=self.state.message
        )

        self.state.submitted = True
        self.success("Message sent successfully!")
```

```html
<!-- templates/components/contact_form.html -->
<form x-show="!submitted">
    <input type="text" x-model="name" placeholder="Jearel Alcantara">
    <span x-show="errors.name" x-text="errors.name" class="error"></span>

    <input type="email" x-model="email" placeholder="Your email">

    <textarea x-model="message" placeholder="Your message"></textarea>
    <span x-show="errors.message" x-text="errors.message" class="error"></span>

    <button @click="call('submit')" :disabled="isLoading">
        Send Message
    </button>
</form>

<div x-show="submitted" class="success-message">
    <h3>Thank you!</h3>
    <p>We'll get back to you soon.</p>
</div>
```

---

### ModelNitroComponent (ORM Integration)

**Use when:** Your component represents a single Django model instance.

**Best for:** Detail views, profile editors, single-item forms.

**Features:**
- Automatic model loading via `pk` or `id`
- Built-in `refresh()` method to reload from database
- Automatic secure field detection (ids and foreign keys)

```python
from django.db import models
from pydantic import BaseModel
from nitro.base import ModelNitroComponent
from nitro.registry import register_component


# Django Model
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published = models.BooleanField(default=False)
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


# Pydantic Schema
class BlogPostSchema(BaseModel):
    id: int
    title: str
    content: str
    published: bool
    author_id: int

    class Config:
        from_attributes = True


# Component
@register_component
class BlogPostEditor(ModelNitroComponent[BlogPostSchema]):
    template_name = "components/blog_post_editor.html"
    state_class = BlogPostSchema
    model = BlogPost

    # No need to define get_initial_state - it's automatic!
    # Just pass pk in the view: BlogPostEditor(request, pk=123)

    def toggle_published(self):
        """Toggle the published status."""
        obj = self.get_object(self.state.id)
        obj.published = not obj.published
        obj.save()
        self.refresh()  # Reload from database
        self.success("Post updated!")

    def save_content(self):
        """Save the current content."""
        obj = self.get_object(self.state.id)
        obj.title = self.state.title
        obj.content = self.state.content
        obj.save()
        self.success("Changes saved!")
```

**Usage in view:**

```python
def edit_post(request, post_id):
    editor = BlogPostEditor(request=request, pk=post_id)
    return render(request, 'edit_post.html', {'editor': editor})
```

**Template:**

```html
<!-- templates/components/blog_post_editor.html -->
<div class="editor">
    <input type="text" x-model="title" placeholder="Post title">

    <textarea x-model="content" rows="10"></textarea>

    <div class="actions">
        <button @click="call('save_content')">Save Draft</button>
        <button @click="call('toggle_published')">
            <span x-text="published ? 'Unpublish' : 'Publish'"></span>
        </button>
    </div>

    <!-- Messages -->
    <template x-for="msg in messages">
        <div :class="'alert-' + msg.level" x-text="msg.text"></div>
    </template>
</div>
```

---

### CrudNitroComponent (Full CRUD)

**Use when:** You need a list view with create, read, update, delete operations.

**Best for:** Admin panels, data tables, list management.

**Features:**
- Pre-built `create_item()`, `delete_item()`, `start_edit()`, `save_edit()`, `cancel_edit()` methods
- Built-in `create_buffer` and `edit_buffer` for form handling
- Automatic inline editing support

```python
from typing import Optional
from pydantic import BaseModel, Field
from nitro.base import CrudNitroComponent
from nitro.registry import register_component


# Schema for a single task
class TaskSchema(BaseModel):
    id: int
    title: str
    completed: bool = False

    class Config:
        from_attributes = True


# Schema for creating/editing tasks (no id required)
class TaskFormSchema(BaseModel):
    title: str = ""
    completed: bool = False


# State schema for the component
class TaskListState(BaseModel):
    tasks: list[TaskSchema] = []
    create_buffer: TaskFormSchema = Field(default_factory=TaskFormSchema)
    edit_buffer: Optional[TaskFormSchema] = None
    editing_id: Optional[int] = None


@register_component
class TaskList(CrudNitroComponent[TaskListState]):
    template_name = "components/task_list.html"
    state_class = TaskListState
    model = Task  # Your Django model

    def get_initial_state(self, **kwargs):
        return TaskListState(
            tasks=[TaskSchema.model_validate(t) for t in Task.objects.all()]
        )

    def refresh(self):
        """Reload tasks from database."""
        self.state.tasks = [
            TaskSchema.model_validate(t)
            for t in Task.objects.all().order_by('-id')
        ]

    def toggle_completed(self, id: int):
        """Custom action to toggle task completion."""
        task = Task.objects.get(id=id)
        task.completed = not task.completed
        task.save()
        self.refresh()

    # create_item() - already implemented ✅
    # delete_item(id) - already implemented ✅
    # start_edit(id) - already implemented ✅
    # save_edit() - already implemented ✅
    # cancel_edit() - already implemented ✅
```

**Template:**

```html
<!-- templates/components/task_list.html -->
<div class="task-list">
    <!-- Create new task -->
    <div class="create-form">
        <input
            type="text"
            x-model="create_buffer.title"
            placeholder="New task..."
            @keyup.enter="call('create_item')"
        >
        <button @click="call('create_item')">Add</button>
    </div>

    <!-- Task list -->
    <ul>
        <template x-for="task in tasks" :key="task.id">
            <li>
                <!-- Normal view -->
                <template x-if="editing_id !== task.id">
                    <div class="task-item">
                        <input
                            type="checkbox"
                            :checked="task.completed"
                            @click="call('toggle_completed', {id: task.id})"
                        >
                        <span x-text="task.title"></span>
                        <button @click="call('start_edit', {id: task.id})">Edit</button>
                        <button @click="call('delete_item', {id: task.id})">Delete</button>
                    </div>
                </template>

                <!-- Edit view -->
                <template x-if="editing_id === task.id && edit_buffer">
                    <div class="task-edit">
                        <input type="text" x-model="edit_buffer.title">
                        <button @click="call('save_edit')">Save</button>
                        <button @click="call('cancel_edit')">Cancel</button>
                    </div>
                </template>
            </li>
        </template>
    </ul>

    <!-- Messages -->
    <template x-for="msg in messages">
        <div :class="'alert-' + msg.level" x-text="msg.text"></div>
    </template>
</div>
```

---

### BaseListComponent (Pagination + Search + Filters)

**Use when:** You need a list view with pagination, search, and filters.

**Best for:** Admin panels, data tables, dashboards, any paginated list.

**Features:**
- Pre-built pagination with Django Paginator
- Full-text search across configurable fields
- Dynamic filtering
- All CRUD operations (inherited from CrudNitroComponent)
- Navigation methods: `next_page()`, `previous_page()`, `go_to_page()`, `set_per_page()`
- Search and filter methods: `search_items()`, `set_filters()`, `clear_filters()`
- Rich metadata: `total_count`, `showing_start`, `showing_end` for UX

```python
from pydantic import BaseModel
from nitro.list import BaseListComponent, BaseListState
from nitro.registry import register_component
from myapp.models import Company


# Schema for a single company
class CompanySchema(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    is_active: bool

    class Config:
        from_attributes = True


# Schema for creating/editing (no id)
class CompanyFormSchema(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""


# State schema for the list
class CompanyListState(BaseListState):
    items: list[CompanySchema] = []
    # search, page, per_page, filters, etc. inherited from BaseListState

    # IMPORTANT: Must specify buffer types explicitly
    # (BaseListState uses Any, which causes inference issues)
    create_buffer: CompanyFormSchema = Field(default_factory=CompanyFormSchema)
    edit_buffer: Optional[CompanyFormSchema] = None


@register_component
class CompanyList(BaseListComponent[CompanyListState]):
    template_name = "components/company_list.html"
    state_class = CompanyListState
    model = Company

    # Configure search and pagination
    search_fields = ['name', 'email', 'phone']
    per_page = 25
    order_by = '-created_at'

    # All these methods are pre-built:
    # - Pagination: next_page(), previous_page(), go_to_page(), set_per_page()
    # - Search: search_items(search)
    # - Filters: set_filters(**filters), clear_filters()
    # - CRUD: create_item(), delete_item(), start_edit(), save_edit(), cancel_edit()
```

**Template:**

```html
<!-- templates/components/company_list.html -->
<div class="company-list">

    <!-- Search bar -->
    <div class="search-bar">
        <input
            type="text"
            x-model="search"
            @input.debounce.300ms="call('search_items', {search: $el.value})"
            placeholder="Search companies..."
        >
        <button @click="call('clear_filters')">Clear</button>
    </div>

    <!-- Results info -->
    <div class="results-info" x-show="total_count > 0">
        Showing <strong x-text="showing_start"></strong>
        - <strong x-text="showing_end"></strong>
        of <strong x-text="total_count"></strong> results
    </div>

    <!-- Items table -->
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <template x-for="company in items" :key="company.id">
                <tr>
                    <td x-text="company.name"></td>
                    <td x-text="company.email"></td>
                    <td x-text="company.phone"></td>
                    <td>
                        <button @click="call('start_edit', {id: company.id})">Edit</button>
                        <button @click="call('delete_item', {id: company.id})">Delete</button>
                    </td>
                </tr>
            </template>
        </tbody>
    </table>

    <!-- Pagination -->
    <div class="pagination">
        <button
            @click="call('previous_page')"
            :disabled="!has_previous || isLoading"
        >
            Previous
        </button>

        <span>
            Page <strong x-text="page"></strong> of <strong x-text="num_pages"></strong>
        </span>

        <button
            @click="call('next_page')"
            :disabled="!has_next || isLoading"
        >
            Next
        </button>

        <!-- Items per page selector -->
        <select
            x-model="per_page"
            @change="call('set_per_page', {per_page: parseInt($el.value)})"
        >
            <option value="10">10</option>
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
        </select>
    </div>

</div>
```

**Advanced: Custom Filtering**

Override `get_base_queryset()` for custom logic:

```python
class CompanyList(BaseListComponent[CompanyListState]):
    def get_base_queryset(self, search='', filters=None):
        # Only show companies owned by current user
        qs = self.model.objects.filter(owner=self.request.user)

        # Apply standard search
        if search:
            qs = self.apply_search(qs, search)

        # Apply filters
        if filters:
            qs = self.apply_filters(qs, filters)

        # Custom ordering
        return qs.select_related('owner').order_by(self.order_by)
```

**Usage in view:**

```python
def company_list_page(request):
    component = CompanyList(request=request)
    return render(request, 'company_list_page.html', {'companies': component})
```

---

## Security Mixins & Authentication

Django Nitro v0.3.0+ provides powerful security mixins and authentication helpers for common authorization patterns. These mixins help you implement **ownership-based access control**, **multi-tenant data isolation**, and **custom permissions** with minimal code.

> **📚 Full Documentation:** For complete guides and examples, visit the [Security Documentation](https://django-nitro.github.io/django-nitro/security/overview/)

### Request User Helpers

Every `NitroComponent` has built-in properties and methods for working with authenticated users:

```python
@register_component
class MyComponent(NitroComponent[MyState]):
    def my_action(self):
        # ✅ Shortcut to request.user (returns None if not authenticated)
        user = self.current_user

        # ✅ Check if user is authenticated
        if self.is_authenticated:
            user.profile.increment_action_count()

        # ✅ Enforce authentication requirement
        if not self.require_auth("You must be logged in"):
            return  # Stops execution and shows error message

        # Continue with authenticated user...
```

**Properties:**
- `current_user` - Returns `request.user` if authenticated, otherwise `None`
- `is_authenticated` - Returns `True` if user is authenticated

**Methods:**
- `require_auth(message="Authentication required")` - Enforces auth, shows error if not authenticated

---

### OwnershipMixin

**Use when:** You need to filter data to show only items owned by the current user.

**Best for:** User dashboards, personal data management, user-owned resources.

```python
from nitro.security import OwnershipMixin
from nitro.list import BaseListComponent

@register_component
class MyDocuments(OwnershipMixin, BaseListComponent[DocumentListState]):
    model = Document
    owner_field = 'user'  # Field name linking to user (default: 'user')
    search_fields = ['title', 'description']

    # That's it! No need to override get_base_queryset()
    # Automatically filters to current user's documents
```

**How it works (v0.5.1+):**
- **Automatically** applies filter: `queryset.filter(user=request.user)`
- Returns empty queryset if user is not authenticated
- Override `owner_field` to customize the field name (e.g., `'author'`, `'created_by'`)
- **No manual override required** - BaseListComponent auto-detects and applies the mixin

**Example:**
```python
class MyTasksState(BaseListState):
    items: list[TaskSchema] = []

@register_component
class MyTasks(OwnershipMixin, BaseListComponent[MyTasksState]):
    model = Task
    owner_field = 'owner'
    search_fields = ['title', 'description']

    # Users can only see/edit their own tasks
```

---

### TenantScopedMixin

**Use when:** Building multi-tenant SaaS applications where data must be isolated by organization/tenant.

**Best for:** SaaS apps, team workspaces, organization-based access control.

```python
from nitro.security import TenantScopedMixin
from nitro.list import BaseListComponent

@register_component
class CompanyProjects(TenantScopedMixin, BaseListComponent[ProjectListState]):
    model = Project
    tenant_field = 'organization'  # Field linking to tenant (default: 'organization')
    search_fields = ['name', 'description']

    def get_user_tenant(self):
        """Override to return current user's tenant/organization."""
        return self.request.user.current_organization

    # That's it! Automatically filters by tenant (v0.5.1+)
```

**Required:** You must override `get_user_tenant()` to return the current user's tenant.

**How it works (v0.5.1+):**
- **Automatically** applies filter: `queryset.filter(organization=current_organization)`
- Returns empty queryset if user has no tenant
- **No manual override of get_base_queryset() required**

**Example with profile-based tenancy:**
```python
@register_component
class TeamDocuments(TenantScopedMixin, BaseListComponent[DocumentListState]):
    model = Document
    tenant_field = 'team'

    def get_user_tenant(self):
        # Get tenant from user profile
        if hasattr(self.request.user, 'profile'):
            return self.request.user.profile.current_team
        return None
```

---

### PermissionMixin

**Use when:** You need custom permission logic beyond Django's built-in permissions.

**Best for:** Complex authorization rules, role-based access control (RBAC), custom business logic.

```python
from nitro.security import PermissionMixin
from nitro.base import CrudNitroComponent

@register_component
class AdminPanel(PermissionMixin, CrudNitroComponent[AdminState]):
    model = Settings

    def check_permission(self, action: str) -> bool:
        """Override with custom permission logic."""
        user = self.current_user

        if not user or not user.is_authenticated:
            return False

        # Custom role-based logic
        if action == 'delete':
            return user.is_superuser

        if action in ['create', 'edit']:
            return user.has_perm('settings.change_settings')

        return True  # Allow read by default

    def delete_item(self, id: int):
        # Enforce permission before deletion
        if not self.enforce_permission('delete', "Only admins can delete"):
            return

        super().delete_item(id)
```

**Methods:**
- `check_permission(action: str) -> bool` - Override with your logic
- `enforce_permission(action: str, error_message: str = None) -> bool` - Check and show error if denied

**Example with subscription-based permissions:**
```python
class ProjectManager(PermissionMixin, CrudNitroComponent[ProjectState]):
    def check_permission(self, action: str) -> bool:
        user = self.current_user
        if not user:
            return False

        # Check subscription tier
        if action == 'create':
            if user.subscription_tier == 'free':
                # Check project count limit
                return user.projects.count() < 3
            return True  # Paid users unlimited

        return True

    def create_item(self):
        if not self.enforce_permission('create',
            "Free tier limited to 3 projects. Upgrade to create more."):
            return

        super().create_item()
```

---

### Combining Mixins

You can combine multiple security mixins for powerful authorization:

```python
@register_component
class TeamDocuments(
    OwnershipMixin,      # Filter by current user
    TenantScopedMixin,   # Filter by user's organization
    PermissionMixin,     # Custom permission logic
    BaseListComponent[DocumentListState]
):
    model = Document
    owner_field = 'created_by'
    tenant_field = 'organization'

    def get_user_tenant(self):
        return self.request.user.profile.organization

    def check_permission(self, action: str) -> bool:
        user = self.current_user
        if not user:
            return False

        # Managers can do everything
        if user.role == 'manager':
            return True

        # Members can read and create, but not delete
        if action == 'delete':
            return False

        return True
```

**MRO (Method Resolution Order) matters:**
- Mixins are applied **left to right**
- `OwnershipMixin` filters first, then `TenantScopedMixin`, then your component
- Both filters are combined (AND logic)

---

## State Management

### How State Works

1. **Server-Side (Python)**: State is defined as a Pydantic model
2. **Rendered to HTML**: State is embedded in the template as JSON
3. **Client-Side (Alpine)**: State becomes reactive Alpine data
4. **On Action**: State is sent back to server, processed, and returned
5. **Auto-Sync**: Alpine updates the UI reactively

### State Schema Best Practices

```python
from pydantic import BaseModel, Field, validator
from typing import Optional


class MyComponentState(BaseModel):
    # Use type hints for validation
    count: int = 0
    email: str = ""

    # Use Optional for nullable fields
    selected_id: Optional[int] = None

    # Use Field for defaults and validation
    items: list[str] = Field(default_factory=list)

    # Custom validation
    @validator('email')
    def email_must_be_valid(cls, v):
        if v and '@' not in v:
            raise ValueError('Invalid email')
        return v

    class Config:
        # Enable ORM mode for Django models
        from_attributes = True
```

### Accessing State in Templates

```html
<!-- Direct access to state properties -->
<div x-text="count"></div>
<div x-text="email"></div>
<div x-text="selected_id"></div>

<!-- Loop through arrays -->
<template x-for="item in items" :key="item">
    <div x-text="item"></div>
</template>

<!-- Conditional rendering -->
<div x-show="count > 0">Count is positive</div>
<div x-show="selected_id !== null">Something is selected</div>
```

### Nested Fields (Dot Notation) (v0.5.0)

Access deeply nested state properties using dot notation in templates:

```python
from pydantic import BaseModel

class ProfileSchema(BaseModel):
    name: str = ""
    avatar_url: str = ""

class SettingsSchema(BaseModel):
    theme: str = "light"
    notifications: bool = True

class UserState(BaseModel):
    profile: ProfileSchema = Field(default_factory=ProfileSchema)
    settings: SettingsSchema = Field(default_factory=SettingsSchema)


@register_component
class UserDashboard(NitroComponent[UserState]):
    template_name = "components/user_dashboard.html"
    state_class = UserState
```

```html
<!-- Access nested fields with dot notation -->
<h1>{% nitro_text 'profile.name' %}</h1>
<img :src="profile.avatar_url" alt="Avatar">

<!-- Bind to nested fields -->
<input type="text" x-model="profile.name" placeholder="Your name">
<select x-model="settings.theme">
    <option value="light">Light</option>
    <option value="dark">Dark</option>
</select>

<!-- Conditionals with nested fields -->
<div x-show="settings.notifications">
    Notifications are enabled
</div>
```

Nitro automatically handles nested field updates, syncing changes back to the server while maintaining the full state structure.

---

## Actions & Methods

### Defining Actions

Any public method (not starting with `_`) on your component can be called from the template.

```python
class MyComponent(NitroComponent[MyState]):
    # ✅ Can be called from template
    def increment(self):
        self.state.count += 1

    # ✅ Can accept parameters
    def add(self, amount: int):
        self.state.count += amount

    # ✅ Can use request object
    def save_for_user(self):
        if self.request.user.is_authenticated:
            # save logic
            pass

    # ❌ Cannot be called (starts with _)
    def _internal_helper(self):
        pass
```

### Calling Actions from Templates

```html
<!-- Simple call -->
<button @click="call('increment')">+1</button>

<!-- With parameters -->
<button @click="call('add', {amount: 5})">+5</button>

<!-- With debouncing -->
<input
    x-model="search"
    @input.debounce.300ms="call('search')"
>

<!-- On form submit -->
<form @submit.prevent="call('submit_form')">
    <button type="submit">Submit</button>
</form>
```

---

## Template Integration

### Available Variables

Every Nitro component template has access to:

```html
<!-- State properties (direct access) -->
<div x-text="count"></div>
<div x-text="email"></div>

<!-- Internal properties -->
<div x-show="isLoading">Loading...</div>

<!-- Errors (per-field validation errors) -->
<span x-show="errors.email" x-text="errors.email"></span>

<!-- Messages (success/error notifications) -->
<template x-for="msg in messages">
    <div x-text="msg.text"></div>
</template>
```

### Alpine Directives Cheatsheet

```html
<!-- Text content -->
<div x-text="count"></div>

<!-- HTML content -->
<div x-html="content"></div>

<!-- Attributes -->
<button :disabled="isLoading">Click</button>
<input :class="{'error': errors.email}">

<!-- Show/Hide (keeps in DOM) -->
<div x-show="count > 0">Visible when count > 0</div>

<!-- If/Else (removes from DOM) -->
<template x-if="count > 0">
    <div>Count is positive</div>
</template>

<!-- Loops -->
<template x-for="item in items" :key="item.id">
    <div x-text="item.name"></div>
</template>

<!-- Two-way binding -->
<input x-model="email" type="email">

<!-- Events -->
<button @click="call('increment')">Click</button>
<input @keyup.enter="call('submit')">
<input @input.debounce.500ms="call('search')">
```

### Advanced Template Tags (v0.5.0)

Django Nitro v0.5.0 introduces powerful template tags for cleaner, more expressive templates.

#### `nitro_attr` - Dynamic Attributes

Set any HTML attribute dynamically based on state:

```html
{% load nitro_tags %}

<!-- Dynamic class based on state -->
<div {% nitro_attr 'class' 'status' %}>
    Status indicator
</div>
<!-- Renders: <div class="active"> if status="active" -->

<!-- Dynamic href -->
<a {% nitro_attr 'href' 'profile_url' %}>View Profile</a>

<!-- With fallback value -->
<img {% nitro_attr 'src' 'avatar_url' fallback='/static/default-avatar.png' %}>
```

#### `nitro_if` - Server-Side Conditionals

Render content conditionally based on state (SEO-friendly):

```html
{% load nitro_tags %}

<!-- Show content based on boolean state -->
{% nitro_if 'is_premium' %}
    <div class="premium-badge">Premium Member</div>
{% end_nitro_if %}

<!-- With else clause -->
{% nitro_if 'is_authenticated' %}
    <span>Welcome back!</span>
{% nitro_else %}
    <a href="/login">Sign In</a>
{% end_nitro_if %}

<!-- Comparison operators -->
{% nitro_if 'cart_count' gt 0 %}
    <span class="badge">{{ cart_count }}</span>
{% end_nitro_if %}
```

#### `nitro_disabled` - Conditional Button States

Disable buttons based on state conditions:

```html
{% load nitro_tags %}

<!-- Disable when loading -->
<button @click="call('submit')" {% nitro_disabled 'isLoading' %}>
    Submit
</button>

<!-- Disable based on validation -->
<button @click="call('save')" {% nitro_disabled 'form_invalid' %}>
    Save Changes
</button>

<!-- Disable with compound conditions -->
<button
    @click="call('checkout')"
    {% nitro_disabled 'cart_empty' %}
    {% nitro_disabled 'isLoading' %}
>
    Checkout
</button>
```

#### `nitro_file` - Streamlined File Uploads

Simplified file upload handling:

```html
{% load nitro_tags %}

<!-- Basic file upload -->
{% nitro_file 'upload_document' %}
    <span>Upload Document</span>
{% end_nitro_file %}

<!-- With file type restrictions -->
{% nitro_file 'upload_image' accept='image/*' %}
    <span>Choose Image</span>
{% end_nitro_file %}

<!-- With additional parameters -->
{% nitro_file 'upload_attachment' id=document.id accept='.pdf,.docx' %}
    <span>Attach File</span>
{% end_nitro_file %}

<!-- Styled file upload button -->
{% nitro_file 'upload_avatar' class='btn btn-primary' %}
    <i class="icon-upload"></i> Upload Avatar
{% end_nitro_file %}
```

The `nitro_file` tag automatically handles:
- File input creation and styling
- FormData construction
- CSRF token inclusion
- Action invocation with file parameter

---

## Form Field Template Tags (v0.6.0)

Django Nitro includes pre-built template tags for common form fields with built-in validation, error handling, and Alpine.js integration.

### `{% nitro_input %}`

Renders an input field with automatic error display and optional chaining support.

**Basic Usage:**

```django
<!-- Text input -->
{% nitro_input 'name' %}

<!-- Email input -->
{% nitro_input 'email' type='email' %}

<!-- Number input -->
{% nitro_input 'price' type='number' %}

<!-- Date input -->
{% nitro_input 'birth_date' type='date' %}

<!-- With placeholder -->
{% nitro_input 'phone' type='tel' placeholder='555-1234' %}

<!-- With custom CSS classes -->
{% nitro_input 'username' class='form-control-lg' %}

<!-- Disabled input -->
{% nitro_input 'id' disabled=True %}

<!-- With custom attributes -->
{% nitro_input 'age' type='number' min='18' max='100' %}
```

**Edit Buffer Support:**

```django
<!-- Automatically uses edit_buffer when present in field name -->
{% nitro_input 'edit_buffer.name' %}

<!-- Works with nested fields -->
{% nitro_input 'edit_buffer.address.street' %}
```

**Generated HTML:**

```html
<div class="mb-3">
  <input
    type="text"
    x-model="name"
    class="form-control"
    :class="{'is-invalid': errors?.name}"
  >
  <div x-show="errors?.name" class="invalid-feedback" x-text="errors?.name"></div>
</div>
```

### `{% nitro_select %}`

Renders a select dropdown with choices and error handling.

**Basic Usage:**

```django
<!-- Simple select with choices list -->
{% nitro_select 'status' choices=status_choices %}

<!-- With custom CSS classes -->
{% nitro_select 'category' choices=categories class='form-select-lg' %}

<!-- Disabled select -->
{% nitro_select 'country' choices=countries disabled=True %}

<!-- Edit buffer support -->
{% nitro_select 'edit_buffer.priority' choices=priority_choices %}
```

**Choices Format:**

```python
# In your component
class MyComponent(NitroComponent[MyState]):
    def get_initial_state(self):
        return MyState(
            status_choices=[
                {'value': 'active', 'label': 'Active'},
                {'value': 'inactive', 'label': 'Inactive'},
                {'value': 'pending', 'label': 'Pending'},
            ]
        )
```

**Generated HTML:**

```html
<div class="mb-3">
  <select x-model="status" class="form-select" :class="{'is-invalid': errors?.status}">
    <option value="">---------</option>
    <option value="active">Active</option>
    <option value="inactive">Inactive</option>
    <option value="pending">Pending</option>
  </select>
  <div x-show="errors?.status" class="invalid-feedback" x-text="errors?.status"></div>
</div>
```

### `{% nitro_checkbox %}`

Renders a checkbox input with label and error handling.

**Basic Usage:**

```django
<!-- Simple checkbox -->
{% nitro_checkbox 'is_active' label='Active' %}

<!-- Terms and conditions -->
{% nitro_checkbox 'terms_accepted' label='I agree to the terms and conditions' %}

<!-- With custom CSS classes -->
{% nitro_checkbox 'newsletter' label='Subscribe to newsletter' class='form-check-lg' %}

<!-- Disabled checkbox -->
{% nitro_checkbox 'verified' label='Verified' disabled=True %}

<!-- Edit buffer support -->
{% nitro_checkbox 'edit_buffer.is_featured' label='Featured' %}
```

**Generated HTML:**

```html
<div class="form-check mb-3">
  <input
    type="checkbox"
    x-model="is_active"
    class="form-check-input"
    :class="{'is-invalid': errors?.is_active}"
    id="id_is_active"
  >
  <label class="form-check-label" for="id_is_active">
    Active
  </label>
  <div x-show="errors?.is_active" class="invalid-feedback" x-text="errors?.is_active"></div>
</div>
```

### `{% nitro_textarea %}`

Renders a textarea field with error handling.

**Basic Usage:**

```django
<!-- Simple textarea -->
{% nitro_textarea 'description' %}

<!-- With rows -->
{% nitro_textarea 'notes' rows='5' %}

<!-- With placeholder -->
{% nitro_textarea 'comments' placeholder='Enter your comments...' %}

<!-- With custom CSS classes -->
{% nitro_textarea 'bio' class='form-control-lg' rows='10' %}

<!-- Disabled textarea -->
{% nitro_textarea 'system_log' disabled=True %}

<!-- Edit buffer support -->
{% nitro_textarea 'edit_buffer.description' rows='8' %}
```

**Generated HTML:**

```html
<div class="mb-3">
  <textarea
    x-model="description"
    class="form-control"
    :class="{'is-invalid': errors?.description}"
    rows="3"
  ></textarea>
  <div x-show="errors?.description" class="invalid-feedback" x-text="errors?.description"></div>
</div>
```

### Complete Form Example

```django
<div x-data="nitroComponent('{{ component_id }}', {{ state|json_script:component_id|safe }})">
  <form @submit.prevent="call('save_item')">
    {% nitro_input 'name' placeholder='Full Name' %}
    {% nitro_input 'email' type='email' placeholder='email@example.com' %}
    {% nitro_select 'status' choices=status_choices %}
    {% nitro_textarea 'bio' rows='5' placeholder='Tell us about yourself...' %}
    {% nitro_checkbox 'newsletter' label='Subscribe to newsletter' %}

    <button type="submit" class="btn btn-primary" :disabled="isLoading">
      <span x-show="!isLoading">Save</span>
      <span x-show="isLoading">Saving...</span>
    </button>
  </form>
</div>
```

### Error Handling

All form field tags automatically display validation errors from your Pydantic models:

```python
class UserSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    age: int = Field(ge=18, le=120)

class UserForm(NitroComponent[UserSchema]):
    def save_user(self):
        try:
            # Pydantic validation runs automatically
            user = User.objects.create(**self.state.dict())
            self.success("User created!")
        except ValidationError as e:
            # Errors automatically displayed under each field
            pass
```

The error messages will appear automatically under the corresponding field with Bootstrap's `.invalid-feedback` styling.

---

## Security & Integrity

Django Nitro provides multiple layers of security to protect your application.

### 1. CSRF Protection

All Nitro requests automatically include Django's CSRF token. The JavaScript layer:
- Reads the CSRF token from cookies
- Includes it in every request header (`X-CSRFToken`)
- Works with both JSON and FormData requests

**No configuration needed** - it just works with Django's standard CSRF middleware.

### 2. Integrity Verification

Nitro automatically protects sensitive fields from client-side tampering using HMAC-based signatures.

**ModelNitroComponent** automatically secures:
- `id` field
- Any field ending with `_id` (foreign keys)

```python
class BlogPostEditor(ModelNitroComponent[BlogPostSchema]):
    model = BlogPost
    # Automatically secured: id, author_id
```

**Custom Secure Fields:**

```python
class PricingComponent(NitroComponent[PricingState]):
    secure_fields = ['price', 'discount', 'currency']
    # These fields cannot be modified client-side
```

**How It Works:**

1. On render, an **integrity token** is computed using Django's `Signer` (HMAC signature)
2. Token is sent with every action
3. Server verifies the token matches the current secure field values
4. If verification fails → 403 Forbidden with error message

**Client sees:**
```json
{
  "state": {"id": 123, "price": 99.99},
  "integrity": "abc123def456..."
}
```

If the user modifies `price` in browser DevTools and tries to send it back, the integrity check fails and the user sees:
> ⚠️ Security: Data has been tampered with.

### 3. Developer Responsibilities

While Nitro provides security foundations, **you are responsible for**:

#### ✅ Authentication & Authorization

```python
from django.core.exceptions import PermissionDenied

class DocumentEditor(ModelNitroComponent[DocumentSchema]):
    def delete_document(self):
        # CHECK: Is user authenticated?
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication required")

        # CHECK: Does user own this document?
        doc = self.get_object(self.state.id)
        if doc.owner != self.request.user:
            raise PermissionDenied("You don't own this document")

        # CHECK: Does user have permission?
        if not self.request.user.has_perm('documents.delete_document'):
            raise PermissionDenied("Missing delete permission")

        doc.delete()
```

#### ✅ Input Validation

```python
class UserProfileEditor(NitroComponent[ProfileState]):
    def update_profile(self):
        # Validate on server-side (never trust client data)
        if len(self.state.bio) > 500:
            self.error("Bio too long (max 500 characters)")
            return

        if not self.state.email or '@' not in self.state.email:
            self.error("Invalid email address")
            return

        # Additional validation
        if contains_profanity(self.state.bio):
            self.error("Bio contains inappropriate content")
            return

        # Save after validation
        profile = self.request.user.profile
        profile.bio = self.state.bio
        profile.save()
```

#### ✅ Rate Limiting

```python
from django.core.cache import cache
from django.core.exceptions import PermissionDenied

class SearchComponent(NitroComponent[SearchState]):
    def search(self):
        # Simple rate limiting example
        user_id = self.request.user.id or self.request.META.get('REMOTE_ADDR')
        cache_key = f"search_rate_{user_id}"

        request_count = cache.get(cache_key, 0)
        if request_count > 10:  # 10 searches per minute
            raise PermissionDenied("Too many searches. Please wait.")

        cache.set(cache_key, request_count + 1, 60)  # 60 seconds

        # Perform search...
```

#### ✅ File Upload Security

```python
class DocumentUploader(CrudNitroComponent[DocumentState]):
    def upload_file(self, uploaded_file=None):
        if not uploaded_file:
            self.error("No file provided")
            return

        # VALIDATE: File extension
        allowed = ['.pdf', '.docx', '.txt']
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in allowed:
            self.error(f"Invalid file type: {ext}")
            return

        # VALIDATE: File size
        max_size = 5 * 1024 * 1024  # 5MB
        if uploaded_file.size > max_size:
            self.error("File too large (max 5MB)")
            return

        # VALIDATE: Content type (not just extension)
        import magic  # python-magic library
        file_type = magic.from_buffer(uploaded_file.read(1024), mime=True)
        uploaded_file.seek(0)  # Reset file pointer

        allowed_types = ['application/pdf', 'text/plain']
        if file_type not in allowed_types:
            self.error(f"Invalid file content type: {file_type}")
            return

        # SANITIZE: Generate safe filename
        import uuid
        safe_filename = f"{uuid.uuid4()}{ext}"

        # Save with sanitized name
        doc = Document.objects.create(
            file=uploaded_file,
            original_name=uploaded_file.name[:100],  # Limit length
            owner=self.request.user
        )
```

#### ✅ SQL Injection Prevention

Use Django ORM (never raw SQL with user input):

```python
# ✅ SAFE - Django ORM parameterizes queries
def search(self):
    query = self.state.search_query
    results = Product.objects.filter(name__icontains=query)

# ❌ DANGEROUS - Never do this!
def search_raw(self):
    query = self.state.search_query
    cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{query}%'")
```

#### ✅ XSS Prevention

Django templates auto-escape by default, but be careful with:

```python
# ✅ SAFE - Django auto-escapes in templates
# <div x-text="user_input"></div>

# ⚠️ BE CAREFUL with x-html
# <div x-html="user_input"></div>  # Can inject HTML/JS

# If you must use x-html, sanitize first:
import bleach

def save_content(self):
    # Only allow safe HTML tags
    self.state.content = bleach.clean(
        self.state.content,
        tags=['p', 'b', 'i', 'u', 'a'],
        attributes={'a': ['href']}
    )
```

### Security Checklist

Before deploying your Nitro components:

- [ ] All actions check `request.user.is_authenticated` if needed
- [ ] Permission checks use `has_perm()` or custom authorization logic
- [ ] File uploads validate type, size, and content
- [ ] User input is validated server-side (never trust client)
- [ ] Sensitive operations are rate-limited
- [ ] Database queries use ORM (no raw SQL with user input)
- [ ] `secure_fields` includes all IDs and sensitive data
- [ ] Error messages don't leak sensitive information
- [ ] `DEBUG = False` in production
- [ ] `ALLOWED_HOSTS` is properly configured

---

## Messages & Notifications

### Adding Messages

Django Nitro provides four message levels for user feedback:

```python
class MyComponent(NitroComponent[MyState]):
    def save(self):
        try:
            # ... save logic ...
            self.success("Item saved successfully!")  # Green toast
        except ValidationError as e:
            self.error(f"Validation failed: {str(e)}")  # Red toast
            logger.exception("Save failed")

    def export_data(self):
        self.info("Export started. You'll receive an email when complete.")  # Blue toast

    def check_quota(self):
        if self.get_usage() > 80:
            self.warning("You've used 80% of your quota!")  # Yellow/orange toast
```

**Available methods:**
- `self.success(message)` - Green toast for successful operations
- `self.error(message)` - Red toast for errors and failures
- `self.info(message)` - Blue toast for informational messages
- `self.warning(message)` - Yellow/orange toast for warnings

### Toast Notifications (v0.4.0+)

Django Nitro includes a professional toast notification system that works out of the box, with support for custom toast libraries.

#### Native Toasts (No Dependencies)

By default, Nitro shows beautiful native toasts without any external dependencies:

```python
# settings.py (optional - these are the defaults)
NITRO = {
    'TOAST_ENABLED': True,
    'TOAST_POSITION': 'top-right',  # top-right, top-left, top-center, bottom-right, bottom-left, bottom-center
    'TOAST_DURATION': 3000,  # milliseconds (3 seconds)
    'TOAST_STYLE': 'default',  # default, minimal, bordered
}
```

**Features:**
- 6 positions (top-right, top-left, top-center, bottom-right, bottom-left, bottom-center)
- 3 styles (default, minimal, bordered)
- 4 levels (success, error, warning, info)
- Auto-dismiss with configurable duration
- Manual close button
- Smooth animations
- Responsive design

#### Per-Component Configuration

Override global settings for specific components:

```python
@register_component
class CriticalAlert(NitroComponent[AlertState]):
    # Override toast settings for this component
    toast_enabled = True
    toast_position = 'top-center'
    toast_duration = 5000  # Show for 5 seconds
    toast_style = 'bordered'

    def alert_user(self):
        self.error("Critical: Server backup failed!")  # Uses component-specific config
```

#### Custom Toast Libraries

Integrate your favorite toast library (SweetAlert2, Toastify, Notyf, etc.) by defining a custom adapter:

```html
<!-- In your base template, before nitro.js -->
<script>
// Example: SweetAlert2
window.NitroToastAdapter = {
    show: function(message, level, config) {
        Swal.fire({
            icon: level,
            title: message,
            toast: true,
            position: config.position || 'top-end',
            timer: config.duration || 3000,
            showConfirmButton: false
        });
    }
};
</script>

<!-- Or use Toastify -->
<script>
window.NitroToastAdapter = {
    show: function(message, level, config) {
        Toastify({
            text: message,
            className: level,
            duration: config.duration || 3000,
            gravity: config.position.includes('top') ? 'top' : 'bottom',
            position: config.position.includes('right') ? 'right' : 'left'
        }).showToast();
    }
};
</script>
```

**See also:** [Toast Adapters Guide](docs/core-concepts/TOAST_ADAPTERS.md) for complete examples.

#### Disabling Toasts

Disable toasts globally or per-component:

```python
# settings.py - Disable all toasts
NITRO = {
    'TOAST_ENABLED': False,
}

# Or per-component
@register_component
class SilentComponent(NitroComponent[State]):
    toast_enabled = False  # No toasts for this component
```

### Displaying Messages in Templates

If you prefer manual message handling over toasts:

```html
<!-- Basic -->
<template x-for="msg in messages" :key="msg.text">
    <div x-text="msg.text"></div>
</template>

<!-- With styling based on level -->
<template x-for="msg in messages">
    <div
        :class="{
            'alert-success': msg.level === 'success',
            'alert-error': msg.level === 'error',
            'alert-warning': msg.level === 'warning',
            'alert-info': msg.level === 'info'
        }"
        x-text="msg.text"
    ></div>
</template>

<!-- Auto-dismiss with timeout -->
<template x-for="(msg, index) in messages" :key="index">
    <div
        x-data="{show: true}"
        x-init="setTimeout(() => show = false, 3000)"
        x-show="show"
        x-transition
        x-text="msg.text"
    ></div>
</template>
```

---

## Events & Inter-Component Communication (v0.4.0+)

Django Nitro provides a powerful event system for communication between components and custom integrations.

### Emitting Custom Events

Use `emit()` to send custom events from your component:

```python
@register_component
class ShoppingCart(NitroComponent[CartState]):
    def add_to_cart(self, product_id: int):
        # Add product to cart
        self.state.items.append(product_id)

        # Emit custom event that other components can listen to
        self.emit('cart-updated', {
            'item_count': len(self.state.items),
            'product_id': product_id
        })

        self.success("Item added to cart")
```

**Event name conventions:**
- Events are automatically prefixed with `nitro:` if not already
- `emit('cart-updated')` → dispatches `nitro:cart-updated`
- `emit('nitro:custom')` → dispatches `nitro:custom` (no double prefix)

### Refreshing Other Components

Trigger a refresh in another component using the `refresh_component()` helper:

```python
@register_component
class ProductEditor(ModelNitroComponent[ProductSchema]):
    def save_product(self):
        obj = self.get_object(self.state.id)
        obj.name = self.state.name
        obj.price = self.state.price
        obj.save()

        # Tell the ProductList component to refresh
        self.refresh_component('ProductList')

        self.success("Product saved!")
```

This emits a `nitro:refresh-productlist` event that your components can listen to.

### Listening to Events (JavaScript)

Listen to Nitro events in your templates or custom JavaScript:

```html
<script>
// Listen for cart updates
window.addEventListener('nitro:cart-updated', (event) => {
    console.log('Cart updated:', event.detail);
    // event.detail contains: { component: 'ShoppingCart', item_count: 3, product_id: 42 }

    // Update badge count
    document.getElementById('cart-badge').textContent = event.detail.item_count;
});

// Listen for component refresh requests
window.addEventListener('nitro:refresh-productlist', (event) => {
    console.log('ProductList should refresh');
    // Trigger a refresh on your component if needed
});
</script>
```

### Built-in DOM Events

Nitro automatically dispatches these events:

**`nitro:message`** - Each message/toast notification
```javascript
window.addEventListener('nitro:message', (event) => {
    // event.detail: { component: 'MyComponent', level: 'success', text: 'Saved!' }
});
```

**`nitro:action-complete`** - Action succeeded
```javascript
window.addEventListener('nitro:action-complete', (event) => {
    // event.detail: { component: 'MyComponent', action: 'save', state: {...} }
    console.log('Action completed:', event.detail.action);
});
```

**`nitro:error`** - Error occurred
```javascript
window.addEventListener('nitro:error', (event) => {
    // event.detail: { component: 'MyComponent', action: 'save', error: '...', status: 500 }
    console.error('Nitro error:', event.detail.error);
});
```

### Example: Multi-Component Workflow

```python
# Product editor component
@register_component
class ProductEditor(ModelNitroComponent[ProductSchema]):
    def delete_product(self):
        obj = self.get_object(self.state.id)
        product_name = obj.name
        obj.delete()

        # Notify analytics component
        self.emit('product-deleted', {'product_name': product_name})

        # Refresh the product list
        self.refresh_component('ProductList')

        self.success(f"Deleted {product_name}")

# Analytics component
@register_component
class Analytics(NitroComponent[AnalyticsState]):
    def track_deletion(self, product_name: str):
        # Called via JavaScript event listener
        self.state.deleted_count += 1
        # Send to analytics service...
```

```html
<!-- In your template -->
<script>
window.addEventListener('nitro:product-deleted', (event) => {
    // Track the deletion
    fetch('/api/analytics/track', {
        method: 'POST',
        body: JSON.stringify({
            event: 'product_deleted',
            product: event.detail.product_name
        })
    });
});
</script>
```

---

## CLI Tools (v0.4.0+)

### Component Scaffolding

Quickly generate new Nitro components with the `startnitro` management command:

```bash
# Basic component
python manage.py startnitro ComponentName --app myapp

# List component with pagination and search
python manage.py startnitro ProductList --app products --list

# Full CRUD component
python manage.py startnitro TaskManager --app tasks --crud
```

**Arguments:**
- `ComponentName` - Name of the component (must start with uppercase)
- `--app` - Django app where the component will be created (required)
- `--list` - Generate a list component with pagination and search
- `--crud` - Generate a CRUD component with create/edit/delete (implies `--list`)

### What Gets Generated

The command creates:

1. **Component file**: `{app}/components/{component_name}.py`
   - State schema (Pydantic model)
   - Component class with actions
   - Imports and boilerplate

2. **Template file**: `{app}/templates/components/{component_name}.html`
   - AlpineJS bindings
   - Form inputs
   - Action buttons

3. **Package file**: `{app}/components/__init__.py` (if missing)

### Example: Generated CRUD Component

```bash
python manage.py startnitro CompanyList --app companies --crud
```

Creates `companies/components/company_list.py`:

```python
from pydantic import BaseModel, ConfigDict, Field
from nitro import BaseListComponent, BaseListState, register_component

class CompanySchema(BaseModel):
    """Schema for Company item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = ""
    # TODO: Add more fields

class CompanyFormSchema(BaseModel):
    """Form schema for creating/editing Company."""
    name: str = ""
    # TODO: Add more fields

class CompanyListState(BaseListState):
    """State schema for CompanyList component."""
    items: list[CompanySchema] = []
    create_buffer: CompanyFormSchema = Field(default_factory=CompanyFormSchema)
    edit_buffer: CompanyFormSchema | None = None

@register_component
class CompanyList(BaseListComponent[CompanyListState]):
    """
    CompanyList component with pagination, search, and CRUD.

    Usage:
        {% nitro_component 'CompanyList' %}
    """
    template_name = "components/company_list.html"
    state_class = CompanyListState
    # model = Company  # TODO: Uncomment and import model

    search_fields = ['name']  # TODO: Adjust search fields
    per_page = 20
    order_by = '-id'

    # Pre-built methods: create_item(), delete_item(), search_items(), etc.
```

And `companies/templates/components/company_list.html` with a complete UI including search, pagination, and CRUD forms.

**Next steps:**
1. Uncomment and import your Django model
2. Add fields to the schemas
3. Customize search fields and actions
4. Use in templates: `{% nitro_component 'CompanyList' %}`

---

## SEO-Friendly Template Tags (v0.4.0+)

For public-facing content that needs SEO (search engine optimization), Nitro provides special template tags that render static HTML for crawlers while maintaining Alpine.js reactivity.

### `{% nitro_scripts %}` - Include Nitro Assets

Load Nitro's CSS and JavaScript files (includes toast styles):

```html
{% load nitro_tags %}
<!DOCTYPE html>
<html>
<head>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <!-- Loads nitro.css and nitro.js -->
    {% nitro_scripts %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

Expands to:
```html
<link rel="stylesheet" href="/static/nitro/nitro.css">
<script defer src="/static/nitro/nitro.js"></script>
```

### `{% nitro_text %}` - SEO-Friendly Text Binding

Renders server-side text that's also reactive with Alpine.js:

```html
{% load nitro_tags %}

<!-- Traditional Alpine (not SEO-friendly) -->
<h1 x-text="product.name"></h1>
<!-- Crawlers see: <h1 x-text="product.name"></h1> (no text content) -->

<!-- SEO-friendly Nitro tag -->
<h1>{% nitro_text 'product.name' %}</h1>
<!-- Crawlers see: <h1><span x-text="product.name">Gaming Laptop</span></h1> -->
<!-- Users see: Same thing, but reactive! -->
```

**How it works:**
1. Server renders the actual value ("Gaming Laptop")
2. Adds `x-text` binding for reactivity
3. When state changes, Alpine updates the content
4. Search engines see the static HTML

**Usage:**
```html
<div class="product-card">
    <h2>{% nitro_text 'item.name' %}</h2>
    <p class="price">${% nitro_text 'item.price' %}</p>
    <p class="description">{% nitro_text 'item.description' %}</p>
</div>
```

### `{% nitro_for %}` - SEO-Friendly Loops

Renders list items on the server for SEO, while keeping Alpine.js reactivity:

```html
{% load nitro_tags %}

<!-- Traditional Alpine (not SEO-friendly) -->
<template x-for="product in products" :key="product.id">
    <div class="card">
        <h3 x-text="product.name"></h3>
    </div>
</template>
<!-- Crawlers see: Nothing (template tag is not rendered) -->

<!-- SEO-friendly Nitro tag -->
{% nitro_for 'products' as 'product' %}
    <div class="card">
        <h3>{% nitro_text 'product.name' %}</h3>
        <p>{% nitro_text 'product.description' %}</p>
    </div>
{% end_nitro_for %}
<!-- Crawlers see: All cards with actual content -->
<!-- Users see: Same thing, but reactive when products change! -->
```

**How it works:**
1. Server renders all items (e.g., 50 products)
2. Wraps them in a hidden div (`x-show="false"`)
3. Adds an Alpine `<template x-for>` for reactivity
4. Search engines index the static content
5. Alpine shows/updates the reactive template

**Complete example:**

```html
{% load nitro_tags %}

<div class="property-list">
    <h1>Available Properties</h1>

    <!-- SEO-friendly list -->
    {% nitro_for 'properties' as 'property' %}
        <div class="property-card">
            <h2>{% nitro_text 'property.title' %}</h2>
            <p class="address">{% nitro_text 'property.address' %}</p>
            <p class="price">${% nitro_text 'property.price' %}</p>

            <button @click="call('view_details', {id: property.id})">
                View Details
            </button>
        </div>
    {% end_nitro_for %}
</div>
```

**When to use SEO tags:**
- ✅ Public product listings
- ✅ Blog posts
- ✅ Property/real estate listings
- ✅ Any content you want indexed by Google
- ❌ Private dashboards (not crawled anyway)
- ❌ Admin panels
- ❌ Authenticated-only content

---

## Performance Optimization (v0.4.0+)

### Smart State Updates (Diffing)

For components with large lists (500+ items), enable smart updates to only send changes instead of the full list:

```python
from pydantic import BaseModel
from nitro import BaseListComponent, register_component

class TaskSchema(BaseModel):
    id: int  # Required for diffing
    title: str
    completed: bool

@register_component
class TaskList(BaseListComponent[TaskListState]):
    # Enable smart updates
    smart_updates = True

    def toggle_task(self, id: int):
        # Only the changed task is sent to the client
        task = Task.objects.get(id=id)
        task.completed = not task.completed
        task.save()

        # Refresh state
        self.refresh()
        # Client receives: {added: [], removed: [], updated: [{id: 42, completed: true}]}
        # Instead of: {items: [500 tasks...]}
```

**How it works:**
1. Nitro compares old state vs new state
2. For lists with items that have an `id` field, it calculates:
   - `added` - New items
   - `removed` - Deleted items (by id)
   - `updated` - Modified items
3. Client applies changes in-place (no full re-render)

**Requirements:**
- Items must have an `id` field
- Set `smart_updates = True` on component
- List must be in state (e.g., `items: list[TaskSchema]`)

**Example response:**
```json
{
  "partial": true,
  "state": {
    "items": {
      "diff": {
        "added": [{"id": 101, "title": "New task", "completed": false}],
        "removed": [99],
        "updated": [{"id": 42, "title": "Updated title", "completed": true}]
      }
    }
  }
}
```

**Performance benefits:**
- 500 items → ~50KB full state vs ~1KB diff
- Faster network transfer
- Faster client-side processing
- Better UX for real-time updates

**When to use:**
- ✅ Lists with 100+ items
- ✅ Real-time collaborative editing
- ✅ Live dashboards with frequent updates
- ❌ Small lists (< 50 items) - overhead not worth it
- ❌ Components without list state

---

## File Uploads

Django Nitro supports file uploads using Django Ninja's built-in multipart/form-data handling.

### Backend: Add File Upload Action

```python
from django.core.files.uploadedfile import UploadedFile

@register_component
class DocumentManager(CrudNitroComponent[DocumentState]):
    template_name = "components/document_manager.html"
    state_class = DocumentState
    model = Document

    def upload_file(self, document_id: int, uploaded_file=None):
        """
        Handle file upload.

        Note: The uploaded_file parameter name must match exactly.
        Nitro automatically detects it and passes the file from the request.
        """
        # Validate file was provided
        if not uploaded_file:
            self.error("No file selected")
            return

        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        if file_ext not in allowed_extensions:
            self.error(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
            return

        # Validate file size (5MB max)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if uploaded_file.size > max_size:
            self.error("File too large (max 5MB)")
            return

        # Save to database
        try:
            doc = self.model.objects.get(id=document_id)
            doc.file = uploaded_file
            doc.save()

            self.refresh()
            self.success(f"File '{uploaded_file.name}' uploaded successfully!")
        except Exception as e:
            logger.exception("File upload failed")
            self.error(f"Upload failed: {str(e)}")
```

### Frontend: File Input

```html
<!-- templates/components/document_manager.html -->
<template x-for="doc in documents" :key="doc.id">
    <div class="document-item">
        <span x-text="doc.name"></span>

        <!-- Show current file if exists -->
        <template x-if="doc.file_url">
            <a :href="doc.file_url" target="_blank">View File</a>
        </template>

        <!-- File upload input -->
        <label class="file-upload">
            <input
                type="file"
                accept=".pdf,.docx,.txt"
                class="hidden"
                @change="(e) => {
                    const file = e.target.files[0];
                    if (file) {
                        // Third parameter is the file
                        call('upload_file', {document_id: doc.id}, file);
                        e.target.value = '';  // Reset input
                    }
                }"
            >
            <span>Upload File</span>
        </label>
    </div>
</template>
```

### Important Notes

1. **Parameter Name**: The action method must have a parameter named exactly `uploaded_file` - Nitro automatically detects this and passes the file
2. **File Validation**: Always validate file type and size server-side
3. **CSRF Protection**: File uploads automatically include CSRF tokens
4. **Media Settings**: Configure Django's `MEDIA_URL` and `MEDIA_ROOT` in settings.py
5. **FormData**: Nitro automatically uses FormData when a file is provided, no configuration needed

### Django Settings for File Uploads

```python
# settings.py

# Media files (user uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

```python
# urls.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your URLs
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Debugging

### Enable Debug Mode (v0.5.0)

To see detailed console logs for development:

```html
<!-- Add to your base template before nitro.js -->
<script>
    window.NITRO_DEBUG = true;
</script>
<script src="{% static 'nitro/nitro.js' %}"></script>
```

Or configure in Django settings:

```python
# settings.py
NITRO = {
    'DEBUG': True,  # Enables client-side debug logging
}
```

When enabled, you'll see:
- Component initialization logs
- Action calls with state and payload
- Server responses
- Message notifications
- State diff information (when smart_updates is enabled)

**Important**: Set to `False` in production to avoid console spam.

### Django Debug Toolbar Panel (v0.5.0)

Django Nitro includes a custom panel for Django Debug Toolbar that shows:
- Registered components and their state
- Action invocations during the request
- State changes and integrity verification
- Performance metrics

**Setup:**

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
    'nitro',  # Must be after debug_toolbar
]

DEBUG_TOOLBAR_PANELS = [
    # ... default panels ...
    'nitro.panels.NitroDebugPanel',
]
```

The panel displays:
- **Components**: All registered Nitro components
- **Actions**: Actions called during the request with parameters
- **State**: Initial and final state for each component
- **Timing**: Time spent in each action

---

## Advanced Usage

### Nested Components

You can render Nitro components inside other Nitro components:

```python
# Parent component
@register_component
class PropertyDetail(ModelNitroComponent[PropertySchema]):
    template_name = "components/property_detail.html"
    # ...

# Child component
@register_component
class TenantList(CrudNitroComponent[TenantListState]):
    template_name = "components/tenant_list.html"
    # ...
```

```html
<!-- templates/components/property_detail.html -->
<div class="property-detail">
    <h1 x-text="name"></h1>
    <p x-text="address"></p>

    <!-- Render child component -->
    {% load nitro %}
    {{ tenant_list.render }}
</div>
```

```python
def property_detail(request, pk):
    property_comp = PropertyDetail(request=request, pk=pk)
    tenant_list = TenantList(request=request, property_id=pk)
    return render(request, 'property_detail.html', {
        'property': property_comp,
        'tenant_list': tenant_list
    })
```

### Optimistic Updates

For better UX, update the UI immediately without waiting for server response:

```python
class TaskList(CrudNitroComponent[TaskListState]):
    def toggle_completed(self, id: int):
        # Update state immediately (optimistic)
        for task in self.state.tasks:
            if task.id == id:
                task.completed = not task.completed
                break

        # Then update database
        try:
            task_obj = Task.objects.get(id=id)
            task_obj.completed = not task_obj.completed
            task_obj.save()
        except Exception as e:
            # If it fails, refresh to revert
            self.refresh()
            self.error("Failed to update task")
```

### Custom Refresh Logic

Override `refresh()` for custom reload behavior:

```python
class ProductList(CrudNitroComponent[ProductListState]):
    def refresh(self):
        """Custom refresh that preserves filters."""
        # Keep current search query
        query = self.state.search_query

        # Reload products
        qs = Product.objects.filter(name__icontains=query)
        self.state.products = [
            ProductSchema.model_validate(p) for p in qs
        ]

        # Don't clear buffers (unlike default refresh)
        # Users can keep typing while data refreshes
```

### Permission Checks

Use Django's permission system in your actions:

```python
from django.core.exceptions import PermissionDenied

class DocumentEditor(ModelNitroComponent[DocumentSchema]):
    def delete_document(self):
        if not self.request.user.has_perm('documents.delete_document'):
            raise PermissionDenied("You don't have permission to delete")

        obj = self.get_object(self.state.id)
        obj.delete()
        self.success("Document deleted")
```

---

## Best Practices

### 1. Keep Actions Small and Focused

```python
# ✅ Good
def increment(self):
    self.state.count += 1

def save_and_notify(self):
    self.save()
    send_notification(self.request.user)

# ❌ Avoid
def do_everything(self):
    self.state.count += 1
    self.save()
    send_email()
    log_analytics()
    # too much responsibility
```

### 2. Use Proper Validation

```python
from pydantic import BaseModel, validator, EmailStr

class FormState(BaseModel):
    email: EmailStr  # Built-in email validation
    age: int

    @validator('age')
    def age_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Age cannot be negative')
        return v
```

### 3. Handle Errors Gracefully

```python
def save(self):
    try:
        # ... save logic ...
        self.success("Saved!")
    except ValidationError as e:
        self.error("Please check your input")
    except Exception as e:
        logger.exception("Unexpected error")
        self.error("Something went wrong. Please try again.")
```

### 4. Optimize Database Queries

```python
def get_initial_state(self, **kwargs):
    # ✅ Good - use select_related/prefetch_related
    properties = Property.objects.select_related('owner').prefetch_related('tenants')

    # ❌ Avoid - N+1 queries
    properties = Property.objects.all()
    for prop in properties:
        _ = prop.owner  # separate query each time
```

### 5. Use Debouncing for Search

```html
<!-- Debounce search to avoid too many requests -->
<input
    x-model="search_query"
    @input.debounce.300ms="call('search')"
    placeholder="Search..."
>
```

### 6. Provide Loading States

```html
<!-- Show loading indicator -->
<div x-show="isLoading" class="spinner">Loading...</div>

<!-- Disable buttons during loading -->
<button @click="call('save')" :disabled="isLoading">
    Save
</button>
```

---

## Comparison to Alternatives

### vs Django Unicorn

| Feature | Django Nitro | Django Unicorn |
|---------|-------------|----------------|
| **Frontend Library** | AlpineJS (~15KB) | Morphdom (~50KB) |
| **State Validation** | Pydantic (strict typing) | Django Forms/Models |
| **Type Safety** | Full (Generic types) | Partial |
| **API Layer** | Django Ninja (fast) | Custom |
| **Learning Curve** | Low (if you know Alpine) | Medium |
| **Syntax** | `@click="call('action')"` | `unicorn:click="action"` |

### vs HTMX

| Feature | Django Nitro | HTMX |
|---------|-------------|------|
| **State Management** | Automatic (Pydantic) | Manual (server-side) |
| **Reactivity** | Full (Alpine) | Partial (HTML swaps) |
| **Complexity** | Medium | Low |
| **Use Case** | Complex SPAs | Simple interactions |

### vs Vanilla Alpine + Django

| Feature | Django Nitro | Alpine + Django |
|---------|-------------|-----------------|
| **Backend Integration** | Built-in | Manual API calls |
| **State Sync** | Automatic | Manual |
| **Type Safety** | Yes (Pydantic) | No |
| **Security** | Built-in integrity | Manual CSRF |

---

## Example Projects

This repository includes three complete example applications in the `examples/` folder:

### 1. Counter Example (`examples/counter/`)
Simple beginner-friendly example demonstrating basic Nitro concepts:
- ✅ Component state management
- ✅ Action methods (increment, decrement, reset)
- ✅ AlpineJS template bindings
- ✅ Success messages

### 2. Contact Form (`examples/contact-form/`) ⭐ NEW in v0.6.0
Demonstrates the new **Form Field Template Tags** with a complete contact form:
- ✅ `{% nitro_input %}` for text, email, and tel inputs
- ✅ `{% nitro_select %}` for dropdown with subject choices
- ✅ `{% nitro_textarea %}` for multi-line message field
- ✅ `{% nitro_checkbox %}` for terms acceptance
- ✅ Automatic error handling and validation
- ✅ Bootstrap styling integration

### 3. Property Manager (`examples/property-manager/`)
Comprehensive real-world example with advanced features:
- ✅ Property CRUD with search and pagination
- ✅ Tenant management (nested component)
- ✅ Inline editing
- ✅ Real-time validation
- ✅ Success/error messages
- ✅ File uploads (PDF documents for tenants)

**Run an example:**

```bash
git clone https://github.com/django-nitro/django-nitro.git
cd django-nitro/examples/counter  # or contact-form or property-manager
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install -r requirements.txt
python manage.py migrate  # (not needed for contact-form)
python manage.py runserver
```

Visit **http://localhost:8000**

---

## Troubleshooting

### Component not updating?

**Check:**
1. Is `nitro.js` loaded after Alpine?
2. Are you calling `call('action_name')` correctly?
3. Check browser console for errors
4. Verify the API URL is `/api/nitro/dispatch`

### "Component not found" error?

Make sure:
1. Component is decorated with `@register_component`
2. Component file is imported somewhere (e.g., in `apps.py`)

### State not persisting?

- State is **not** persisted between page loads
- Use Django sessions or database for persistence
- Component state resets on page refresh

### Alpine errors like "Cannot read property"?

- Use `x-show="edit_buffer && edit_buffer.field"` instead of just `x-show="edit_buffer.field"`
- Alpine evaluates bindings even when elements are hidden

---

## Contributing

Contributions are welcome! Please:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Credits

- Inspired by [Django Unicorn](https://www.django-unicorn.com/) and [Laravel Livewire](https://laravel-livewire.com/)
- Built with [AlpineJS](https://alpinejs.dev/)
- API powered by [Django Ninja](https://django-ninja.rest-framework.com/)
- State validation by [Pydantic](https://docs.pydantic.dev/)

---

## Support & Community

- 📖 [Documentation](https://github.com/django-nitro/django-nitro/wiki)
- 🐛 [Report Issues](https://github.com/django-nitro/django-nitro/issues)
- 💬 [Discussions](https://github.com/django-nitro/django-nitro/discussions)
- ⭐ Star us on [GitHub](https://github.com/django-nitro/django-nitro)

---

**Built with ❤️ for the Django community**
