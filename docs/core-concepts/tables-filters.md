# Tables & Filters

## NitroTable

Declarative table definition.

```python
from nitro.tables import NitroTable, Column, RowAction

class PropertyTable(NitroTable):
    name = Column(label='Nombre', sortable=True)
    address = Column(label='Dirección')
    rent_amount = Column(label='Renta', format='currency', sortable=True)
    status = Column(label='Estado', format='status_badge')
    created_at = Column(label='Creado', format='date', sortable=True)

    class Meta:
        model = Property
        row_actions = [
            RowAction('edit', 'Editar', icon='pencil'),
            RowAction('delete', 'Eliminar', icon='trash', confirm=True),
        ]
```

### Using in Views

```python
class PropertyListView(NitroListView):
    model = Property
    table_class = PropertyTable
    template_name = 'properties/list.html'
```

### Template

```html
{% load nitro_tags %}

{% nitro_table table %}
```

### Column Options

| Parameter | Description |
|-----------|-------------|
| `label` | Column header |
| `sortable` | Enable sorting |
| `format` | Display format: `currency`, `date`, `datetime`, `status_badge`, `boolean` |
| `accessor` | Custom accessor for nested attributes |
| `css_class` | CSS class for column |
| `visible` | Show/hide column |

### RowAction Options

| Parameter | Description |
|-----------|-------------|
| `name` | Action identifier |
| `label` | Display label |
| `icon` | Icon name |
| `url` | URL pattern (uses `{pk}` placeholder) |
| `confirm` | Show confirmation dialog |
| `method` | HTTP method (default: GET) |

---

## NitroFilterSet

Declarative filter definitions.

```python
from nitro.filters import NitroFilterSet, SearchFilter, SelectFilter, DateRangeFilter

class PropertyFilterSet(NitroFilterSet):
    search = SearchFilter(fields=['name', 'address'])
    status = SelectFilter(choices=[('active', 'Activo'), ('inactive', 'Inactivo')])
    property_type = SelectFilter(field='property_type')
    created = DateRangeFilter(field='created_at')

    class Meta:
        model = Property
```

### Using in Views

```python
class PropertyListView(NitroListView):
    model = Property
    filter_class = PropertyFilterSet
    template_name = 'properties/list.html'
```

### Filter Types

#### SearchFilter

Full-text search across multiple fields.

```python
search = SearchFilter(
    fields=['name', 'address', 'description'],
    placeholder='Buscar propiedades...'
)
```

#### SelectFilter

Dropdown selection.

```python
status = SelectFilter(
    field='status',
    choices=[('active', 'Activo'), ('inactive', 'Inactivo')],
    include_all=True,  # Add "Todos" option
    label='Estado'
)

# Dynamic choices from queryset
property_filter = SelectFilter(
    field='property',
    queryset=Property.objects.all(),
    label_field='name'
)
```

#### RangeFilter

Numeric range.

```python
rent = RangeFilter(
    field='rent_amount',
    min_label='Mínimo',
    max_label='Máximo'
)
```

#### DateRangeFilter

Date range selection.

```python
created = DateRangeFilter(
    field='created_at',
    presets=['today', 'week', 'month', 'year']
)
```

#### BooleanFilter

True/false selection.

```python
is_available = BooleanFilter(
    field='is_available',
    label='Disponible'
)
```

### Template Integration

```html
{% load nitro_tags %}

<div class="filters flex gap-4 mb-4">
    {% nitro_search filter_set.search target='#list' %}
    {% nitro_filter filter_set.status target='#list' %}
    {% nitro_filter filter_set.property_type target='#list' %}
</div>
```

### Custom Filters

```python
from nitro.filters import BaseFilter

class CustomFilter(BaseFilter):
    def filter(self, queryset, value):
        if not value:
            return queryset
        # Custom filtering logic
        return queryset.filter(custom_field__contains=value)
```
