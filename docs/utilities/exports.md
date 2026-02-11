# Export Utilities

Export data to CSV or Excel formats.

## ExportMixin

Add export functionality to any list view.

```python
from nitro.exports import ExportMixin
from nitro.views import NitroListView

class PropertyListView(ExportMixin, NitroListView):
    model = Property
    template_name = 'properties/list.html'

    export_fields = ['name', 'address', 'rent_amount', 'status', 'created_at']
    export_filename = 'propiedades'
```

### Template

```html
{% load nitro_tags %}

{% nitro_export_buttons %}
```

Renders CSV and Excel download buttons.

---

## Configuration

### export_fields

List of fields to include in export.

```python
export_fields = ['name', 'address', 'rent_amount', 'status']
```

### export_headers

Custom column headers.

```python
export_headers = {
    'name': 'Nombre',
    'address': 'Dirección',
    'rent_amount': 'Renta Mensual',
    'status': 'Estado',
}
```

### export_filename

Base filename (without extension).

```python
export_filename = 'propiedades'  # Results in propiedades.csv or propiedades.xlsx
```

### get_export_queryset

Customize the queryset for export.

```python
def get_export_queryset(self):
    """Export all records, not just current page."""
    return self.get_filtered_queryset()  # Respects search/filters
```

### format_export_value

Format values for export.

```python
def format_export_value(self, obj, field):
    value = getattr(obj, field)

    if field == 'rent_amount':
        return f"RD$ {value:,.2f}"
    if field == 'status':
        return dict(Property.STATUS_CHOICES).get(value, value)
    if field == 'created_at':
        return value.strftime('%d/%m/%Y')

    return value
```

---

## Direct Export Functions

```python
from nitro.exports import export_csv, export_excel

def export_payments_csv(request):
    payments = Payment.objects.filter(company=request.user.company)

    return export_csv(
        queryset=payments,
        fields=['date', 'amount', 'tenant__name', 'status'],
        headers={
            'date': 'Fecha',
            'amount': 'Monto',
            'tenant__name': 'Inquilino',
            'status': 'Estado',
        },
        filename='pagos'
    )

def export_payments_excel(request):
    payments = Payment.objects.filter(company=request.user.company)

    return export_excel(
        queryset=payments,
        fields=['date', 'amount', 'tenant__name', 'status'],
        headers={...},
        filename='pagos'
    )
```

---

## Nested Fields

Access related model fields using double underscore:

```python
export_fields = [
    'name',
    'property__name',      # Property name
    'tenant__name',        # Tenant name
    'tenant__email',       # Tenant email
]
```

---

## Custom Export View

For more control, create a dedicated export view:

```python
from django.http import HttpResponse
from nitro.exports import generate_csv, generate_excel

class PropertyExportView(CompanyMixin, View):
    def get(self, request, format='csv'):
        properties = Property.objects.filter(company=self.organization)

        data = []
        for prop in properties:
            data.append({
                'Nombre': prop.name,
                'Dirección': prop.address,
                'Renta': f"RD$ {prop.rent_amount:,.2f}",
                'Estado': prop.get_status_display(),
                'Inquilino': prop.current_tenant.name if prop.current_tenant else '-',
            })

        if format == 'excel':
            return generate_excel(data, 'propiedades')
        return generate_csv(data, 'propiedades')
```

---

## Template Tag

```html
{% load nitro_tags %}

<!-- Full export buttons -->
{% nitro_export_buttons %}

<!-- Individual buttons -->
{% nitro_export_button format='csv' label='Descargar CSV' %}
{% nitro_export_button format='excel' label='Descargar Excel' %}

<!-- With custom URL -->
{% nitro_export_button format='csv' url='/api/properties/export/' %}
```

---

## Security

Exports respect:

1. **Organization filtering** via CompanyMixin
2. **View permissions** - users can only export what they can view
3. **Field restrictions** - only specified fields are exported

```python
class SensitiveReportView(PermissionRequiredMixin, ExportMixin, NitroListView):
    permission_required = 'reports.export_sensitive'
    export_fields = ['name', 'status']  # Exclude sensitive fields
```
