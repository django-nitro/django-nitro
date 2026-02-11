# Multi-Tenancy

Nitro provides mixins for building multi-tenant applications where data is scoped to organizations (companies, teams, etc.).

## OrganizationMixin

Base mixin for organization-scoped views.

```python
from nitro.mixins import OrganizationMixin

class CompanyMixin(OrganizationMixin):
    """Your app-specific implementation."""
    org_field = 'company'  # Field name on models

    def get_organization(self):
        """Return the current organization."""
        return self.request.user.company
```

## Using in Views

```python
class PropertyListView(CompanyMixin, NitroListView):
    model = Property
    # Queryset automatically filtered by company
```

```python
class PropertyCreateView(CompanyMixin, NitroCreateView):
    model = Property
    form_class = PropertyForm
    # obj.company automatically set on save
```

## How It Works

### Automatic Queryset Filtering

```python
# Without mixin:
def get_queryset(self):
    return Property.objects.filter(company=self.request.user.company)

# With mixin (automatic):
class PropertyListView(CompanyMixin, NitroListView):
    model = Property
    # Queryset already filtered by company
```

### Automatic Assignment on Create

```python
# Without mixin:
def form_valid(self, form):
    obj = form.save(commit=False)
    obj.company = self.request.user.company
    obj.save()

# With mixin (automatic):
class PropertyCreateView(CompanyMixin, NitroCreateView):
    model = Property
    form_class = PropertyForm
    # company field automatically set
```

## Advanced Configuration

### Custom Organization Field

```python
class TeamMixin(OrganizationMixin):
    org_field = 'team'  # Models use 'team' instead of 'company'

    def get_organization(self):
        return self.request.user.team
```

### Session-Based Organization

For superusers who can switch between organizations:

```python
class CompanyMixin(OrganizationMixin):
    org_field = 'company'

    def get_organization(self):
        # Check session first (for superusers)
        if self.request.user.is_superuser:
            company_id = self.request.session.get('current_company_id')
            if company_id:
                return Company.objects.get(id=company_id)

        # Fall back to user's company
        return self.request.user.company
```

### Optional Organization

Some models may not require organization scoping:

```python
class PropertyListView(CompanyMixin, NitroListView):
    model = Property

    def get_queryset(self):
        qs = super().get_queryset()
        # Additional filtering
        return qs.filter(is_published=True)
```

## Related Mixins

### OwnerRequiredMixin

Ensure user owns the object.

```python
from nitro.mixins import OwnerRequiredMixin

class ProfileUpdateView(OwnerRequiredMixin, NitroUpdateView):
    model = Profile
    owner_field = 'user'  # Profile.user must match request.user
```

### StaffRequiredMixin

Require staff status.

```python
from nitro.mixins import StaffRequiredMixin

class AdminDashboardView(StaffRequiredMixin, NitroView):
    template_name = 'admin/dashboard.html'
```

### PermissionRequiredMixin

Require specific permissions.

```python
from nitro.mixins import PermissionRequiredMixin

class PropertyDeleteView(PermissionRequiredMixin, NitroDeleteView):
    model = Property
    permission_required = 'leasing.delete_property'
```

## Security Best Practices

1. **Always use organization mixins** for tenant-scoped data
2. **Validate in forms** that related objects belong to same organization
3. **Check permissions** before sensitive operations
4. **Audit sensitive actions** with logging

```python
class LeaseCreateView(CompanyMixin, NitroCreateView):
    model = Lease
    form_class = LeaseForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Limit property choices to current company
        form.fields['property'].queryset = Property.objects.filter(
            company=self.organization
        )
        return form
```
