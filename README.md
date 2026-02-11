# Django Nitro

**Server-rendered Django views with HTMX + Alpine.js - No JavaScript required**

Django Nitro is a library of views, template tags, and components for building reactive Django applications using HTMX and Alpine.js. Server renders HTML, HTMX swaps it, Alpine handles local UI.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2+](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)

---

## Why Django Nitro?

- **Zero JavaScript** - Build reactive UIs with Python views and template tags
- **Standard Django** - Uses Django views, forms, and templates (no custom runtime)
- **HTMX powered** - Server-rendered HTML swaps for reactive interactions
- **Lightweight** - HTMX (~14KB) + Alpine.js (~15KB) via CDN
- **Batteries included** - Search, filters, pagination, modals, slideovers, toasts, file uploads, wizards
- **Multi-tenant ready** - Generic `OrganizationMixin` for multi-tenant apps

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Views](#views)
- [Template Tags](#template-tags)
- [Forms](#forms)
- [Components](#components)
- [Multi-Tenancy](#multi-tenancy)
- [Utilities](#utilities)
- [Migration from v0.7](#migration-from-v07)

---

## Installation

```bash
pip install django-nitro
```

### Requirements

- Python 3.12+
- Django 5.2+
- HTMX and Alpine.js (loaded via CDN, no pip install needed)

### Setup

**1. Add to INSTALLED_APPS**

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'nitro',
]
```

**2. Add scripts to your base template**

```html
{% load nitro_tags %}
<!DOCTYPE html>
<html>
<head>
    {% nitro_scripts %}
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body>
    {% block content %}{% endblock %}
    {% nitro_toast %}
</body>
</html>
```

`{% nitro_scripts %}` includes HTMX, `nitro.js`, and `alpine-components.js`.

---

## Quick Start

### 1. Define the View

```python
# views.py
from nitro.views import NitroListView

class PropertyListView(NitroListView):
    model = Property
    template_name = 'properties/property_list.html'
    partial_template = 'properties/partials/property_list_content.html'
    search_fields = ['name', 'address']
    filter_fields = ['status', 'property_type']
    paginate_by = 20
```

### 2. Create the Template

```html
<!-- property_list.html -->
{% load nitro_tags %}
{% extends "base.html" %}

{% block content %}
<div class="flex gap-4 mb-4">
    {% nitro_search target='#list-content' %}
    {% nitro_filter field='status' options=filter_options.status %}
</div>

<div id="list-content">
    {% include "properties/partials/property_list_content.html" %}
</div>
{% endblock %}
```

```html
<!-- partials/property_list_content.html -->
{% load nitro_tags %}
{% for property in object_list %}
<div class="p-4 border rounded-lg">
    <h3>{{ property.name }}</h3>
    <p>{{ property.address }}</p>
    <span>{{ property.status|status_badge }}</span>
</div>
{% endfor %}
{% nitro_pagination page_obj target='#list-content' %}
```

### 3. Wire the URL

```python
# urls.py
from .views import PropertyListView

urlpatterns = [
    path('properties/', PropertyListView.as_view(), name='property_list'),
]
```

That's it. Search with debounce, filters, and pagination all work via HTMX without writing JavaScript.

---

## Views

### NitroView

Base view with HTMX detection and toast helpers.

```python
from nitro.views import NitroView

class DashboardView(NitroView):
    template_name = 'dashboard.html'
    partial_template = 'partials/dashboard_content.html'  # for HTMX requests
```

**Methods:**
- `self.is_htmx` - Check if request is HTMX
- `self.toast(message, level)` - Send toast notification
- `self.success(message)` / `self.error(message)` - Toast shortcuts
- `self.htmx_redirect(url)` - Client-side redirect via HTMX
- `self.htmx_refresh()` - Refresh page via HTMX

### NitroListView

List view with built-in search, filters, sorting, and pagination.

```python
class TenantListView(NitroListView):
    model = Tenant
    template_name = 'tenants/list.html'
    partial_template = 'tenants/partials/list_content.html'
    search_fields = ['name', 'email', 'phone']
    filter_fields = ['status']
    sortable_fields = ['name', 'created_at']
    paginate_by = 25
    select_related = ['property']
    default_sort = '-created_at'

    def get_filter_options(self):
        return {
            'status': [('active', 'Activo'), ('inactive', 'Inactivo')],
        }
```

### NitroFormView

Form handling with HTMX support.

```python
class PropertyFormView(NitroFormView):
    form_class = PropertyForm
    template_name = 'properties/form.html'
    success_url = '/properties/'
```

### NitroCreateView / NitroUpdateView / NitroDeleteView

CRUD views with slideover + toast pattern:

```python
class PropertyCreateView(CompanyMixin, NitroCreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/form.html'
    # Automatically: closes slideover, shows toast, refreshes page

class PropertyUpdateView(CompanyMixin, NitroUpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'properties/form.html'

class PropertyDeleteView(CompanyMixin, NitroDeleteView):
    model = Property

    def can_delete(self, obj):
        if obj.leases.filter(status='active').exists():
            return False, 'Has active leases'
        return True, None
```

### NitroModelView

Detail view for a single model instance.

```python
class PropertyDetailView(NitroModelView):
    model = Property
    template_name = 'properties/detail.html'
```

### NitroWizard

Multi-step form wizard with session-based data persistence.

```python
from nitro.wizards import NitroWizard, WizardStep

class OnboardingWizard(NitroWizard):
    wizard_name = 'onboarding'
    steps = [
        WizardStep('company', CompanyForm, 'wizard/company.html', 'Company'),
        WizardStep('plan', PlanForm, 'wizard/plan.html', 'Plan'),
        WizardStep('confirm', None, 'wizard/confirm.html', 'Confirm'),
    ]

    def done(self, wizard_data):
        Company.objects.create(**wizard_data['company'])
        self.clear_wizard_data()
        return redirect('dashboard')
```

---

## Template Tags

Load with `{% load nitro_tags %}`.

### HTMX Action Tags

```html
{% nitro_search target='#list' placeholder='Search...' %}
{% nitro_filter field='status' options=opts target='#list' %}
{% nitro_pagination page_obj target='#list' %}
{% nitro_sort 'name' 'Name' target='#list' %}
{% nitro_delete url=delete_url target='#list' confirm='Delete?' %}
```

### Form Tags

```html
{% nitro_field form.name %}
{% nitro_select form.category search_url='/api/search/' %}
{% nitro_form_footer slideover='create-item' label='Save' %}
```

### Component Tags

```html
{% nitro_modal id='create' title='New Item' %}...{% end_nitro_modal %}
{% nitro_slideover id='edit' title='Edit' size='lg' %}...{% end_nitro_slideover %}
{% nitro_tabs id='tabs' target='#content' %}
    {% nitro_tab name='info' label='Info' active=True %}
    {% nitro_tab name='docs' label='Documents' %}
{% end_nitro_tabs %}
{% nitro_empty_state icon='icon' title='No data' message='Add your first item' %}
{% nitro_stats_card icon='icon' label='Revenue' value=total change='+12%' change_type='positive' %}
{% nitro_avatar user size='md' %}
{% nitro_file_upload upload_url='/upload/' field_name='file' accept='image/*' multiple=True %}
{% nitro_toast %}
```

### UI Helpers

```html
{% nitro_open_modal 'create' %}       {# attrs for a button to open modal #}
{% nitro_close_modal 'create' %}
{% nitro_open_slideover 'edit' %}
{% nitro_close_slideover 'edit' %}
{% nitro_scripts %}                    {# include HTMX + Nitro JS #}
```

### Transition Presets

```html
<div x-show="open" {% nitro_transition 'fade' %}>...</div>
<div x-show="open" {% nitro_transition 'slide-up' '200' %}>...</div>
<div x-show="open" {% nitro_transition 'scale' %}>...</div>
```

Presets: `fade`, `slide-up`, `slide-down`, `slide-right`, `slide-left`, `scale`.

### Keyboard Shortcuts

```html
<body {% nitro_key 'meta.k' "$dispatch('focus-search')" %}>
<div {% nitro_key 'escape' 'open = false' %}>
```

### Display Filters

```html
{{ amount|currency }}                  {# RD$ 15,000.00 #}
{{ amount|currency:'USD' }}            {# US$ 15,000.00 #}
{{ item.status|status_badge }}         {# colored badge #}
{{ ticket.priority|priority_badge }}   {# colored badge #}
{{ phone|phone_format }}               {# (809) 555-1234 #}
{{ date|relative_date }}               {# Hoy, Ayer, Hace 3 dias #}
{{ uuid|truncate_id:8 }}               {# first 8 chars #}
{{ 4.5|rating }}                       {# star rating SVG #}
{{ count|pluralize_es:'item,items' }}  {# Spanish pluralization #}
```

---

## Forms

```python
from nitro.forms import NitroModelForm, NitroForm, PhoneField, CedulaField, CurrencyField

class PropertyForm(NitroModelForm):
    class Meta:
        model = Property
        fields = ['name', 'address', 'rent_amount']
    # All widgets get Tailwind classes automatically

class ContactForm(NitroForm):
    phone = PhoneField()
    cedula = CedulaField()
    amount = CurrencyField()
```

---

## Components (Alpine.js)

Registered automatically via `alpine-components.js`:

- **`loadingBtn`** - Spinner on submit during HTMX requests
- **`fileUpload`** - Drag-and-drop file uploads
- **`clipboard`** - Copy to clipboard
- **`charCounter`** - Character counter for textareas
- **`confirmAction`** - Confirm dialog
- **`toggle`** - Collapsible sections
- **`tabs`** - Client-side tabs
- **`currencyInput`** - Auto-format currency
- **`phoneInput`** - Auto-format phone numbers
- **`dirtyForm`** - Unsaved changes warning

---

## Multi-Tenancy

```python
from nitro.mixins import OrganizationMixin

class CompanyMixin(OrganizationMixin):
    org_field = 'company'

    def get_organization(self):
        return self.request.user.company

# Use in views:
class PropertyListView(CompanyMixin, NitroListView):
    model = Property  # automatically filtered by company
```

---

## Utilities

### Currency

```python
from nitro.utils import format_currency, parse_currency

format_currency(1234.5)           # "RD$ 1,234.50"
format_currency(1234.5, 'USD')    # "US$ 1,234.50"
parse_currency('RD$ 1,234.50')    # Decimal('1234.50')
```

### Dates

```python
from nitro.utils import today, relative_date, month_name, is_overdue, add_months

relative_date(some_date)   # "Hoy", "Ayer", "Hace 3 dias"
month_name(1)              # "Enero"
is_overdue(due_date)       # True/False
add_months(date, 3)        # date + 3 months
```

---

## Configuration

```python
# settings.py (all optional)
NITRO = {
    'TOAST_ENABLED': True,
    'TOAST_POSITION': 'top-right',
    'TOAST_DURATION': 3000,
    'DEBUG': False,
}
```

---

## Migration from v0.7

v0.8.0 is a complete rewrite. The component-based architecture (NitroComponent, Pydantic state, Django Ninja API) has been replaced with standard Django views + HTMX.

### What changed

| v0.7 | v0.8 |
|------|------|
| `NitroComponent` classes | Django views (`NitroListView`, `NitroFormView`) |
| Pydantic `BaseModel` state | Django forms and template context |
| Django Ninja JSON API | Server-rendered HTML + HTMX swaps |
| `@register_component` | Standard Django URL routing |
| `call('action')` in templates | `hx-post`/`hx-get` HTMX attributes |
| `nitro_model` two-way binding | Alpine `x-model` (local) + form submit |
| `nitro_action` template tag | HTMX attributes via template tags |
| `requirements: pydantic, django-ninja` | `requirements: Django only` |

### Why the change

The component system added complexity (Pydantic state sync, JSON API, client-side rendering) that wasn't necessary for most Django apps. HTMX achieves the same reactive UX with standard Django patterns, is easier to debug, and has zero additional Python dependencies.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
