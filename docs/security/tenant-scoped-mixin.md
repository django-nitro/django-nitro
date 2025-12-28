# TenantScopedMixin

`TenantScopedMixin` provides multi-tenant data isolation for SaaS applications. It ensures users only see data belonging to their organization, company, or team - preventing data leakage between tenants.

## Use Cases

- **SaaS Applications** - Company/organization-scoped data
- **Team Workspaces** - Team-based access control
- **Multi-tenant Platforms** - Isolated data per tenant
- **Enterprise Applications** - Department/division isolation

## Basic Usage

```python
from nitro.security import TenantScopedMixin
from nitro.list import BaseListComponent, BaseListState
from nitro.registry import register_component

@register_component
class CompanyDocuments(TenantScopedMixin, BaseListComponent[DocumentListState]):
    model = Document
    tenant_field = 'organization'  # Field linking to tenant (default: 'organization')

    def get_user_tenant(self):
        """REQUIRED: Return current user's tenant."""
        return self.request.user.profile.organization

    # Automatically filters to current organization's documents only
```

## Configuration

### `tenant_field: str`

The name of the ForeignKey field linking to your tenant model.

**Default:** `'organization'`

```python
class CompanyDocuments(TenantScopedMixin, BaseListComponent):
    tenant_field = 'organization'  # Document.organization
    # or
    tenant_field = 'company'       # Document.company
    # or
    tenant_field = 'team'          # Document.team
```

Your model must have this field:

```python
class Document(models.Model):
    title = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

### `get_user_tenant() -> Model`

**REQUIRED** method that returns the current user's tenant.

```python
def get_user_tenant(self):
    # From user profile
    return self.request.user.profile.organization

    # Or from session
    # return Organization.objects.get(id=self.request.session['org_id'])

    # Or from custom user model
    # return self.request.user.current_organization
```

## Methods

### `filter_by_tenant(queryset) -> QuerySet`

Filters a queryset to show only items belonging to the current tenant.

**Returns:**
- Filtered queryset if tenant exists
- Empty queryset if tenant is None

```python
def get_base_queryset(self, search='', filters=None):
    # Start with all items
    qs = self.model.objects.all()

    # Filter to current tenant
    qs = self.filter_by_tenant(qs)

    # Apply search
    if search:
        qs = self.apply_search(qs, search)

    return qs.order_by('-created_at')
```

## How It Works

Behind the scenes:

```python
def filter_by_tenant(self, queryset):
    tenant = self.get_user_tenant()
    if not tenant:
        return queryset.none()  # Empty queryset

    # Filter: queryset.filter(organization=current_tenant)
    return queryset.filter(**{self.tenant_field: tenant})
```

## Complete Example

```python
from django.db import models
from django.contrib.auth.models import User
from pydantic import BaseModel, Field
from nitro.security import TenantScopedMixin
from nitro.list import BaseListComponent, BaseListState
from nitro.registry import register_component
from typing import Optional

# Tenant Model
class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# User Profile with Organization
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, default='member')

    def __str__(self):
        return f"{self.user.username} @ {self.organization.name}"

# Multi-tenant Model
class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
        ]

# Schemas
class ProjectSchema(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool

    class Config:
        from_attributes = True

class ProjectFormSchema(BaseModel):
    name: str = ""
    description: str = ""

class ProjectListState(BaseListState):
    items: list[ProjectSchema] = []
    create_buffer: ProjectFormSchema = Field(default_factory=ProjectFormSchema)
    edit_buffer: Optional[ProjectFormSchema] = None

# Multi-tenant Component
@register_component
class OrganizationProjects(TenantScopedMixin, BaseListComponent[ProjectListState]):
    template_name = "components/organization_projects.html"
    state_class = ProjectListState
    model = Project
    tenant_field = 'organization'  # Project.organization field

    search_fields = ['name', 'description']
    per_page = 25
    order_by = '-created_at'

    def get_user_tenant(self):
        """Get current user's organization."""
        if not self.is_authenticated:
            return None

        # Assumes user has a profile with organization
        if hasattr(self.current_user, 'profile'):
            return self.current_user.profile.organization

        return None

    def create_item(self):
        """Create project in current tenant."""
        if not self.require_auth():
            return

        tenant = self.get_user_tenant()
        if not tenant:
            self.error("No organization found")
            return

        try:
            project = self.model.objects.create(
                **self.state.create_buffer.dict(),
                organization=tenant,  # Set tenant
                created_by=self.current_user
            )
            self.refresh()
            self.success(f"Created: {project.name}")
        except Exception as e:
            logger.exception("Create failed")
            self.error("Failed to create project")

    def toggle_active(self, id: int):
        """Custom action with tenant check."""
        tenant = self.get_user_tenant()
        if not tenant:
            self.error("No organization found")
            return

        try:
            # Verify project belongs to current tenant
            project = self.model.objects.get(
                id=id,
                organization=tenant
            )
            project.is_active = not project.is_active
            project.save()
            self.refresh()

            status = "activated" if project.is_active else "deactivated"
            self.success(f"{project.name} {status}")
        except self.model.DoesNotExist:
            self.error("Project not found in your organization")
```

## Tenant Models

### Typical Tenant Model

```python
class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    plan = models.CharField(max_length=50, default='free')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional: limits per plan
    max_users = models.IntegerField(default=5)
    max_projects = models.IntegerField(default=10)
```

### User-Tenant Relationship

#### Option 1: OneToOne Profile

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

def get_user_tenant(self):
    return self.current_user.profile.organization
```

#### Option 2: Custom User Model

```python
from django.contrib.auth.models.AbstractUser

class CustomUser(AbstractUser):
    current_organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True
    )

def get_user_tenant(self):
    return self.current_user.current_organization
```

#### Option 3: ManyToMany (User in multiple orgs)

```python
class Organization(models.Model):
    name = models.CharField(max_length=200)
    members = models.ManyToManyField(User, through='Membership')

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)

def get_user_tenant(self):
    # From session - user selects which org
    org_id = self.request.session.get('current_organization_id')
    if org_id:
        return Organization.objects.get(id=org_id)
    return None
```

## Combining with OwnershipMixin

Filter by both tenant AND user:

```python
from nitro.security import OwnershipMixin, TenantScopedMixin

@register_component
class MyTeamTasks(
    OwnershipMixin,       # Filter by current user
    TenantScopedMixin,    # Filter by current team
    BaseListComponent[TaskListState]
):
    model = Task
    owner_field = 'user'
    tenant_field = 'team'

    def get_user_tenant(self):
        return self.current_user.profile.team

    def get_base_queryset(self, search='', filters=None):
        # Both filters applied
        qs = self.model.objects.all()

        # First: filter by tenant (team)
        qs = self.filter_by_tenant(qs)

        # Then: filter by owner (user)
        qs = self.filter_by_owner(qs)

        # Result: user's tasks within their team

        if search:
            qs = self.apply_search(qs, search)

        return qs.order_by(self.order_by)
```

## Security Considerations

### 1. Always Set Tenant on Create

```python
# ✅ Good - set tenant explicitly
def create_item(self):
    tenant = self.get_user_tenant()
    if not tenant:
        self.error("No organization")
        return

    item = self.model.objects.create(
        **self.state.create_buffer.dict(),
        organization=tenant  # Explicit tenant
    )

# ❌ Bad - letting client set tenant
def create_item(self):
    # Client could send organization_id for another org!
    item = self.model.objects.create(
        **self.state.create_buffer.dict()
    )
```

### 2. Verify Tenant on Update/Delete

```python
# ✅ Good - verify tenant before delete
def delete_item(self, id: int):
    tenant = self.get_user_tenant()
    if not tenant:
        return

    try:
        item = self.model.objects.get(
            id=id,
            organization=tenant  # Ensure correct tenant
        )
        item.delete()
    except self.model.DoesNotExist:
        self.error("Not found in your organization")

# ❌ Bad - trusting that id is valid
def delete_item(self, id: int):
    item = self.model.objects.get(id=id)  # Could be another org's!
    item.delete()
```

### 3. Handle Missing Tenant

```python
def get_initial_state(self, **kwargs):
    tenant = self.get_user_tenant()
    if not tenant:
        # No organization - show empty list
        return MyListState(items=[])

    # Load items for tenant
    ...
```

### 4. Validate Tenant Exists

```python
def get_user_tenant(self):
    if not self.is_authenticated:
        return None

    try:
        return self.current_user.profile.organization
    except (AttributeError, Organization.DoesNotExist):
        logger.warning(f"User {self.current_user.id} has no organization")
        return None
```

## Advanced Patterns

### Hierarchical Tenants

```python
class Department(models.Model):
    name = models.CharField(max_length=200)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, on_delete=models.CASCADE)

class Project(models.Model):
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

@register_component
class DepartmentProjects(TenantScopedMixin, BaseListComponent):
    model = Project
    tenant_field = 'department'

    def get_user_tenant(self):
        # From session - user selects department
        dept_id = self.request.session.get('current_department')
        if dept_id:
            # Verify department belongs to user's organization
            return Department.objects.get(
                id=dept_id,
                organization=self.current_user.profile.organization
            )
        return None
```

### Tenant Switching

```python
@register_component
class TenantSwitcher(NitroComponent[TenantSwitcherState]):
    def switch_organization(self, org_id: int):
        """Allow user to switch between their organizations."""
        # Verify user is member of this org
        try:
            membership = Membership.objects.get(
                user=self.current_user,
                organization_id=org_id
            )

            # Store in session
            self.request.session['current_organization_id'] = org_id
            self.success(f"Switched to {membership.organization.name}")

        except Membership.DoesNotExist:
            self.error("You're not a member of this organization")
```

### Tenant-Aware Permissions

```python
from nitro.security import TenantScopedMixin, PermissionMixin

@register_component
class TenantDocuments(
    TenantScopedMixin,
    PermissionMixin,
    BaseListComponent
):
    model = Document
    tenant_field = 'organization'

    def get_user_tenant(self):
        return self.current_user.profile.organization

    def check_permission(self, action: str) -> bool:
        """Permissions based on user's role in org."""
        try:
            membership = Membership.objects.get(
                user=self.current_user,
                organization=self.get_user_tenant()
            )

            if action == 'delete':
                return membership.role in ['admin', 'manager']

            if action == 'create':
                return membership.role != 'viewer'

            return True  # read allowed for all members

        except Membership.DoesNotExist:
            return False
```

## Best Practices

### 1. Always Implement get_user_tenant()

```python
# ✅ Required
def get_user_tenant(self):
    return self.current_user.profile.organization

# ❌ Will raise NotImplementedError
# (Don't skip this method!)
```

### 2. Add Database Indexes

```python
class Project(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        db_index=True  # ✅ Index for fast filtering
    )

    class Meta:
        indexes = [
            # ✅ Composite index for tenant + created_at
            models.Index(fields=['organization', '-created_at']),
        ]
```

### 3. Optimize Related Queries

```python
def get_base_queryset(self, search='', filters=None):
    qs = self.filter_by_tenant(self.model.objects.all())

    # ✅ Eager load tenant data
    qs = qs.select_related('organization')

    return qs
```

### 4. Log Tenant Access

```python
def get_base_queryset(self, search='', filters=None):
    tenant = self.get_user_tenant()

    # ✅ Log for audit trail
    logger.info(
        f"User {self.current_user.id} accessing "
        f"data for org {tenant.id if tenant else 'None'}"
    )

    qs = self.filter_by_tenant(self.model.objects.all())
    return qs
```

## Troubleshooting

### Empty List (No Items)

Check:
1. Does user have a tenant set?
2. Is `tenant_field` correct?
3. Do items have the correct tenant set?

```python
def get_initial_state(self, **kwargs):
    tenant = self.get_user_tenant()
    print(f"Tenant: {tenant}")
    print(f"Tenant field: {self.tenant_field}")

    qs = self.filter_by_tenant(self.model.objects.all())
    print(f"Count: {qs.count()}")
    ...
```

### NotImplementedError

Means you forgot to implement `get_user_tenant()`:

```python
# ✅ Always implement this method
def get_user_tenant(self):
    return self.current_user.profile.organization
```

## See Also

- [OwnershipMixin](ownership-mixin.md) - Filter by user ownership
- [PermissionMixin](permission-mixin.md) - Custom permissions
- [Security Overview](overview.md) - Security best practices
