# Quick Start

Build a property list with search, filters, and pagination in 5 minutes.

## 1. Create the View

```python
# views.py
from nitro.views import NitroListView

class PropertyListView(NitroListView):
    model = Property
    template_name = 'properties/list.html'
    partial_template = 'properties/partials/list_content.html'
    search_fields = ['name', 'address']
    filter_fields = ['status', 'property_type']
    sortable_fields = ['name', 'rent_amount', 'created_at']
    paginate_by = 20
    default_sort = '-created_at'

    def get_filter_options(self):
        return {
            'status': [('active', 'Activo'), ('inactive', 'Inactivo')],
            'property_type': [('house', 'Casa'), ('apartment', 'Apartamento')],
        }
```

## 2. Create the Main Template

```html
<!-- templates/properties/list.html -->
{% extends "base.html" %}
{% load nitro_tags %}

{% block content %}
<div class="p-6">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold">Propiedades</h1>
        <a href="{% url 'property_create' %}" class="btn btn-primary">
            + Nueva Propiedad
        </a>
    </div>

    <div class="flex gap-4 mb-4">
        {% nitro_search target='#property-list' placeholder='Buscar...' %}
        {% nitro_filter field='status' options=filter_options.status target='#property-list' %}
        {% nitro_filter field='property_type' options=filter_options.property_type target='#property-list' %}
    </div>

    <div id="property-list">
        {% include "properties/partials/list_content.html" %}
    </div>
</div>
{% endblock %}
```

## 3. Create the Partial Template

```html
<!-- templates/properties/partials/list_content.html -->
{% load nitro_tags %}

{% if object_list %}
<div class="grid gap-4">
    {% for property in object_list %}
    <div class="bg-white rounded-lg shadow p-4">
        <div class="flex justify-between">
            <div>
                <h3 class="font-semibold">{{ property.name }}</h3>
                <p class="text-gray-600">{{ property.address }}</p>
            </div>
            <div class="text-right">
                <p class="font-bold">{{ property.rent_amount|currency }}</p>
                {{ property.status|status_badge }}
            </div>
        </div>
    </div>
    {% endfor %}
</div>

{% nitro_pagination page_obj target='#property-list' %}

{% else %}
{% nitro_empty_state
    icon="🏠"
    title="Sin propiedades"
    message="Agrega tu primera propiedad"
    action_url="/properties/create/"
    action_text="Crear propiedad"
%}
{% endif %}
```

## 4. Wire the URL

```python
# urls.py
from django.urls import path
from .views import PropertyListView

urlpatterns = [
    path('properties/', PropertyListView.as_view(), name='property_list'),
]
```

## How It Works

1. **Initial load**: Django renders the full page with `list.html`
2. **Search/Filter**: HTMX sends GET request, Django returns only `list_content.html`
3. **Pagination**: Same pattern - HTMX swaps just the list content

No JavaScript written. Search has 300ms debounce. Filters update immediately. Pagination preserves search/filter state.

## Next Steps

- [Views Reference](../core-concepts/views.md) - All view classes
- [Template Tags](../core-concepts/template-tags.md) - All template tags
- [Multi-Tenancy](../core-concepts/multi-tenancy.md) - Add organization scoping
