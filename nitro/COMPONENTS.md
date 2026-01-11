# Nitro UI Components

Reusable UI patterns and template tags for building consistent Nitro applications.

## Installation

The components are automatically available when you have `nitro` in your Django project.

## Usage

Load the component tags in your template:

```django
{% load nitro_components %}
```

## Available Components

### 1. Toggle Button

A button that changes text based on a state variable (e.g., for showing/hiding panels).

```django
{% toggle_btn 'show_create_form' 'toggle_create_form' '+ Create Item' '✕ Cancel' 'w-full bg-blue-600 text-white py-3 rounded-xl' %}
```

**Parameters:**
- `state_var`: State variable name (e.g., `show_create_form`)
- `action_name`: Nitro action to call
- `open_text`: Text when panel is closed
- `close_text`: Text when panel is open
- `css_class`: Optional CSS classes (has sensible defaults)

### 2. Loading Button

Button with loading state indicator.

```django
<button {% nitro_action 'save_item' %} {% loading_btn 'Save' 'Saving...' 'bg-green-600 text-white py-3 px-4 rounded-xl' '💾' %}></button>
```

**Parameters:**
- `text`: Button text
- `loading_text`: Text during loading
- `css_class`: CSS classes
- `icon`: Optional emoji/icon

### 3. Panel Container

An expandable panel with Alpine.js transitions.

```django
{% panel_container 'show_create_form' 'bg-white rounded-lg shadow-sm p-4' %}
    <h2 class="font-bold mb-4">Create New Item</h2>
    <!-- Your form content -->
</div>
```

**Parameters:**
- `state_var`: State variable controlling visibility
- `css_class`: Optional CSS classes

### 4. Form Field

Consistent form field with label and styling.

```django
<div>
    <label class="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
    <input type="number"
           {% nitro_model 'create_buffer.amount' %}
           step="0.01"
           class="w-full rounded-lg border-gray-300 shadow-sm">
</div>
```

### 5. Card

Card container with optional title and colored border.

```django
{% card 'Payment Summary' 'Due: $500' '' 'border-green-500' %}
    <p>Content goes here</p>
</div>
```

**Parameters:**
- `title`: Card title
- `subtitle`: Card subtitle
- `css_class`: Additional CSS classes
- `border_color`: Left border color (e.g., `border-blue-500`)

### 6. Empty State

Empty state message with optional action button.

```django
{% empty_state '📦' 'No Items' 'Create your first item' '+ Create' 'toggle_create_form' %}
```

**Parameters:**
- `icon`: Emoji or icon
- `title`: Main message
- `message`: Detailed description
- `action_text`: Button text (optional)
- `action_call`: Nitro action (optional)

## 7. Searchable Dropdown

A dropdown with search/filter capabilities for selecting from many options.

```django
{% load nitro_components %}

{% searchable_dropdown
    'tenant_id'
    tenants
    label='Select Tenant'
    display_field='full_name'
    value_field='id'
    placeholder='Search tenants...'
    required=True
    help_text='Choose the tenant for this lease' %}
```

**Parameters:**
- `field_name`: Name for hidden input (e.g., `tenant_id`)
- `options`: List of objects or dicts
- `label`: Field label (optional)
- `display_field`: Field to display (default: `name`)
- `value_field`: Field to use as value (default: `id`)
- `placeholder`: Search placeholder (default: `Search...`)
- `required`: Whether field is required (default: `False`)
- `help_text`: Optional help text
- `current_value`: Pre-selected value (optional)
- `current_display`: Pre-selected display text (optional)
- `nitro_model`: Nitro model binding (optional)

**Features:**
- Live search/filter
- Click outside to close
- Clear selection button
- Keyboard navigation ready
- Works with Django models and dicts
- Mobile responsive

**With Nitro Model Binding:**

```django
{% searchable_dropdown
    'tenant'
    available_tenants
    label='Tenant'
    display_field='full_name'
    nitro_model='create_buffer.tenant_id' %}
```

## Slideover Component

True slide-out panel from the side of the screen.

### Usage

```django
<!-- In your component's state -->
show_slideover: bool = False

<!-- In your template -->
<button @click="call('toggle_slideover')">Open Panel</button>

<!-- Include the slideover -->
{% include 'nitro/components/slideover.html' with show_var='show_slideover' title='Edit Item' content=form_html %}
```

**Parameters:**
- `show_var`: State variable (default: `show`)
- `title`: Panel title
- `content`: HTML content (use `|safe` filter)
- `position`: `right` or `left` (default: `right`)
- `max_width`: Max width class (default: `max-w-md`)
- `footer`: Optional footer HTML

### Slideover with Block Content

```django
{% include 'nitro/components/slideover.html' with show_var='show_edit' title='Edit Property' %}
    {% block slideover_content %}
        <!-- Your form here -->
    {% endblock %}
{% endinclude %}
```

## Complete Example

Here's a before/after comparison:

### Before (Verbose)

```django
<button @click="call('toggle_create_form')"
        class="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg active:scale-95 transition-transform">
    <span x-show="!show_create_form">+ Create</span>
    <span x-show="show_create_form">✕ Cancel</span>
</button>

<div x-show="show_create_form" class="bg-white rounded-lg shadow-sm p-4" x-transition>
    <h2 class="font-bold text-gray-900 mb-4">New Item</h2>

    <div class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
            <input type="number"
                   {% nitro_model 'create_buffer.amount' %}
                   class="w-full rounded-lg border-gray-300 shadow-sm">
        </div>

        <button {% nitro_action 'create_item' %}
                :disabled="is_loading"
                class="flex-1 bg-green-600 text-white font-bold py-3 px-4 rounded-xl">
            <span x-show="!is_loading">💾 Save</span>
            <span x-show="is_loading">
                <span class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
                Saving...
            </span>
        </button>
    </div>
</div>
```

### After (Using Components)

```django
{% load nitro_components %}

{% toggle_btn 'show_create_form' 'toggle_create_form' '+ Create' '✕ Cancel' 'w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg active:scale-95 transition-transform' %}

{% panel_container 'show_create_form' %}
    <h2 class="font-bold text-gray-900 mb-4">New Item</h2>

    <div class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Amount *</label>
            <input type="number"
                   {% nitro_model 'create_buffer.amount' %}
                   class="w-full rounded-lg border-gray-300 shadow-sm">
        </div>

        <button {% nitro_action 'create_item' %} {% loading_btn 'Save' 'Saving...' 'flex-1 bg-green-600 text-white font-bold py-3 px-4 rounded-xl' '💾' %}></button>
    </div>
</div>
```

## Benefits

- **Less Boilerplate**: Reduce repetitive HTML by 40-60%
- **Consistency**: All components follow the same design patterns
- **Maintainability**: Update styles in one place
- **Readability**: Cleaner, more semantic templates
- **Type Safety**: Template tags are Python functions with proper validation

## Customization

All components accept custom CSS classes, so you can override defaults:

```django
{% toggle_btn 'show_form' 'toggle' 'Open' 'Close' 'custom-btn-class my-custom-style' %}
```

## Advanced: Creating Custom Component Tags

To add your own component tags, edit `/nitro/templatetags/nitro_components.py`:

```python
@register.simple_tag
def my_component(param1, param2='default'):
    html = f'<div class="custom">{param1}</div>'
    return mark_safe(html)
```

Then use in templates:

```django
{% load nitro_components %}
{% my_component 'value' %}
```
