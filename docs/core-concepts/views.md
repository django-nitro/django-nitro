# Views

Nitro provides Django class-based views with HTMX integration.

## View Hierarchy

```
NitroView              → Base with HTMX helpers, toasts
├── NitroListView      → Search, filter, sort, pagination
├── NitroModelView     → Single object detail
├── NitroFormView      → Form handling
│   ├── NitroCreateView → Create with auto company/user
│   └── NitroUpdateView → Edit existing
└── NitroDeleteView    → Delete with soft-delete support
```

---

## NitroView

Base view for all Nitro views.

```python
from nitro.views import NitroView

class DashboardView(NitroView):
    template_name = 'dashboard.html'
    partial_template = 'partials/dashboard_content.html'
```

### Properties

| Property | Description |
|----------|-------------|
| `template_name` | Full page template |
| `partial_template` | Template for HTMX requests |
| `is_htmx` | `True` if request is HTMX |

### Methods

```python
# HTMX detection
if self.is_htmx:
    return self.render_partial()

# Toast notifications
self.toast('Mensaje', 'success')  # success, error, warning, info
self.success('Guardado')
self.error('Error al guardar')

# HTMX responses
self.htmx_redirect('/url/')      # Client-side redirect
self.htmx_refresh()              # Refresh page
self.htmx_trigger('event-name')  # Trigger JS event
```

---

## NitroListView

List view with built-in search, filters, sorting, and pagination.

```python
from nitro.views import NitroListView

class TenantListView(NitroListView):
    model = Tenant
    template_name = 'tenants/list.html'
    partial_template = 'tenants/partials/list_content.html'

    # Search
    search_fields = ['name', 'email', 'phone']

    # Filters
    filter_fields = ['status', 'property']

    # Sorting
    sortable_fields = ['name', 'created_at', 'rent_amount']
    default_sort = '-created_at'

    # Pagination
    paginate_by = 25

    # Query optimization
    select_related = ['property', 'company']
    prefetch_related = ['leases']

    def get_filter_options(self):
        return {
            'status': [('active', 'Activo'), ('inactive', 'Inactivo')],
            'property': [(p.id, p.name) for p in Property.objects.all()],
        }
```

### Context Variables

| Variable | Description |
|----------|-------------|
| `object_list` | Paginated queryset |
| `page_obj` | Paginator page object |
| `filter_options` | From `get_filter_options()` |
| `current_filters` | Current filter values |
| `current_search` | Current search query |
| `current_sort` | Current sort field |
| `total_count` | Total objects count |

---

## NitroModelView

Detail view for a single model instance.

```python
from nitro.views import NitroModelView

class PropertyDetailView(NitroModelView):
    model = Property
    template_name = 'properties/detail.html'
    context_object_name = 'property'
```

Access the object via `{{ object }}` or `{{ property }}` in template.

---

## NitroFormView

Form handling with HTMX support.

```python
from nitro.views import NitroFormView

class ContactFormView(NitroFormView):
    form_class = ContactForm
    template_name = 'contact/form.html'
    success_url = '/contact/thanks/'
    success_message = 'Mensaje enviado'
```

On HTMX submit, returns toast notification. On regular submit, redirects.

---

## NitroCreateView

Create view with automatic company/user assignment.

```python
from nitro.views import NitroCreateView
from nitro.mixins import OrganizationMixin

class PropertyCreateView(OrganizationMixin, NitroCreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/form.html'
    success_message = 'Propiedad creada'
```

Automatically sets:

- `obj.company = self.organization` (if using OrganizationMixin)
- `obj.created_by = request.user` (if model has field)

---

## NitroUpdateView

Update existing instance.

```python
from nitro.views import NitroUpdateView

class PropertyUpdateView(OrganizationMixin, NitroUpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/form.html'
    success_message = 'Propiedad actualizada'
```

---

## NitroDeleteView

Delete with soft-delete support.

```python
from nitro.views import NitroDeleteView

class PropertyDeleteView(OrganizationMixin, NitroDeleteView):
    model = Property
    success_url = '/properties/'
    success_message = 'Propiedad eliminada'

    def can_delete(self, obj):
        """Optional: check if deletion is allowed."""
        if obj.leases.filter(status='active').exists():
            return False, 'Tiene contratos activos'
        return True, None
```

If the model has `soft_delete()` method, it calls that instead of `delete()`.
