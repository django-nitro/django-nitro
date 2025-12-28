# PermissionMixin

`PermissionMixin` provides a framework for implementing custom permission logic beyond Django's built-in permissions. It's perfect for role-based access control (RBAC), action-level authorization, and complex business rules.

## Use Cases

- **Role-Based Access Control (RBAC)** - Different permissions for admin, manager, member
- **Action-Level Permissions** - Control who can create, edit, delete
- **Subscription-Based Access** - Feature gating based on plan tier
- **Custom Business Rules** - Complex permission logic
- **Conditional Access** - Time-based, location-based, or context-based permissions

## Basic Usage

```python
from nitro.security import PermissionMixin
from nitro.base import CrudNitroComponent
from nitro.registry import register_component

@register_component
class DocumentManager(PermissionMixin, CrudNitroComponent[DocumentState]):
    model = Document

    def check_permission(self, action: str) -> bool:
        """Override with your permission logic."""
        user = self.current_user

        if not user or not user.is_authenticated:
            return False

        # Admins can do anything
        if user.is_superuser:
            return True

        # Custom logic per action
        if action == 'delete':
            return user.has_perm('documents.delete_document')

        if action in ['create', 'edit']:
            return user.has_perm('documents.change_document')

        return True  # Read allowed by default

    def delete_item(self, id: int):
        # Enforce permission
        if not self.enforce_permission('delete', "Only admins can delete"):
            return

        super().delete_item(id)
```

## Methods

### `check_permission(action: str) -> bool`

**REQUIRED** - Override this method with your permission logic.

**Parameters:**
- `action` - String identifying the action (e.g., 'create', 'edit', 'delete', 'export')

**Returns:**
- `True` if permission granted
- `False` if permission denied

```python
def check_permission(self, action: str) -> bool:
    user = self.current_user

    if not user:
        return False

    # Your logic here
    if action == 'delete':
        return user.is_staff

    return True
```

### `enforce_permission(action: str, error_message: Optional[str] = None) -> bool`

Checks permission and shows error message if denied.

**Parameters:**
- `action` - Action to check permission for
- `error_message` - Custom error message (default: "Permission denied")

**Returns:**
- `True` if permission granted
- `False` if permission denied (and error message shown)

```python
def delete_item(self, id: int):
    # Check permission and show error if denied
    if not self.enforce_permission('delete', "Only managers can delete"):
        return  # Stops execution

    # Continue with delete...
    super().delete_item(id)
```

## Complete Example

```python
from django.db import models
from django.contrib.auth.models import User
from pydantic import BaseModel, Field
from nitro.security import PermissionMixin, OwnershipMixin
from nitro.list import BaseListComponent, BaseListState
from nitro.registry import register_component
from typing import Optional

# Models
class UserRole(models.TextChoices):
    VIEWER = 'viewer', 'Viewer'
    MEMBER = 'member', 'Member'
    MANAGER = 'manager', 'Manager'
    ADMIN = 'admin', 'Admin'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.MEMBER)
    subscription_tier = models.CharField(max_length=20, default='free')

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# Schemas
class ProjectSchema(BaseModel):
    id: int
    name: str
    description: str
    is_archived: bool

    class Config:
        from_attributes = True

class ProjectFormSchema(BaseModel):
    name: str = ""
    description: str = ""

class ProjectListState(BaseListState):
    items: list[ProjectSchema] = []
    create_buffer: ProjectFormSchema = Field(default_factory=ProjectFormSchema)
    edit_buffer: Optional[ProjectFormSchema] = None

# Component with Permission Control
@register_component
class ProjectManager(
    PermissionMixin,
    OwnershipMixin,
    BaseListComponent[ProjectListState]
):
    template_name = "components/project_manager.html"
    state_class = ProjectListState
    model = Project
    owner_field = 'owner'

    search_fields = ['name', 'description']
    per_page = 25

    def check_permission(self, action: str) -> bool:
        """Role-based permission logic."""
        user = self.current_user

        # Not authenticated = no access
        if not user or not user.is_authenticated:
            return False

        # Get user's role
        try:
            role = user.profile.role
        except (AttributeError, UserProfile.DoesNotExist):
            return False

        # Admins can do anything
        if role == UserRole.ADMIN:
            return True

        # Managers can create, edit, read
        if role == UserRole.MANAGER:
            if action == 'delete':
                return False  # Managers can't delete
            return True

        # Members can create and read
        if role == UserRole.MEMBER:
            if action in ['delete', 'archive']:
                return False
            if action == 'edit':
                return False  # Can only edit own (checked elsewhere)
            return True

        # Viewers can only read
        if role == UserRole.VIEWER:
            if action in ['create', 'edit', 'delete', 'archive']:
                return False
            return True

        return False

    def create_item(self):
        """Create with permission check."""
        if not self.enforce_permission('create', "You don't have permission to create projects"):
            return

        # Check subscription limits
        if not self._check_subscription_limit():
            return

        try:
            project = self.model.objects.create(
                **self.state.create_buffer.dict(),
                owner=self.current_user
            )
            self.refresh()
            self.success(f"Created: {project.name}")
        except Exception as e:
            logger.exception("Create failed")
            self.error("Failed to create project")

    def save_edit(self):
        """Edit with permission check."""
        if not self.enforce_permission('edit', "You don't have permission to edit"):
            return

        # Additional ownership check
        try:
            project = self.model.objects.get(id=self.state.editing_id)

            # Members can only edit their own projects
            if self.current_user.profile.role == UserRole.MEMBER:
                if project.owner != self.current_user:
                    self.error("You can only edit your own projects")
                    return

            # Proceed with edit
            super().save_edit()

        except (Project.DoesNotExist, AttributeError):
            self.error("Project not found")

    def delete_item(self, id: int):
        """Delete with permission check."""
        if not self.enforce_permission('delete', "Only admins can delete projects"):
            return

        super().delete_item(id)

    def archive_project(self, id: int):
        """Custom action with permission check."""
        if not self.enforce_permission('archive', "You don't have permission to archive"):
            return

        try:
            project = self.model.objects.get(id=id, owner=self.current_user)
            project.is_archived = not project.is_archived
            project.save()
            self.refresh()

            status = "archived" if project.is_archived else "unarchived"
            self.success(f"{project.name} {status}")
        except Project.DoesNotExist:
            self.error("Project not found")

    def _check_subscription_limit(self) -> bool:
        """Helper to check subscription limits."""
        try:
            tier = self.current_user.profile.subscription_tier

            if tier == 'free':
                # Free tier: max 3 projects
                count = self.model.objects.filter(owner=self.current_user).count()
                if count >= 3:
                    self.error("Free tier limited to 3 projects. Upgrade to create more.")
                    return False

            # Paid tiers have unlimited projects
            return True

        except AttributeError:
            return False
```

## Permission Patterns

### Django Permission System

```python
def check_permission(self, action: str) -> bool:
    user = self.current_user
    if not user:
        return False

    # Use Django's built-in permissions
    if action == 'create':
        return user.has_perm('myapp.add_project')

    if action == 'edit':
        return user.has_perm('myapp.change_project')

    if action == 'delete':
        return user.has_perm('myapp.delete_project')

    return user.has_perm('myapp.view_project')
```

### Role-Based (RBAC)

```python
def check_permission(self, action: str) -> bool:
    user = self.current_user
    if not user:
        return False

    role = user.profile.role

    # Define role permissions
    PERMISSIONS = {
        'admin': ['create', 'read', 'edit', 'delete', 'export'],
        'manager': ['create', 'read', 'edit', 'export'],
        'member': ['create', 'read'],
        'viewer': ['read'],
    }

    allowed_actions = PERMISSIONS.get(role, [])
    return action in allowed_actions
```

### Subscription-Based

```python
def check_permission(self, action: str) -> bool:
    user = self.current_user
    if not user:
        return False

    tier = user.profile.subscription_tier

    # Free tier restrictions
    if tier == 'free':
        if action == 'export':
            return False
        if action == 'create':
            # Check limits
            count = Project.objects.filter(owner=user).count()
            return count < 3

    # Pro tier restrictions
    if tier == 'pro':
        if action == 'export':
            return True
        if action == 'create':
            count = Project.objects.filter(owner=user).count()
            return count < 50

    # Enterprise tier: no restrictions
    return True
```

### Owner-Only Actions

```python
def check_permission(self, action: str) -> bool:
    user = self.current_user
    if not user:
        return False

    # Anyone can read
    if action == 'read':
        return True

    # Only authenticated can create
    if action == 'create':
        return user.is_authenticated

    # Only owners can edit/delete
    # (check in action method, not here)
    if action in ['edit', 'delete']:
        return user.is_authenticated

    return False

def delete_item(self, id: int):
    if not self.enforce_permission('delete'):
        return

    # Check ownership
    try:
        item = self.model.objects.get(id=id)
        if item.owner != self.current_user:
            self.error("You don't own this item")
            return

        item.delete()
        self.refresh()
    except self.model.DoesNotExist:
        self.error("Item not found")
```

### Time-Based Permissions

```python
from django.utils import timezone

def check_permission(self, action: str) -> bool:
    user = self.current_user
    if not user:
        return False

    # Business hours only
    if action in ['delete', 'export']:
        now = timezone.now()
        if now.hour < 9 or now.hour >= 17:
            self.error("This action is only allowed during business hours (9-5)")
            return False

    # Weekend restrictions
    if action == 'delete':
        if now.weekday() >= 5:  # Saturday or Sunday
            self.error("Deletions not allowed on weekends")
            return False

    return True
```

### Composite Permissions

```python
def check_permission(self, action: str) -> bool:
    user = self.current_user
    if not user:
        return False

    # Must have both role AND Django permission
    has_role = user.profile.role in ['admin', 'manager']
    has_perm = user.has_perm(f'myapp.{action}_project')

    return has_role and has_perm
```

## Combining with Other Mixins

### With OwnershipMixin

```python
from nitro.security import PermissionMixin, OwnershipMixin

@register_component
class MyProjects(
    PermissionMixin,
    OwnershipMixin,
    BaseListComponent
):
    model = Project
    owner_field = 'owner'

    def check_permission(self, action: str) -> bool:
        # Permission logic
        ...

    # get_base_queryset automatically filters by owner
    # Permission checks happen in action methods
```

### With TenantScopedMixin

```python
from nitro.security import PermissionMixin, TenantScopedMixin

@register_component
class CompanyProjects(
    PermissionMixin,
    TenantScopedMixin,
    BaseListComponent
):
    model = Project
    tenant_field = 'organization'

    def get_user_tenant(self):
        return self.current_user.profile.organization

    def check_permission(self, action: str) -> bool:
        """Permissions based on role within organization."""
        try:
            membership = Membership.objects.get(
                user=self.current_user,
                organization=self.get_user_tenant()
            )

            if action == 'delete':
                return membership.role == 'admin'

            if action in ['create', 'edit']:
                return membership.role in ['admin', 'manager']

            return True  # Read allowed for all members

        except Membership.DoesNotExist:
            return False
```

## Advanced Patterns

### Caching Permissions

```python
from django.core.cache import cache

def check_permission(self, action: str) -> bool:
    user = self.current_user
    if not user:
        return False

    # Cache permissions for 5 minutes
    cache_key = f"perms_{user.id}_{action}"
    result = cache.get(cache_key)

    if result is None:
        # Expensive permission check
        result = self._compute_permission(action)
        cache.set(cache_key, result, 300)  # 5 minutes

    return result

def _compute_permission(self, action: str) -> bool:
    # Your expensive logic here
    ...
```

### Logging Permission Denials

```python
import logging

logger = logging.getLogger(__name__)

def enforce_permission(self, action: str, error_message: Optional[str] = None) -> bool:
    if not self.check_permission(action):
        # Log denial
        logger.warning(
            f"Permission denied: user={self.current_user.id} "
            f"action={action} component={self.__class__.__name__}"
        )

        # Show error
        self.error(error_message or "Permission denied")
        return False

    return True
```

### Dynamic Permission Messages

```python
def delete_item(self, id: int):
    user = self.current_user

    # Custom messages based on why permission denied
    if not user:
        if not self.enforce_permission('delete', "Please log in to delete"):
            return

    elif not user.is_staff:
        if not self.enforce_permission('delete', "Only staff members can delete"):
            return

    elif user.profile.subscription_tier == 'free':
        if not self.enforce_permission('delete', "Upgrade to Pro to delete items"):
            return

    else:
        if not self.enforce_permission('delete'):
            return

    # Proceed with delete
    super().delete_item(id)
```

## Best Practices

### 1. Always Implement check_permission()

```python
# ✅ Required
def check_permission(self, action: str) -> bool:
    # Your logic
    return True

# ❌ Will raise NotImplementedError
# (Don't skip this method!)
```

### 2. Use enforce_permission() in Actions

```python
# ✅ Good - permission checked
def delete_item(self, id: int):
    if not self.enforce_permission('delete'):
        return
    super().delete_item(id)

# ❌ Bad - no permission check
def delete_item(self, id: int):
    super().delete_item(id)
```

### 3. Provide Helpful Error Messages

```python
# ✅ Good - clear message
if not self.enforce_permission('export', "Upgrade to Pro to export data"):
    return

# ⚠️ OK - generic message
if not self.enforce_permission('export'):
    return  # Shows "Permission denied"
```

### 4. Don't Trust Client Data

```python
# ❌ Bad - client could fake role
def check_permission(self, action: str) -> bool:
    # Don't use state data for permissions!
    role = self.state.user_role  # Client controls this!
    return role == 'admin'

# ✅ Good - use server data
def check_permission(self, action: str) -> bool:
    role = self.current_user.profile.role  # Server truth
    return role == 'admin'
```

### 5. Keep Permission Logic Simple

```python
# ✅ Good - clear and simple
def check_permission(self, action: str) -> bool:
    if action == 'delete':
        return self.current_user.is_staff
    return True

# ❌ Avoid - too complex
def check_permission(self, action: str) -> bool:
    if ((action == 'delete' and self.current_user.is_staff) or
        (action == 'edit' and (self.current_user.is_staff or
         self.current_user.profile.role == 'manager')) or ...):
        # Too much nesting!
```

## Testing Permissions

```python
from django.test import TestCase, RequestFactory
from myapp.components import ProjectManager

class PermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = User.objects.create_user('admin', role='admin')
        self.member = User.objects.create_user('member', role='member')
        self.viewer = User.objects.create_user('viewer', role='viewer')

    def test_admin_can_delete(self):
        request = self.factory.get('/')
        request.user = self.admin

        component = ProjectManager(request=request)
        self.assertTrue(component.check_permission('delete'))

    def test_member_cannot_delete(self):
        request = self.factory.get('/')
        request.user = self.member

        component = ProjectManager(request=request)
        self.assertFalse(component.check_permission('delete'))

    def test_viewer_cannot_create(self):
        request = self.factory.get('/')
        request.user = self.viewer

        component = ProjectManager(request=request)
        self.assertFalse(component.check_permission('create'))
```

## Troubleshooting

### NotImplementedError

Means you forgot to implement `check_permission()`:

```python
# ✅ Always implement this method
def check_permission(self, action: str) -> bool:
    # Your logic here
    return True
```

### Permissions Not Working

Check:
1. Is `check_permission()` being called?
2. Is `enforce_permission()` used in action methods?
3. Are you checking server-side data (not client state)?

```python
# Debug
def check_permission(self, action: str) -> bool:
    print(f"Checking permission: {action}")
    print(f"User: {self.current_user}")
    result = # ... your logic
    print(f"Result: {result}")
    return result
```

## See Also

- [OwnershipMixin](ownership-mixin.md) - Filter by user ownership
- [TenantScopedMixin](tenant-scoped-mixin.md) - Multi-tenant filtering
- [Security Overview](overview.md) - Security best practices
