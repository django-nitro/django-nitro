# ModelNitroComponent

`ModelNitroComponent` extends `NitroComponent` with Django ORM integration. It automatically loads model instances and provides convenient methods for working with single database objects.

## When to Use

Use `ModelNitroComponent` when you need to:

- Display or edit a **single model instance**
- Load an object by primary key automatically
- Refresh component state from the database
- Work with model-backed forms

**Examples:**
- User profile editor
- Blog post detail page
- Product details with edit capability
- Document viewer/editor

## Basic Structure

```python
from pydantic import BaseModel
from nitro.base import ModelNitroComponent
from nitro.registry import register_component
from myapp.models import Product

# State schema
class ProductSchema(BaseModel):
    id: int
    name: str
    price: float
    description: str
    is_active: bool

    class Config:
        from_attributes = True  # Enable ORM loading

# Component
@register_component
class ProductEditor(ModelNitroComponent[ProductSchema]):
    template_name = "components/product_editor.html"
    state_class = ProductSchema
    model = Product  # Django model class
```

## Key Differences from NitroComponent

### 1. Automatic State Loading

`ModelNitroComponent` automatically loads the model instance if you pass `pk` or `id`:

```python
# In your view
def edit_product(request, product_id):
    editor = ProductEditor(request=request, pk=product_id)
    # State automatically loaded from Product.objects.get(pk=product_id)
    return render(request, 'edit_product.html', {'editor': editor})
```

### 2. Automatic Secure Fields

Foreign keys and the `id` field are automatically secured:

```python
class BlogPostSchema(BaseModel):
    id: int          # Automatically secured
    title: str
    author_id: int   # Automatically secured (ends with _id)
    content: str

    class Config:
        from_attributes = True

@register_component
class BlogPostEditor(ModelNitroComponent[BlogPostSchema]):
    model = BlogPost
    # No need to set secure_fields - id and author_id are auto-secured
```

### 3. Built-in Refresh

`refresh()` reloads state from the database:

```python
def toggle_active(self):
    obj = self.get_object(self.state.id)
    obj.is_active = not obj.is_active
    obj.save()

    self.refresh()  # Reload from database
    status = "activated" if self.state.is_active else "deactivated"
    self.success(f"Product {status}")
```

## Class Attributes

Inherits all attributes from `NitroComponent` plus:

### Required

```python
model: Type[Model]
```
Django model class to load instances from.

```python
# Example
class ProductEditor(ModelNitroComponent[ProductSchema]):
    model = Product
```

## Methods

### ORM Methods

#### `get_object(pk: int) -> Model`

Retrieves a model instance by primary key.

```python
def delete_product(self):
    obj = self.get_object(self.state.id)
    obj.delete()
    # Navigate away or show confirmation
```

#### `refresh() -> None`

Reloads state from the database using the current `id` field.

```python
def save_changes(self):
    obj = self.get_object(self.state.id)
    obj.title = self.state.title
    obj.content = self.state.content
    obj.save()

    self.refresh()  # Reload to get computed fields, updated_at, etc.
    self.success("Changes saved")
```

### Lifecycle Methods

#### `get_initial_state(**kwargs) -> BaseModel`

**Automatic behavior:**
- If `pk` or `id` in kwargs → loads from database
- Otherwise → returns empty state or custom logic

**Override for custom initialization:**

```python
def get_initial_state(self, **kwargs):
    if 'pk' in kwargs or 'id' in kwargs:
        # Automatic loading
        pk = kwargs.get('pk') or kwargs.get('id')
        obj = self.model.objects.select_related('category').get(pk=pk)
        return self.state_class.model_validate(obj)

    # Custom initialization for new objects
    return self.state_class(
        name="New Product",
        price=0.0,
        is_active=True
    )
```

## Complete Example

```python
from django.db import models
from pydantic import BaseModel, validator
from nitro.base import ModelNitroComponent
from nitro.registry import register_component
from typing import Optional

# Django Model
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    published = models.BooleanField(default=False)
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# Pydantic Schema
class BlogPostSchema(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    published: bool
    author_id: int
    category_id: Optional[int] = None
    created_at: str
    updated_at: str

    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title is required')
        return v.strip()

    class Config:
        from_attributes = True

# Component
@register_component
class BlogPostEditor(ModelNitroComponent[BlogPostSchema]):
    template_name = "components/blog_post_editor.html"
    state_class = BlogPostSchema
    model = BlogPost

    # No need to override get_initial_state - automatic!

    def save_changes(self):
        """Save current edits to database."""
        if not self.require_auth("Please log in to save"):
            return

        try:
            # Get object
            post = self.get_object(self.state.id)

            # Check ownership
            if post.author != self.current_user:
                self.error("You don't own this post")
                return

            # Update fields
            post.title = self.state.title
            post.content = self.state.content
            post.save()

            # Reload with updated timestamp
            self.refresh()
            self.success("Post saved successfully")

        except BlogPost.DoesNotExist:
            self.error("Post not found")
        except Exception as e:
            logger.exception("Save failed")
            self.error("Failed to save changes")

    def toggle_published(self):
        """Publish or unpublish the post."""
        if not self.require_auth():
            return

        try:
            post = self.get_object(self.state.id)

            # Check ownership
            if post.author != self.current_user:
                self.error("Permission denied")
                return

            # Toggle
            post.published = not post.published
            post.save()

            # Reload
            self.refresh()

            status = "published" if post.published else "unpublished"
            self.success(f"Post {status}")

        except BlogPost.DoesNotExist:
            self.error("Post not found")

    def delete_post(self):
        """Delete the post permanently."""
        if not self.require_auth():
            return

        try:
            post = self.get_object(self.state.id)

            # Check ownership
            if post.author != self.current_user:
                self.error("Permission denied")
                return

            # Delete
            post.delete()
            self.success("Post deleted")

            # In real app, you'd redirect here
            # return HttpResponseRedirect('/posts/')

        except BlogPost.DoesNotExist:
            self.error("Post not found")
```

**Template:**

```html
<div class="blog-post-editor">
    <div class="header">
        <h1>Edit Post</h1>
        <span class="post-id" x-text="'ID: ' + id"></span>
    </div>

    <!-- Title -->
    <div class="form-group">
        <label for="title">Title</label>
        <input
            id="title"
            x-model="title"
            type="text"
            :class="{'error': errors.title}"
        >
        <span x-show="errors.title" x-text="errors.title" class="error"></span>
    </div>

    <!-- Content -->
    <div class="form-group">
        <label for="content">Content</label>
        <textarea
            id="content"
            x-model="content"
            rows="15"
            :class="{'error': errors.content}"
        ></textarea>
        <span x-show="errors.content" x-text="errors.content" class="error"></span>
    </div>

    <!-- Actions -->
    <div class="actions">
        <button @click="call('save_changes')" :disabled="isLoading">
            <span x-show="!isLoading">Save Changes</span>
            <span x-show="isLoading">Saving...</span>
        </button>

        <button
            @click="call('toggle_published')"
            :disabled="isLoading"
            :class="{'btn-success': !published, 'btn-warning': published}"
        >
            <span x-text="published ? 'Unpublish' : 'Publish'"></span>
        </button>

        <button
            @click="confirm('Delete this post?') && call('delete_post')"
            :disabled="isLoading"
            class="btn-danger"
        >
            Delete
        </button>
    </div>

    <!-- Metadata -->
    <div class="metadata">
        <small>
            Created: <span x-text="created_at"></span> |
            Updated: <span x-text="updated_at"></span>
        </small>
    </div>

    <!-- Messages -->
    <template x-for="msg in messages" :key="msg.text">
        <div :class="'alert alert-' + msg.level" x-text="msg.text"></div>
    </template>
</div>
```

**Usage in view:**

```python
from django.shortcuts import render, get_object_or_404
from myapp.components import BlogPostEditor

def edit_post(request, post_id):
    # Automatic state loading from database
    editor = BlogPostEditor(request=request, pk=post_id)
    return render(request, 'edit_post.html', {'editor': editor})
```

## Optimizing Queries

Use `select_related` and `prefetch_related` for better performance:

```python
@register_component
class ProductEditor(ModelNitroComponent[ProductSchema]):
    model = Product

    def get_initial_state(self, **kwargs):
        pk = kwargs.get('pk') or kwargs.get('id')
        if pk:
            # Optimized query with related data
            product = self.model.objects.select_related(
                'category',
                'manufacturer'
            ).prefetch_related(
                'tags',
                'images'
            ).get(pk=pk)

            return self.state_class.model_validate(product)

        return self.state_class()
```

## Security Considerations

### 1. Check Ownership

```python
def save_changes(self):
    obj = self.get_object(self.state.id)

    # ✅ Check ownership
    if obj.owner != self.current_user:
        self.error("Permission denied")
        return

    # Proceed with save...
```

### 2. Check Permissions

```python
def delete_document(self):
    # ✅ Check permission
    if not self.request.user.has_perm('documents.delete_document'):
        self.error("Permission denied")
        return

    obj = self.get_object(self.state.id)
    obj.delete()
```

### 3. Validate All Changes

```python
def update_price(self):
    # ✅ Server-side validation
    if self.state.price < 0:
        self.error("Price cannot be negative")
        return

    obj = self.get_object(self.state.id)
    obj.price = self.state.price
    obj.save()
```

## Best Practices

### 1. Use from_attributes=True

```python
class ProductSchema(BaseModel):
    # ... fields ...

    class Config:
        from_attributes = True  # Required for model loading
```

### 2. Reload After Updates

```python
def save(self):
    obj = self.get_object(self.state.id)
    obj.name = self.state.name
    obj.save()

    self.refresh()  # ✅ Reload to get computed fields, timestamps
```

### 3. Handle DoesNotExist

```python
def delete_item(self):
    try:
        obj = self.get_object(self.state.id)
        obj.delete()
    except self.model.DoesNotExist:
        self.error("Item not found")
```

### 4. Optimize Related Queries

```python
def get_initial_state(self, **kwargs):
    pk = kwargs.get('pk')
    if pk:
        # ✅ Load related data efficiently
        obj = self.model.objects.select_related('author').get(pk=pk)
        return self.state_class.model_validate(obj)
```

## Common Patterns

### Inline Editing

```python
class ProductQuickEdit(ModelNitroComponent[ProductSchema]):
    def toggle_active(self):
        obj = self.get_object(self.state.id)
        obj.is_active = not obj.is_active
        obj.save()
        self.refresh()

    def update_price(self, new_price: float):
        if new_price < 0:
            self.error("Invalid price")
            return

        obj = self.get_object(self.state.id)
        obj.price = new_price
        obj.save()
        self.refresh()
        self.success("Price updated")
```

### Optimistic Updates

```python
def toggle_favorite(self):
    # Update UI immediately
    self.state.is_favorite = not self.state.is_favorite

    # Then sync to database
    try:
        obj = self.get_object(self.state.id)
        obj.is_favorite = self.state.is_favorite
        obj.save()
    except Exception:
        # Revert on error
        self.refresh()
        self.error("Failed to update")
```

## See Also

- [NitroComponent](nitro-component.md) - Base component class
- [CrudNitroComponent](crud-nitro-component.md) - For CRUD operations
- [State Management](../core-concepts/state-management.md) - Managing state
