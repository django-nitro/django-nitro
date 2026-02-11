# Components Overview

Nitro includes two types of components:

1. **HTML Components** - Server-rendered templates included via template tags
2. **Alpine Components** - Client-side JavaScript components for local UI interactions

## Philosophy

- **Server renders HTML** - Django templates generate the markup
- **HTMX swaps it** - Server returns partial HTML on interactions
- **Alpine handles local UI** - Dropdowns, modals, tooltips (no data fetching)

## HTML Components

Located in `nitro/templates/nitro/components/`:

| Component | Description |
|-----------|-------------|
| `toast.html` | Toast notifications |
| `modal.html` | Modal dialogs |
| `slideover.html` | Slide-out panels |
| `tabs.html` | Tab navigation |
| `empty_state.html` | Empty state placeholder |
| `stats_card.html` | Statistics card |
| `avatar.html` | User avatar |
| `pagination.html` | Pagination controls |
| `search_bar.html` | Search input |
| `filter_select.html` | Filter dropdown |
| `file_upload.html` | File upload zone |
| `table.html` | Data table |
| `form_field.html` | Form field wrapper |
| `confirm.html` | Confirmation dialog |

### Usage

```html
{% load nitro_tags %}

{% nitro_toast %}
{% nitro_empty_state icon="📭" title="Sin datos" %}
{% nitro_stats_card icon="💰" label="Total" value="$1,000" %}
```

## Alpine Components

Registered in `alpine-components.js`:

| Component | Description |
|-----------|-------------|
| `toastManager()` | Manages toast queue |
| `fileUpload()` | Drag-and-drop uploads |
| `clipboard()` | Copy to clipboard |
| `searchableSelect()` | Select with search |
| `confirmAction()` | Confirmation modal |
| `charCounter()` | Character counter |
| `currencyInput()` | Currency formatting |
| `phoneInput()` | Phone formatting |
| `dirtyForm()` | Unsaved changes warning |
| `infiniteScroll()` | Load more on scroll |

### Usage

```html
<div x-data="fileUpload({ maxFiles: 5, maxSize: 10 })">
    ...
</div>

<input x-data="currencyInput()" x-model="formatted" />
```

## When to Use What

| Scenario | Solution |
|----------|----------|
| Show data from server | HTML component (template tag) |
| Toggle visibility | Alpine `x-show` |
| Form validation | HTML component + server validation |
| File upload preview | Alpine `fileUpload()` |
| Search with server | HTML + HTMX `hx-get` |
| Filter dropdown | HTML + HTMX |
| Copy text | Alpine `clipboard()` |
| Modal/slideover | HTML component + Alpine |

## Example: Search with Filter

```html
{% load nitro_tags %}

<!-- Server-rendered, HTMX-powered -->
<div class="flex gap-4">
    {% nitro_search target='#results' %}
    {% nitro_filter field='status' options=status_options target='#results' %}
</div>

<div id="results">
    {% include "partials/results.html" %}
</div>
```

## Example: Modal with Form

```html
{% load nitro_tags %}

<!-- Button to open -->
<button {% nitro_open_modal 'create-item' %}>
    Crear
</button>

<!-- Modal component -->
{% nitro_modal id='create-item' title='Nuevo Item' %}
<form hx-post="{% url 'item_create' %}" hx-target="#results">
    {% csrf_token %}
    {% nitro_field form.name %}
    {% nitro_field form.description %}
    {% nitro_form_footer modal='create-item' %}
</form>
{% end_nitro_modal %}
```

## Example: File Upload

```html
{% load nitro_tags %}

{% nitro_file_upload
    upload_url='/api/documents/upload/'
    field_name='file'
    accept='.pdf,.doc,.docx'
    multiple=True
    max_size=10
%}
```

This renders an Alpine-powered drag-and-drop zone that:

- Shows preview for images
- Validates file types and sizes
- Uploads via AJAX
- Shows progress bar
