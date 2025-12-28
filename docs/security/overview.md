# Security

Django Nitro v0.3.0 introduces security mixins for common authentication and authorization patterns.

## Security Mixins

### [OwnershipMixin](ownership-mixin.md)

Filter querysets to show only the current user's data.

**Use case:** "My Orders", "My Documents", user-scoped data

```python
from nitro.security import OwnershipMixin
from nitro.list import BaseListComponent

class MyOrdersList(OwnershipMixin, BaseListComponent):
    model = Order
    owner_field = 'customer'  # FK to User

    def get_base_queryset(self, search='', filters=None):
        qs = self.filter_by_owner(self.model.objects.all())
        return qs.order_by('-created_at')
```

---

### [TenantScopedMixin](tenant-scoped-mixin.md)

Multi-tenant data isolation for SaaS applications.

**Use case:** Company-scoped data, organization isolation

```python
from nitro.security import TenantScopedMixin

class CompanyDocumentList(TenantScopedMixin, BaseListComponent):
    model = Document
    tenant_field = 'company'

    def get_user_tenant(self):
        return self.request.user.current_company
```

---

### [PermissionMixin](permission-mixin.md)

Framework for custom permission logic.

**Use case:** RBAC, custom permissions, action-level authorization

```python
from nitro.security import PermissionMixin

class InvoiceManager(PermissionMixin, CrudNitroComponent):
    def check_permission(self, action: str) -> bool:
        if action == 'delete':
            return self.request.user.has_perm('invoices.delete')
        return True

    def delete_item(self, id: int):
        if not self.enforce_permission('delete'):
            return
        super().delete_item(id)
```

## Request User Helpers

All `NitroComponent` instances now have convenient request helpers:

### current_user

Shortcut to `request.user` with authentication check.

```python
def create_item(self):
    if self.current_user:
        item.owner = self.current_user
        item.save()
```

### is_authenticated

Check if user is authenticated.

```python
def get_base_queryset(self, search='', filters=None):
    if not self.is_authenticated:
        return queryset.none()
    return queryset.filter(owner=self.current_user)
```

### require_auth()

Enforce authentication with error message.

```python
def delete_item(self, id: int):
    if not self.require_auth("You must be logged in"):
        return  # User sees error message

    super().delete_item(id)
```

## Best Practices

### 1. Always Check Permissions

```python
# ❌ BAD - No permission check
def delete_item(self, id: int):
    super().delete_item(id)

# ✅ GOOD - Permission checked
def delete_item(self, id: int):
    if not self.enforce_permission('delete'):
        return
    super().delete_item(id)
```

### 2. Filter by Ownership

```python
# ❌ BAD - Shows all users' data
def get_base_queryset(self, search='', filters=None):
    return Order.objects.all()

# ✅ GOOD - Only current user's data
def get_base_queryset(self, search='', filters=None):
    return self.filter_by_owner(Order.objects.all())
```

### 3. Validate on Server-Side

```python
# ❌ BAD - Trusting client data
def update_price(self, price: float):
    self.state.price = price  # Client can set any price!

# ✅ GOOD - Server validates
def update_price(self, price: float):
    if not self.request.user.is_staff:
        self.error("Only staff can change prices")
        return

    if price < 0:
        self.error("Price must be positive")
        return

    self.state.price = price
```

## Security Checklist

- [ ] All actions check `is_authenticated` if needed
- [ ] Permission checks use `enforce_permission()` or `has_perm()`
- [ ] Querysets filtered by ownership/tenant
- [ ] User input validated server-side
- [ ] Sensitive operations logged
- [ ] `secure_fields` includes all IDs
- [ ] Error messages don't leak sensitive data

## Learn More

- [OwnershipMixin Guide](ownership-mixin.md)
- [TenantScopedMixin Guide](tenant-scoped-mixin.md)
- [PermissionMixin Guide](permission-mixin.md)
