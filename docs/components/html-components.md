# HTML Components

Server-rendered components included via template tags.

## Toast Notifications

```html
{% load nitro_tags %}

<!-- Include once in base template -->
{% nitro_toast %}
{% nitro_toast position='bottom-right' %}
```

Positions: `top-right` (default), `top-left`, `bottom-right`, `bottom-left`, `top-center`, `bottom-center`

Toasts are triggered via HTMX response headers:

```python
# In view
return self.success('Guardado exitosamente')
return self.error('Error al guardar')
return self.toast('Mensaje', 'warning')
```

---

## Modal

```html
{% nitro_modal id='create-property' title='Nueva Propiedad' size='lg' %}
<form method="post" hx-post="{% url 'property_create' %}">
    {% csrf_token %}
    {% nitro_field form.name %}
    {% nitro_field form.address %}
    {% nitro_form_footer modal='create-property' %}
</form>
{% end_nitro_modal %}

<!-- Open button -->
<button {% nitro_open_modal 'create-property' %} class="btn btn-primary">
    Crear Propiedad
</button>
```

Sizes: `sm`, `md` (default), `lg`, `xl`, `full`

---

## Slideover

```html
{% nitro_slideover id='edit-tenant' title='Editar Inquilino' size='lg' side='right' %}
<form method="post" hx-post="{% url 'tenant_update' tenant.pk %}">
    {% csrf_token %}
    {% nitro_field form.name %}
    {% nitro_field form.email %}
    {% nitro_field form.phone %}
    {% nitro_form_footer slideover='edit-tenant' %}
</form>
{% end_nitro_slideover %}

<!-- Open button -->
<button {% nitro_open_slideover 'edit-tenant' %}>Editar</button>
```

Sizes: `sm`, `md`, `lg`, `xl`, `full`
Sides: `right` (default), `left`

---

## Tabs

```html
{% nitro_tabs id='property-tabs' target='#tab-content' %}
    {% nitro_tab name='info' label='Información' active=True %}
    {% nitro_tab name='leases' label='Contratos' url='/properties/1/leases/' %}
    {% nitro_tab name='photos' label='Fotos' badge=photo_count %}
{% end_nitro_tabs %}

<div id="tab-content">
    {% include "properties/partials/info.html" %}
</div>
```

Tab content loads via HTMX when URL is provided.

---

## Empty State

```html
{% nitro_empty_state
    icon="📭"
    title="Sin propiedades"
    message="Agrega tu primera propiedad para comenzar"
    action_url="/properties/create/"
    action_text="Crear Propiedad"
%}
```

| Parameter | Description |
|-----------|-------------|
| `icon` | Emoji or icon class |
| `title` | Main title |
| `message` | Description text |
| `action_url` | CTA button URL |
| `action_text` | CTA button text |

---

## Stats Card

```html
{% nitro_stats_card
    icon="💰"
    label="Ingresos del Mes"
    value=total_income|currency
    change="+12.5%"
    change_type="positive"
    href="/reports/income/"
%}
```

| Parameter | Description |
|-----------|-------------|
| `icon` | Emoji or icon |
| `label` | Card label |
| `value` | Main value |
| `change` | Change indicator |
| `change_type` | `positive`, `negative`, `neutral` |
| `href` | Optional link |

---

## Avatar

```html
{% nitro_avatar user %}
{% nitro_avatar user size='lg' %}
{% nitro_avatar user size='sm' show_name=True %}
{% nitro_avatar name='John Doe' %}
```

Sizes: `xs`, `sm`, `md` (default), `lg`, `xl`

Shows initials if no image available.

---

## Pagination

```html
{% nitro_pagination page_obj target='#list-content' %}
{% nitro_pagination page_obj target='#list' show_count=True scroll_top=True %}
```

| Parameter | Description |
|-----------|-------------|
| `page_obj` | Django Page object |
| `target` | HTMX target selector |
| `show_count` | Show "Mostrando X de Y" |
| `scroll_top` | Scroll to top on page change |

---

## Search Bar

```html
{% nitro_search target='#results' %}
{% nitro_search target='#results' placeholder='Buscar inquilinos...' debounce=500 %}
```

| Parameter | Description |
|-----------|-------------|
| `target` | HTMX target selector |
| `placeholder` | Input placeholder |
| `debounce` | Debounce ms (default: 300) |
| `name` | Input name (default: 'q') |

---

## Filter Select

```html
{% nitro_filter field='status' options=status_options target='#list' %}
{% nitro_filter field='type' options=type_options label='Tipo' include_all=False %}
```

| Parameter | Description |
|-----------|-------------|
| `field` | Filter field name |
| `options` | List of (value, label) tuples |
| `target` | HTMX target selector |
| `label` | Dropdown label |
| `include_all` | Include "Todos" option (default: True) |

---

## File Upload

```html
{% nitro_file_upload
    upload_url='/api/upload/'
    field_name='document'
    accept='.pdf,.doc,.docx'
    multiple=True
    max_size=10
    max_files=5
%}
```

| Parameter | Description |
|-----------|-------------|
| `upload_url` | Upload endpoint URL |
| `field_name` | Form field name |
| `accept` | Accepted file types |
| `multiple` | Allow multiple files |
| `max_size` | Max file size in MB |
| `max_files` | Max number of files |

---

## Confirm Dialog

```html
{% nitro_confirm
    id='delete-confirm'
    title='¿Eliminar propiedad?'
    message='Esta acción no se puede deshacer.'
    confirm_text='Eliminar'
    cancel_text='Cancelar'
    danger=True
%}
```

Triggered via Alpine event or button click.

---

## Table

```html
{% nitro_table table %}
```

Used with `NitroTable` class. See [Tables & Filters](../core-concepts/tables-filters.md).

---

## Form Field

```html
{% nitro_field form.name %}
{% nitro_field form.email type='email' %}
{% nitro_field form.bio rows=4 %}
```

Wraps field with label, input, and error messages.

---

## Form Footer

```html
{% nitro_form_footer modal='create-item' %}
{% nitro_form_footer slideover='edit-item' label='Guardar Cambios' %}
{% nitro_form_footer label='Enviar' cancel_url='/items/' %}
```

| Parameter | Description |
|-----------|-------------|
| `modal` | Modal ID to close on cancel |
| `slideover` | Slideover ID to close on cancel |
| `label` | Submit button label |
| `cancel_label` | Cancel button label |
| `cancel_url` | Cancel navigation URL |
