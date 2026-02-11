# Django Nitro Examples

v0.8 examples coming soon. See the [README](../README.md) for a complete quick-start guide.

## Quick Start

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

See the full documentation in the [README](../README.md).
