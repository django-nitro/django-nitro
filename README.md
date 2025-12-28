# Django Nitro 🚀

**Build reactive Django components with AlpineJS - No JavaScript required**

Django Nitro is a modern library for building reactive, stateful components in Django applications. Inspired by Django Unicorn and Laravel Livewire, but built on top of AlpineJS and Django Ninja for a lightweight, performant experience.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2+](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)

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
- [State Management](#state-management)
- [Actions & Methods](#actions--methods)
- [Template Integration](#template-integration)
- [Security & Integrity](#security--integrity)
- [Messages & Notifications](#messages--notifications)
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
    <script src="{% static 'nitro/nitro.js' %}"></script>
</body>
</html>
```

**4. Run collectstatic (if in production)**

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

```python
class MyComponent(NitroComponent[MyState]):
    def save(self):
        try:
            # ... save logic ...
            self.success("Item saved successfully!")
        except Exception as e:
            self.error(f"Failed to save: {str(e)}")
            logger.exception("Save failed")
```

### Displaying Messages

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

### Enable Debug Mode

To see detailed console logs for development:

```html
<!-- Add to your base template before nitro.js -->
<script>
    window.NITRO_DEBUG = true;
</script>
<script src="{% static 'nitro/nitro.js' %}"></script>
```

When enabled, you'll see:
- Component initialization logs
- Action calls with state and payload
- Server responses
- Message notifications

**Important**: Remove or set to `false` in production to avoid console spam.

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

## Example Project

This repository includes a complete example app in the `example/` folder:

**Features:**
- ✅ Property CRUD with search
- ✅ Tenant management (nested component)
- ✅ Inline editing
- ✅ Real-time validation
- ✅ Success/error messages
- ✅ File uploads (PDF documents for tenants)

**Run the example:**

```bash
git clone https://github.com/django-nitro/django-nitro.git
cd django-nitro
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install -e ".[dev]"
python manage.py migrate
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
