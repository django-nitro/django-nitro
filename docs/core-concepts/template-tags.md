# Template Tags

Load with `{% load nitro_tags %}`.

## HTMX Action Tags

### nitro_search

Search input with debounce.

```html
{% nitro_search target='#list-content' %}
{% nitro_search target='#list-content' placeholder='Buscar...' debounce=500 %}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `target` | required | CSS selector to update |
| `placeholder` | "Buscar..." | Input placeholder |
| `debounce` | 300 | Debounce in ms |

### nitro_filter

Filter dropdown.

```html
{% nitro_filter field='status' options=filter_options.status target='#list-content' %}
{% nitro_filter field='status' options=opts label='Estado' include_all=True %}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `field` | required | Filter field name |
| `options` | required | List of (value, label) tuples |
| `target` | "#list-content" | CSS selector to update |
| `label` | None | Dropdown label |
| `include_all` | True | Include "Todos" option |

### nitro_pagination

Pagination controls.

```html
{% nitro_pagination page_obj target='#list-content' %}
{% nitro_pagination page_obj target='#list' show_count=True %}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `page_obj` | required | Django Page object |
| `target` | "#list-content" | CSS selector to update |
| `show_count` | False | Show "Mostrando X de Y" |

### nitro_sort

Sortable column header.

```html
{% nitro_sort 'name' 'Nombre' target='#list-content' %}
{% nitro_sort 'created_at' 'Fecha' target='#list' current=current_sort %}
```

### nitro_delete

Delete button/link attributes.

```html
<button {% nitro_delete url=delete_url target='#list' confirm='¿Eliminar?' %}>
    Eliminar
</button>
```

---

## Form Tags

### nitro_field

Styled form field with label and errors.

```html
{% nitro_field form.name %}
{% nitro_field form.email placeholder='correo@ejemplo.com' %}
{% nitro_field form.amount class='w-full' %}
```

### nitro_select

Searchable select dropdown.

```html
{% nitro_select form.category %}
{% nitro_select form.property search_url='/api/properties/search/' %}
```

### nitro_form_footer

Form submit buttons for slideover/modal.

```html
{% nitro_form_footer slideover='create-property' %}
{% nitro_form_footer modal='edit-tenant' label='Guardar' cancel_label='Cancelar' %}
```

---

## Component Tags

### nitro_modal

Modal dialog.

```html
{% nitro_modal id='create-property' title='Nueva Propiedad' %}
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        {% nitro_form_footer modal='create-property' %}
    </form>
{% end_nitro_modal %}

<!-- Open button -->
<button {% nitro_open_modal 'create-property' %}>Crear</button>
```

### nitro_slideover

Slide-out panel.

```html
{% nitro_slideover id='edit-tenant' title='Editar' size='lg' %}
    ...content...
{% end_nitro_slideover %}

<!-- Open button -->
<button {% nitro_open_slideover 'edit-tenant' %}>Editar</button>
```

Sizes: `sm`, `md`, `lg`, `xl`, `full`

### nitro_tabs

Tab navigation.

```html
{% nitro_tabs id='property-tabs' target='#tab-content' %}
    {% nitro_tab name='info' label='Información' active=True %}
    {% nitro_tab name='leases' label='Contratos' %}
    {% nitro_tab name='photos' label='Fotos' badge=photo_count %}
{% end_nitro_tabs %}

<div id="tab-content">
    {% include "properties/partials/info_tab.html" %}
</div>
```

### nitro_empty_state

Empty state placeholder.

```html
{% nitro_empty_state
    icon="📭"
    title="Sin resultados"
    message="No se encontraron propiedades"
    action_url="/properties/create/"
    action_text="Crear propiedad"
%}
```

### nitro_stats_card

Statistics card.

```html
{% nitro_stats_card
    icon="💰"
    label="Ingresos"
    value=total_income|currency
    change="+12%"
    change_type="positive"
%}
```

### nitro_avatar

User avatar.

```html
{% nitro_avatar user %}
{% nitro_avatar user size='lg' %}
{% nitro_avatar user size='sm' show_name=True %}
```

Sizes: `xs`, `sm`, `md`, `lg`, `xl`

### nitro_file_upload

File upload with drag-and-drop.

```html
{% nitro_file_upload
    upload_url='/api/upload/'
    field_name='document'
    accept='.pdf,.doc,.docx'
    multiple=True
    max_size=10
%}
```

### nitro_toast

Toast container (include once in base template).

```html
{% nitro_toast %}
{% nitro_toast position='bottom-right' %}
```

---

## Display Filters

### Currency

```html
{{ amount|currency }}           {# RD$ 15,000.00 #}
{{ amount|currency:'USD' }}     {# US$ 15,000.00 #}
```

### Status Badges

```html
{{ item.status|status_badge }}      {# Colored badge #}
{{ ticket.priority|priority_badge }} {# Priority badge #}
```

### Formatting

```html
{{ phone|phone_format }}        {# (809) 555-1234 #}
{{ date|relative_date }}        {# Hoy, Ayer, Hace 3 días #}
{{ uuid|truncate_id:8 }}        {# First 8 chars #}
{{ 4.5|rating }}                {# Star rating SVG #}
{{ count|pluralize_es:'item,items' }}
```

### WhatsApp

```html
{{ phone|whatsapp_link }}
{{ phone|whatsapp_link:'Hola!' }}
<a href="{{ phone|whatsapp_link:'Hola' }}">WhatsApp</a>
```

---

## UI Helpers

### Transitions

```html
<div x-show="open" {% nitro_transition 'fade' %}>...</div>
<div x-show="open" {% nitro_transition 'slide-up' '200' %}>...</div>
```

Presets: `fade`, `slide-up`, `slide-down`, `slide-left`, `slide-right`, `scale`

### Keyboard Shortcuts

```html
<body {% nitro_key 'meta.k' "$dispatch('focus-search')" %}>
<div {% nitro_key 'escape' 'open = false' %}>
```

### Scripts

```html
{% nitro_scripts %}  {# Include HTMX + Nitro JS #}
```
