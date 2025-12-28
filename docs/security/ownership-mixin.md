# OwnershipMixin

`OwnershipMixin` automatically filters querysets to show only items owned by the current user. It's perfect for user-scoped data where each user should only see their own records.

## Use Cases

- **My Documents** - Users can only see their own documents
- **My Orders** - E-commerce order history
- **My Tasks** - Personal task lists
- **User Profiles** - Profile management
- **Any user-owned resources**

## Basic Usage

```python
from nitro.security import OwnershipMixin
from nitro.list import BaseListComponent, BaseListState
from nitro.registry import register_component

@register_component
class MyDocuments(OwnershipMixin, BaseListComponent[DocumentListState]):
    model = Document
    owner_field = 'user'  # Field linking to User model (default: 'user')
    search_fields = ['title', 'description']
    per_page = 25

    # Automatically filters to current user's documents only
```

## Configuration

### `owner_field: str`

The name of the ForeignKey field linking to Django's User model.

**Default:** `'user'`

```python
class MyDocuments(OwnershipMixin, BaseListComponent):
    owner_field = 'user'        # Document.user
    # or
    owner_field = 'owner'       # Document.owner
    # or
    owner_field = 'created_by'  # Document.created_by
```

Your model must have this field:

```python
class Document(models.Model):
    title = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # owner_field
    created_at = models.DateTimeField(auto_now_add=True)
```

## Methods

### `filter_by_owner(queryset) -> QuerySet`

Filters a queryset to show only items owned by the current user.

**Returns:**
- Filtered queryset if user is authenticated
- Empty queryset if user is not authenticated

```python
def get_base_queryset(self, search='', filters=None):
    # Start with all documents
    qs = self.model.objects.all()

    # Filter to current user's documents
    qs = self.filter_by_owner(qs)

    # Apply search
    if search:
        qs = self.apply_search(qs, search)

    return qs.order_by('-created_at')
```

## How It Works

The mixin adds automatic filtering:

```python
# Without OwnershipMixin
def get_base_queryset(self, search='', filters=None):
    # Shows ALL documents (security risk!)
    return Document.objects.all()

# With OwnershipMixin
def get_base_queryset(self, search='', filters=None):
    # Automatically filtered to current user
    qs = self.filter_by_owner(Document.objects.all())
    return qs
```

Behind the scenes:

```python
def filter_by_owner(self, queryset):
    if not self.request or not self.request.user.is_authenticated:
        return queryset.none()  # Empty queryset

    # Filter: queryset.filter(user=current_user)
    return queryset.filter(**{self.owner_field: self.request.user})
```

## Complete Example

```python
from django.db import models
from pydantic import BaseModel, Field
from nitro.security import OwnershipMixin
from nitro.list import BaseListComponent, BaseListState
from nitro.registry import register_component
from typing import Optional

# Django Model
class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

# Schemas
class TaskSchema(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    priority: int

    class Config:
        from_attributes = True

class TaskFormSchema(BaseModel):
    title: str = ""
    description: str = ""
    completed: bool = False
    priority: int = 0

class TaskListState(BaseListState):
    items: list[TaskSchema] = []
    create_buffer: TaskFormSchema = Field(default_factory=TaskFormSchema)
    edit_buffer: Optional[TaskFormSchema] = None

# Component with OwnershipMixin
@register_component
class MyTasks(OwnershipMixin, BaseListComponent[TaskListState]):
    template_name = "components/my_tasks.html"
    state_class = TaskListState
    model = Task
    owner_field = 'user'  # Task.user field

    search_fields = ['title', 'description']
    per_page = 25
    order_by = '-created_at'

    # get_base_queryset automatically filters by owner
    # No need to override unless you want custom logic

    def create_item(self):
        """Override to set owner automatically."""
        if not self.require_auth():
            return

        try:
            task = self.model.objects.create(
                **self.state.create_buffer.dict(),
                user=self.current_user  # Set owner
            )
            self.refresh()
            self.success(f"Created: {task.title}")
        except Exception as e:
            logger.exception("Create failed")
            self.error("Failed to create task")

    def toggle_completed(self, id: int):
        """Custom action with ownership check."""
        try:
            # OwnershipMixin ensures we only get current user's tasks
            task = self.model.objects.get(
                id=id,
                user=self.current_user
            )
            task.completed = not task.completed
            task.save()
            self.refresh()
        except self.model.DoesNotExist:
            self.error("Task not found")
```

## Customizing Ownership Filter

Override `get_base_queryset()` for custom filtering:

```python
@register_component
class MyDocuments(OwnershipMixin, BaseListComponent[DocumentListState]):
    model = Document
    owner_field = 'created_by'

    def get_base_queryset(self, search='', filters=None):
        # Start with ownership filter
        qs = self.filter_by_owner(self.model.objects.all())

        # Add additional filters
        qs = qs.filter(is_deleted=False)  # Exclude deleted

        # Apply search
        if search:
            qs = self.apply_search(qs, search)

        # Add related data optimization
        qs = qs.select_related('category')

        return qs.order_by(self.order_by)
```

## Multiple Owner Types

If you need to support different owner types:

```python
class DocumentOwnershipMixin:
    """Custom ownership for documents with multiple owner types."""

    def filter_by_owner(self, queryset):
        if not self.is_authenticated:
            return queryset.none()

        user = self.current_user

        # Documents where user is creator OR collaborator
        return queryset.filter(
            Q(created_by=user) | Q(collaborators=user)
        ).distinct()

@register_component
class MyDocuments(DocumentOwnershipMixin, BaseListComponent):
    model = Document
    # Uses custom filter_by_owner from DocumentOwnershipMixin
```

## Combining with Other Mixins

### With TenantScopedMixin

Filter by both user AND tenant:

```python
from nitro.security import OwnershipMixin, TenantScopedMixin

@register_component
class MyCompanyTasks(
    OwnershipMixin,       # Filter by current user
    TenantScopedMixin,    # Filter by current company
    BaseListComponent[TaskListState]
):
    model = Task
    owner_field = 'user'
    tenant_field = 'company'

    def get_user_tenant(self):
        return self.current_user.profile.company

    # Both filters applied: user's tasks within their company
```

### With PermissionMixin

Add permission checks on top of ownership:

```python
from nitro.security import OwnershipMixin, PermissionMixin

@register_component
class MyDocuments(
    OwnershipMixin,
    PermissionMixin,
    BaseListComponent[DocumentListState]
):
    model = Document
    owner_field = 'user'

    def check_permission(self, action: str) -> bool:
        # Even though user owns the document...
        if action == 'delete':
            # They still need delete permission
            return self.current_user.has_perm('documents.delete_document')
        return True

    def delete_item(self, id: int):
        if not self.enforce_permission('delete'):
            return
        super().delete_item(id)
```

## Security Considerations

### 1. Always Filter in get_base_queryset

```python
# ✅ Good - ownership filter applied
def get_base_queryset(self, search='', filters=None):
    qs = self.filter_by_owner(self.model.objects.all())
    return qs

# ❌ Bad - skipping ownership filter
def get_base_queryset(self, search='', filters=None):
    return self.model.objects.all()  # Shows everyone's data!
```

### 2. Set Owner on Create

```python
# ✅ Good - set owner explicitly
def create_item(self):
    item = self.model.objects.create(
        **self.state.create_buffer.dict(),
        user=self.current_user  # Explicit owner
    )

# ❌ Bad - letting client set owner
def create_item(self):
    # Client could send user_id for another user!
    item = self.model.objects.create(
        **self.state.create_buffer.dict()
    )
```

### 3. Double-Check on Delete/Update

```python
# ✅ Good - verify ownership before delete
def delete_item(self, id: int):
    try:
        item = self.model.objects.get(
            id=id,
            user=self.current_user  # Ensure ownership
        )
        item.delete()
    except self.model.DoesNotExist:
        self.error("Not found or access denied")

# ❌ Bad - trusting that id is valid
def delete_item(self, id: int):
    item = self.model.objects.get(id=id)  # Could be another user's!
    item.delete()
```

### 4. Handle Anonymous Users

```python
def get_base_queryset(self, search='', filters=None):
    # ✅ OwnershipMixin handles this automatically
    qs = self.filter_by_owner(self.model.objects.all())
    # Returns queryset.none() if not authenticated

    # ✅ Or check manually
    if not self.is_authenticated:
        return self.model.objects.none()

    return self.model.objects.filter(user=self.current_user)
```

## Best Practices

### 1. Use Consistent Field Names

```python
# ✅ Good - consistent naming
class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

# Both use owner_field = 'user'
```

### 2. Optimize Related Queries

```python
def get_base_queryset(self, search='', filters=None):
    qs = self.filter_by_owner(self.model.objects.all())

    # ✅ Load related data efficiently
    qs = qs.select_related('category')

    return qs
```

### 3. Require Authentication

```python
def create_item(self):
    # ✅ Enforce authentication
    if not self.require_auth("Please log in"):
        return

    # Create with current_user as owner
    ...
```

### 4. Add Database Indexes

```python
class Document(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_index=True  # ✅ Index for fast filtering
    )
```

## Common Patterns

### Read-Only List for Users

```python
@register_component
class MyOrders(OwnershipMixin, BaseListComponent[OrderListState]):
    model = Order
    owner_field = 'customer'

    # Users can view their orders but not create/edit/delete
    # Simply don't override create_item, delete_item, etc.
```

### Shared Resources

```python
class SharedDocumentsMixin:
    def filter_by_owner(self, queryset):
        if not self.is_authenticated:
            return queryset.none()

        # Show documents user owns OR has been shared with
        return queryset.filter(
            Q(owner=self.current_user) |
            Q(shared_with=self.current_user)
        ).distinct()
```

## Troubleshooting

### Empty List (No Items Showing)

Check:
1. Is `owner_field` correct?
2. Do items have the correct owner set?
3. Is user authenticated?

```python
# Debug
def get_initial_state(self, **kwargs):
    print(f"User: {self.current_user}")
    print(f"Owner field: {self.owner_field}")

    qs = self.filter_by_owner(self.model.objects.all())
    print(f"Count: {qs.count()}")

    return MyListState(items=[...])
```

### Wrong Items Showing

Verify ownership filtering is applied:

```python
def get_base_queryset(self, search='', filters=None):
    # Make sure this is called!
    qs = self.filter_by_owner(self.model.objects.all())

    # Not this:
    # qs = self.model.objects.all()  # WRONG!

    return qs
```

## See Also

- [TenantScopedMixin](tenant-scoped-mixin.md) - Multi-tenant filtering
- [PermissionMixin](permission-mixin.md) - Custom permissions
- [Security Overview](overview.md) - Security best practices
