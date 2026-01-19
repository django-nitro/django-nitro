# nitro/templatetags/nitro_tags.py
from django import template
from django.conf import settings
from django.template.base import Node, TemplateSyntaxError
from django.templatetags.static import static
from django.utils.safestring import mark_safe

from nitro.registry import get_component_class
from nitro.utils import build_error_path, build_safe_field

register = template.Library()

# Debug mode flag
NITRO_DEBUG = getattr(settings, "DEBUG", False) and getattr(settings, "NITRO", {}).get(
    "DEBUG", False
)


@register.simple_tag(takes_context=True)
def nitro_component(context, component_name, **kwargs):
    """
    Render a Nitro component.

    Usage:
        {% nitro_component 'Counter' initial=5 %}
        {% nitro_component 'PropertyList' %}
    """
    ComponentClass = get_component_class(component_name)
    if not ComponentClass:
        return ""

    # Extract request from context
    request = context.get("request")

    # Instantiate and render
    instance = ComponentClass(request=request, **kwargs)
    return instance.render()


@register.simple_tag
def nitro_scripts():
    """
    Include Nitro CSS and JS files.

    Usage:
        {% load nitro_tags %}
        <head>
            {% nitro_scripts %}
        </head>

    This will include:
    - nitro.css (toast styles and component utilities)
    - nitro.js (Alpine.js integration and client-side logic)
    """
    css_path = static("nitro/nitro.css")
    js_path = static("nitro/nitro.js")
    # Cache buster based on version
    version = "0.7.0"

    return mark_safe(
        f'<link rel="stylesheet" href="{css_path}?v={version}">\n<script defer src="{js_path}?v={version}"></script>'
    )


class NitroForNode(Node):
    """
    Node for {% nitro_for %} template tag.

    Hybrid rendering: Static content for SEO + Alpine.js x-for for reactivity.
    """

    def __init__(self, list_var, item_var, nodelist):
        self.list_var = template.Variable(list_var)
        self.item_var = item_var
        self.nodelist = nodelist

    def render(self, context):
        # Get the list from context
        try:
            items = self.list_var.resolve(context)
        except template.VariableDoesNotExist:
            items = []

        output = []
        list_var_name = self.list_var.var

        # 1. Static content for SEO (hidden with CSS, not Alpine x-show)
        # Using CSS instead of x-show prevents Alpine.js dataStack initialization errors
        # IMPORTANT: x-ignore tells Alpine to skip processing this element entirely,
        # preventing "variable not defined" errors from x-text bindings inside
        output.append('<div class="nitro-seo-content" style="display: none;" x-ignore>')
        for item in items:
            context.push({self.item_var: item})
            output.append(self.nodelist.render(context))
            context.pop()
        output.append("</div>")

        # 2. Alpine.js template for reactivity
        output.append(
            f'<template x-for="({self.item_var}, index) in {list_var_name}" '
            f':key="{self.item_var}.id || index">'
        )

        # Render template content with Alpine bindings
        # Use first item as example for rendering structure
        if items:
            context.push({self.item_var: items[0]})
            output.append(self.nodelist.render(context))
            context.pop()

        output.append("</template>")

        return "".join(output)


@register.tag
def nitro_for(parser, token):
    """
    SEO-friendly x-for loop.

    Renders static content on server (SEO) + Alpine.js x-for for reactivity.

    Usage:
        {% nitro_for 'items' as 'item' %}
            <div class="card">
                <h3>{% nitro_text 'item.name' %}</h3>
                <p>{% nitro_text 'item.email' %}</p>
            </div>
        {% end_nitro_for %}

    Args:
        list_var: Name of the list variable (string)
        item_var: Name for each item (string)

    Example:
        In component state: items = [{"id": 1, "name": "John"}, ...]

        Template:
        {% nitro_for 'items' as 'item' %}
            <div class="card">
                <h3>{% nitro_text 'item.name' %}</h3>
                <p>{% nitro_text 'item.email' %}</p>
            </div>
        {% end_nitro_for %}

        Results in:
        - Server renders static HTML with actual values (SEO)
        - Wraps in <template x-for> (Alpine reactivity)
        - Each element has x-text bindings for updates
    """
    try:
        # Parse: {% nitro_for 'list_var' as 'item_var' %}
        bits = token.split_contents()
        if len(bits) != 4 or bits[2] != "as":
            raise TemplateSyntaxError(
                f"{bits[0]} tag requires format: {{% nitro_for 'list_var' as 'item_var' %}}"
            )

        tag_name, list_var, as_word, item_var = bits

        # Remove quotes from variables
        list_var = list_var.strip("'\"")
        item_var = item_var.strip("'\"")

    except ValueError:
        raise TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires format: "
            "{% nitro_for 'list_var' as 'item_var' %}"
        ) from None

    # Parse until {% end_nitro_for %}
    nodelist = parser.parse(("end_nitro_for",))
    parser.delete_first_token()

    return NitroForNode(list_var, item_var, nodelist)


@register.simple_tag
def nitro_text(field):
    """
    x-text binding as an attribute.

    Use inside any element to bind text content.

    Usage:
        <span {% nitro_text 'item.name' %}></span>
        <span {% nitro_text 'item.name' %} class="truncate"></span>
        <div {% nitro_text 'count' %} class="text-lg font-bold"></div>

    Args:
        field: Field path or expression to display

    Returns:
        x-text="field" attribute
    """
    return mark_safe(f'x-text="{field}"')


# ============================================================================
# ZERO JAVASCRIPT MODE - Wire-like Template Tags (v0.4.0)
# ============================================================================


@register.simple_tag
def nitro_model(field, debounce="200ms", lazy=False, on_change=None, no_debounce=False):
    """
    Auto-sync bidirectional binding (wire:model equivalent).

    Hides Alpine syntax for "Zero JavaScript" mode.

    NOW WITH DEFAULT DEBOUNCE: 200ms debounce is applied by default to reduce
    server load. This prevents a server request on every keystroke.

    Usage:
        {% nitro_model 'email' %}  <!-- 200ms debounce by default -->
        {% nitro_model 'search' debounce='500ms' %}  <!-- Custom debounce -->
        {% nitro_model 'password' lazy=True %}  <!-- Sync on blur only -->
        {% nitro_model 'email' on_change='validate_email' %}
        {% nitro_model 'counter' no_debounce=True %}  <!-- Instant sync, no debounce -->

    Args:
        field: Field name from state (e.g., 'email', 'search')
        debounce: Debounce time (default: '200ms', e.g., '300ms', '1s')
        lazy: If True, sync on blur instead of input
        on_change: Optional action to call after sync
        no_debounce: If True, disable debouncing entirely (instant sync)

    Returns:
        HTML attributes string with Alpine bindings

    Example:
        <input {% nitro_model 'email' debounce='300ms' %}>

        Expands to:
        <input
            x-model="email"
            @input.debounce.300ms="call('_sync_field', {field: 'email', value: email})"
        >
    """
    # Handle no_debounce flag
    if no_debounce:
        debounce = None

    # Build debug info
    debug_parts = [f"field='{field}'"]
    if debounce:
        debug_parts.append(f"debounce={debounce}")
    if lazy:
        debug_parts.append("lazy=True")
    if on_change:
        debug_parts.append(f"on_change='{on_change}'")

    attrs = []

    # Debug comment (before)
    if NITRO_DEBUG:
        attrs.append(f'data-nitro-debug="nitro_model: {", ".join(debug_parts)}"')

    # Two-way binding
    attrs.append(f'x-model="{field}"')

    # Determine event
    event = "@blur" if lazy else "@input"
    if debounce:
        event += f".debounce.{debounce}"

    # Auto-sync call (silent mode to prevent loading flash during typing)
    # Also track changes for dirty state
    sync_call = f"trackChange('{field}'); call('_sync_field', {{field: '{field}', value: {field}}}, null, {{silent: true}})"

    # Add optional on_change callback
    if on_change:
        sync_call += f"; call('{on_change}')"

    attrs.append(f'{event}="{sync_call}"')

    # Add error styling - use optional chaining for nested fields
    error_path = build_error_path(field)
    attrs.append(f":class=\"{{'border-red-500': {error_path}}}\"")

    return mark_safe(" ".join(attrs))


@register.simple_tag
def nitro_action(action, on_success=None, confirm=None, stop=False, prevent=False, **kwargs):
    """
    Action button (wire:click equivalent).

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        {% nitro_action 'submit' %}
        {% nitro_action 'delete' id='item.id' %}
        {% nitro_action 'update' id='task.id' status='completed' %}
        {% nitro_action 'create_item' on_success='showCreate = false' %}
        {% nitro_action 'delete' id='item.id' confirm='¿Eliminar?' %}
        {% nitro_action 'start_edit' id='item.id' stop=True %}

    Args:
        action: Action method name
        on_success: JavaScript code to run after successful action (optional)
        confirm: Confirmation message before executing (optional)
        stop: Add .stop modifier to prevent event propagation (optional)
        prevent: Add .prevent modifier to prevent default behavior (optional)
        **kwargs: Parameters to pass to the action

    Returns:
        HTML attributes string with Alpine bindings

    Example:
        <button {% nitro_action 'delete' id='item.id' %}>Delete</button>

        Expands to:
        <button
            @click="call('delete', {id: item.id})"
            :disabled="isLoading"
        >Delete</button>

        With on_success:
        <button {% nitro_action 'create_item' on_success='showModal = false' %}>

        Expands to:
        <button
            @click="call('create_item').then(() => { showModal = false })"
            :disabled="isLoading"
        >
    """
    attrs = []

    # Debug info
    if NITRO_DEBUG:
        debug_info = f"nitro_action: action='{action}'"
        if kwargs:
            params_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            debug_info += f", params=({params_str})"
        if on_success:
            debug_info += f", on_success='{on_success}'"
        attrs.append(f'data-nitro-debug="{debug_info}"')

    # Build params object
    if kwargs:
        params = "{" + ", ".join(f"{k}: {v}" for k, v in kwargs.items()) + "}"
        call_expr = f"call('{action}', {params})"
    else:
        call_expr = f"call('{action}')"

    # Add .then() for on_success
    if on_success:
        call_expr = f"{call_expr}.then(() => {{ {on_success} }})"

    # Wrap with confirm if specified
    if confirm:
        click_handler = f"if(confirm('{confirm}')) {{ {call_expr} }}"
    else:
        click_handler = call_expr

    # Build event directive with modifiers
    event_directive = "@click"
    if stop:
        event_directive += ".stop"
    if prevent:
        event_directive += ".prevent"

    attrs.append(f'{event_directive}="{click_handler}"')

    # Auto-disable during loading
    attrs.append(':disabled="isLoading"')

    return mark_safe(" ".join(attrs))


@register.simple_tag
def nitro_show(condition):
    """
    Conditional visibility (x-show wrapper).

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        <div {% nitro_show 'isLoading' %}>Loading...</div>
        <div {% nitro_show '!isLoading' %}>Content</div>
        <div {% nitro_show 'count > 0' %}>Has items</div>

    Args:
        condition: JavaScript expression to evaluate

    Returns:
        HTML attribute string with x-show binding

    Example:
        <div {% nitro_show 'errors.email' %}>
            Error message
        </div>
    """
    return mark_safe(f'x-show="{condition}"')


@register.simple_tag
def nitro_class(**conditions):
    """
    Conditional CSS classes (:class wrapper).

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        <div {% nitro_class active='isActive' disabled='isLoading' %}>
        <div {% nitro_class 'border-red-500'='errors.email' %}>

    Args:
        **conditions: Dict of class_name=condition pairs

    Returns:
        HTML attribute string with :class binding

    Example:
        <div {% nitro_class active='isActive' error='hasError' %}>

        Expands to:
        <div :class="{'active': isActive, 'error': hasError}">
    """
    if not conditions:
        return ""

    class_obj = "{" + ", ".join(f"'{k}': {v}" for k, v in conditions.items()) + "}"
    return mark_safe(f':class="{class_obj}"')


@register.simple_tag
def nitro_class_map(class_map):
    """
    Conditional CSS classes using a JSON-like mapping string.

    Use this for complex Tailwind class names with spaces and dashes that
    can't be used as Python kwargs.

    Usage:
        {% nitro_class_map "{'bg-green-100 text-green-700': item.status === 'active', 'bg-red-100 text-red-700': item.status === 'expired'}" %}

    Args:
        class_map: A JSON-like object string with class names as keys and conditions as values

    Returns:
        HTML attribute string with :class binding

    Example:
        <span {% nitro_class_map "{'bg-green-100 text-green-700 border border-green-300': item.status === 'active', 'bg-gray-200 text-gray-700': item.status === 'draft'}" %}>

        Expands to:
        <span :class="{'bg-green-100 text-green-700 border border-green-300': item.status === 'active', 'bg-gray-200 text-gray-700': item.status === 'draft'}">
    """
    if not class_map:
        return ""

    # The class_map should already be a valid JS object string
    return mark_safe(f':class="{class_map}"')


@register.simple_tag
def nitro_bind(expression):
    """
    Bind text to an element using x-text (attribute-only version of nitro_text).

    Use this when you already have an element and just need to bind text,
    especially for ternary operators, template strings, or complex expressions.

    Usage:
        <span {% nitro_bind 'item.name' %}></span>
        <span {% nitro_bind "item.status === 'active' ? 'Activo' : 'Inactivo'" %}></span>
        <div {% nitro_bind "`Total: ${count} items`" %}></div>

    Args:
        expression: JavaScript expression to evaluate and display

    Returns:
        HTML attribute: x-text="expression"

    Example:
        <span class="status" {% nitro_bind "item.active ? 'Activo' : 'Inactivo'" %}></span>

        Expands to:
        <span class="status" x-text="item.active ? 'Activo' : 'Inactivo'"></span>

    Note:
        - Use {% nitro_text 'field' %} to render a <span> with initial value (SEO-friendly)
        - Use {% nitro_bind 'expression' %} for attribute-only binding on existing elements
    """
    return mark_safe(f'x-text="{expression}"')


# ============================================================================
# ADVANCED ZERO JAVASCRIPT MODE - Template Tags (v0.5.0)
# ============================================================================


@register.simple_tag
def nitro_attr(attr_name, value):
    """
    Dynamic attribute binding (:attr wrapper).

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        <img {% nitro_attr 'src' 'product.image_url' %}>
        <a {% nitro_attr 'href' 'item.link' %}>
        <input {% nitro_attr 'placeholder' 'form.placeholder_text' %}>

    Args:
        attr_name: Attribute name (e.g., 'src', 'href', 'placeholder')
        value: JavaScript expression to bind

    Returns:
        HTML attribute string with :attr binding

    Example:
        <img {% nitro_attr 'src' 'product.image_url' %} alt="Product">

        Expands to:
        <img :src="product.image_url" alt="Product">
    """
    attrs = []

    if NITRO_DEBUG:
        attrs.append(f'data-nitro-debug="nitro_attr: {attr_name}={value}"')

    attrs.append(f':{attr_name}="{value}"')

    return mark_safe(" ".join(attrs))


@register.simple_tag
def nitro_toggle(field, stop=False, action=None, **kwargs):
    """
    Client-side toggle - Zero JS mode.

    Toggles a boolean value. Optionally also calls a server action.

    Usage:
        <button {% nitro_toggle 'showModal' %}>Toggle Modal</button>
        <button {% nitro_toggle 'isExpanded' stop=True %}>Expand</button>
        <button {% nitro_toggle 'show_form' action='toggle_form' %}>Toggle with server sync</button>

    Args:
        field: Boolean field to toggle
        stop: Stop event propagation
        action: Optional server action to call after toggle
        **kwargs: Parameters to pass to the action

    Example:
        <button {% nitro_toggle 'showCreateForm' %}>
            <span x-show="!showCreateForm">+ Nuevo</span>
            <span x-show="showCreateForm">Cancelar</span>
        </button>

        Expands to:
        <button @click="showCreateForm = !showCreateForm">...</button>

        With action:
        <button {% nitro_toggle 'show_form' action='toggle_form' %}>

        Expands to:
        <button @click="show_form = !show_form; call('toggle_form')">
    """
    attrs = []

    if NITRO_DEBUG:
        debug_info = f"nitro_toggle: field='{field}'"
        if action:
            debug_info += f", action='{action}'"
        attrs.append(f'data-nitro-debug="{debug_info}"')

    event = "@click"
    if stop:
        event += ".stop"

    # Build the click handler
    toggle_expr = f"{field} = !{field}"

    if action:
        # Also call server action
        if kwargs:
            params = "{" + ", ".join(f"{k}: {v}" for k, v in kwargs.items()) + "}"
            call_expr = f"call('{action}', {params})"
        else:
            call_expr = f"call('{action}')"
        attrs.append(f'{event}="{toggle_expr}; {call_expr}"')
    else:
        attrs.append(f'{event}="{toggle_expr}"')

    return mark_safe(" ".join(attrs))


@register.simple_tag
def nitro_set(field, value, stop=False):
    """
    Client-side set value - Zero JS mode.

    Sets a field to a specific value WITHOUT server round-trip.
    Use this for purely client-side UI state (tabs, selections, etc.)

    Usage:
        <button {% nitro_set 'activeTab' value="'settings'" %}>Settings</button>
        <button {% nitro_set 'selectedId' value='item.id' stop=True %}>Select</button>
        <button {% nitro_set 'count' value='count + 1' %}>+1</button>

    Args:
        field: Field to set
        value: Value to assign (can be a literal or expression)
        stop: Stop event propagation

    Example:
        <!-- Tabs -->
        <button {% nitro_set 'activeTab' value="'general'" %}>General</button>
        <button {% nitro_set 'activeTab' value="'settings'" %}>Settings</button>

        <!-- Counter -->
        <button {% nitro_set 'count' value='count + 1' %}>+1</button>
        <button {% nitro_set 'count' value='0' %}>Reset</button>

        Expands to:
        <button @click="activeTab = 'general'">General</button>
        <button @click="count = count + 1">+1</button>

    Note:
        This is a CLIENT-SIDE ONLY operation. No server round-trip.
        For server-side state changes, use {% nitro_action %} instead.
    """
    attrs = []

    if NITRO_DEBUG:
        attrs.append(f'data-nitro-debug="nitro_set: field=\'{field}\' value=\'{value}\'"')

    event = "@click"
    if stop:
        event += ".stop"

    attrs.append(f'{event}="{field} = {value}"')

    return mark_safe(" ".join(attrs))


@register.simple_tag
def nitro_key(key, action, prevent=False, stop=False, window=False, **kwargs):
    """
    Keyboard event handler - Zero JS mode.

    Triggers a server action when a specific key is pressed.

    Usage:
        <input {% nitro_model 'search' %} {% nitro_key 'enter' action='do_search' %}>
        <div {% nitro_key 'escape' action='close_modal' window=True %}>
        <input {% nitro_key 'ctrl+s' action='save' prevent=True %}>

    Args:
        key: Key name (enter, escape, space, tab, etc.) or combo (ctrl+s, shift+enter)
        action: Server action to call when key is pressed
        prevent: Prevent default browser behavior (e.g., form submit on enter)
        stop: Stop event propagation
        window: Listen on window instead of element (for global shortcuts)
        **kwargs: Parameters to pass to the action

    Supported keys:
        - enter, escape, space, tab, delete, backspace
        - up, down, left, right (arrow keys)
        - Modifiers: ctrl+, alt+, shift+, meta+ (e.g., ctrl+s, shift+enter)

    Example:
        <input {% nitro_model 'search' %} {% nitro_key 'enter' action='search' %}>

        Expands to:
        <input ... @keydown.enter="call('search')">

        With params:
        <button {% nitro_key 'ctrl+s' action='save' prevent=True id='item.id' %}>

        Expands to:
        <button ... @keydown.ctrl.s.prevent="call('save', {id: item.id})">
    """
    attrs = []

    # Debug info
    if NITRO_DEBUG:
        debug_parts = [f"key='{key}'", f"action='{action}'"]
        if prevent:
            debug_parts.append("prevent=True")
        if stop:
            debug_parts.append("stop=True")
        if window:
            debug_parts.append("window=True")
        if kwargs:
            debug_parts.append(f"params={kwargs}")
        attrs.append(f'data-nitro-debug="nitro_key: {", ".join(debug_parts)}"')

    # Parse key combo (e.g., "ctrl+s" -> ["ctrl", "s"])
    key_parts = key.lower().replace("+", ".").split(".")

    # Build event directive
    event = "@keydown"
    for part in key_parts:
        event += f".{part}"

    # Add modifiers
    if prevent:
        event += ".prevent"
    if stop:
        event += ".stop"
    if window:
        event += ".window"

    # Build action call
    if kwargs:
        params = "{" + ", ".join(f"{k}: {v}" for k, v in kwargs.items()) + "}"
        call_expr = f"call('{action}', {params})"
    else:
        call_expr = f"call('{action}')"

    attrs.append(f'{event}="{call_expr}"')

    return mark_safe(" ".join(attrs))


@register.simple_tag
def nitro_disabled(condition):
    """
    Dynamic disabled state (:disabled wrapper).

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        <button {% nitro_disabled 'isProcessing' %}>Submit</button>
        <button {% nitro_disabled 'isProcessing || !isValid' %}>Submit</button>
        <input {% nitro_disabled 'form.locked' %}>

    Args:
        condition: JavaScript expression to evaluate

    Returns:
        HTML attribute string with :disabled binding

    Example:
        <button {% nitro_disabled 'isProcessing || !isValid' %}>
            Submit
        </button>

        Expands to:
        <button :disabled="isProcessing || !isValid">
            Submit
        </button>
    """
    attrs = []

    if NITRO_DEBUG:
        attrs.append(f'data-nitro-debug="nitro_disabled: {condition}"')

    attrs.append(f':disabled="{condition}"')

    return mark_safe(" ".join(attrs))


# Transition presets - common animation patterns
TRANSITION_PRESETS = {
    'fade': {
        'enter': 'ease-out duration-300',
        'enter-start': 'opacity-0',
        'enter-end': 'opacity-100',
        'leave': 'ease-in duration-200',
        'leave-start': 'opacity-100',
        'leave-end': 'opacity-0',
    },
    'slide-right': {
        'enter': 'transform transition ease-out duration-300',
        'enter-start': 'translate-x-full',
        'enter-end': 'translate-x-0',
        'leave': 'transform transition ease-in duration-200',
        'leave-start': 'translate-x-0',
        'leave-end': 'translate-x-full',
    },
    'slide-left': {
        'enter': 'transform transition ease-out duration-300',
        'enter-start': '-translate-x-full',
        'enter-end': 'translate-x-0',
        'leave': 'transform transition ease-in duration-200',
        'leave-start': 'translate-x-0',
        'leave-end': '-translate-x-full',
    },
    'slide-up': {
        'enter': 'transform transition ease-out duration-300',
        'enter-start': 'translate-y-full',
        'enter-end': 'translate-y-0',
        'leave': 'transform transition ease-in duration-200',
        'leave-start': 'translate-y-0',
        'leave-end': 'translate-y-full',
    },
    'slide-down': {
        'enter': 'transform transition ease-out duration-300',
        'enter-start': '-translate-y-full',
        'enter-end': 'translate-y-0',
        'leave': 'transform transition ease-in duration-200',
        'leave-start': 'translate-y-0',
        'leave-end': '-translate-y-full',
    },
    'scale': {
        'enter': 'ease-out duration-300',
        'enter-start': 'opacity-0 transform scale-95',
        'enter-end': 'opacity-100 transform scale-100',
        'leave': 'ease-in duration-200',
        'leave-start': 'opacity-100 transform scale-100',
        'leave-end': 'opacity-0 transform scale-95',
    },
    'none': {},
}


@register.simple_tag
def nitro_file_action(action, **kwargs):
    """
    File input that triggers a Nitro action on file selection.

    Usage:
        <input type="file" {% nitro_file_action 'upload_document' %}>

    The action will receive the file as the third parameter to call().
    The component method should access it via self.request.FILES.get('file').

    Args:
        action: The component method to call
        **kwargs: Additional parameters to pass to the action

    Example:
        <input type="file" {% nitro_file_action 'upload_avatar' %}>

        Renders:
        <input type="file" @change="call('upload_avatar', {}, $event.target.files[0])">
    """
    if kwargs:
        params = "{" + ", ".join(f"{k}: {v}" for k, v in kwargs.items()) + "}"
    else:
        params = "{}"

    return mark_safe(f'@change="call(\'{action}\', {params}, $event.target.files[0])"')


@register.simple_tag
def nitro_cloak():
    """
    Prevent FOUC (Flash of Unstyled Content) - Zero JS mode.

    Elements with x-cloak are hidden until Alpine.js initializes.
    Requires CSS: [x-cloak] { display: none !important; }

    Usage:
        <div {% nitro_show 'showModal' %} {% nitro_cloak %}>
            Modal content - hidden until Alpine initializes
        </div>
    """
    return mark_safe('x-cloak')


@register.simple_tag
def nitro_stop():
    """
    Stop event propagation - Zero JS mode.

    Add this to an element to prevent click events from bubbling up.
    Typically used on modal/slideover content to prevent closing when clicking inside.

    Usage:
        <div {% nitro_show 'showModal' %} {% nitro_stop %}>
            Modal content - clicks here won't close the modal
        </div>

    Example:
        <div {% nitro_action 'close' %}>  {# Backdrop - clicking closes #}
            <div {% nitro_stop %}>          {# Panel - clicks don't bubble #}
                Panel content
            </div>
        </div>
    """
    return mark_safe('@click.stop')


@register.simple_tag
def nitro_rating(field, max_stars=5, size='text-xs'):
    """
    Star rating display - Zero JS mode.

    Displays a star rating using the value from a numeric field (1-5).

    Usage:
        {% nitro_rating 'item.rating' %}
        {% nitro_rating 'tenant.rating' max_stars=5 size='text-sm' %}

    Args:
        field: Numeric field path (1-5)
        max_stars: Maximum number of stars (default: 5)
        size: Tailwind text size class (default: 'text-xs')

    Example:
        {% nitro_rating 'tenant.rating' %}

        Renders:
        <template x-for="i in 5">
            <span :class="i <= tenant.rating ? 'text-yellow-400' : 'text-gray-300'" class="text-xs">★</span>
        </template>
    """
    return mark_safe(
        f'<template x-for="i in {max_stars}">'
        f'<span :class="i <= {field} ? \'text-yellow-400\' : \'text-gray-300\'" class="{size}">★</span>'
        f'</template>'
    )


@register.simple_tag
def nitro_transition(preset='fade'):
    """
    Transition animation preset - Zero JS mode.

    Hides Alpine x-transition syntax for "Zero JavaScript" mode.

    Usage:
        <div {% nitro_show 'isOpen' %} {% nitro_transition 'fade' %}>
        <div {% nitro_show 'show_form' %} {% nitro_transition 'slide-right' %}>
        <div {% nitro_show 'showModal' %} {% nitro_transition 'scale' %}>

    Available presets:
        - fade: Opacity fade in/out (default)
        - slide-right: Slide in from right (for slideovers)
        - slide-left: Slide in from left
        - slide-up: Slide in from bottom
        - slide-down: Slide in from top
        - scale: Scale + fade (for modals)
        - none: No transition

    Example:
        <div {% nitro_show 'show_form' %} {% nitro_transition 'slide-right' %}>
            Slideover content
        </div>

        Expands to:
        <div x-show="show_form"
             x-transition:enter="transform transition ease-out duration-300"
             x-transition:enter-start="translate-x-full"
             x-transition:enter-end="translate-x-0"
             x-transition:leave="transform transition ease-in duration-200"
             x-transition:leave-start="translate-x-0"
             x-transition:leave-end="translate-x-full">
    """
    transitions = TRANSITION_PRESETS.get(preset, TRANSITION_PRESETS['fade'])

    if not transitions:
        return ""

    attrs = []

    if NITRO_DEBUG:
        attrs.append(f'data-nitro-debug="nitro_transition: preset=\'{preset}\'"')

    for key, value in transitions.items():
        attrs.append(f'x-transition:{key}="{value}"')

    return mark_safe(" ".join(attrs))


@register.simple_tag
def nitro_file(field, accept=None, max_size=None, preview=False):
    """
    File upload with progress tracking.

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        <input type="file" {% nitro_file 'document' %}>
        <input type="file" {% nitro_file 'avatar' accept='.jpg,.png' preview=True %}>
        <input type="file" {% nitro_file 'document' accept='.pdf,.docx' max_size='5MB' %}>

    Args:
        field: Field name from state (e.g., 'document', 'avatar')
        accept: File type filter (e.g., '.pdf,.docx', 'image/*')
        max_size: Maximum file size (e.g., '5MB', '1GB')
        preview: If True, show image preview

    Returns:
        HTML attributes string with file upload bindings

    Example:
        <input type="file" {% nitro_file 'avatar' accept='image/*' preview=True %}>

        Expands to:
        <input
            type="file"
            accept="image/*"
            @change="handleFileUpload($event, 'avatar', {preview: true})"
        >

    Note:
        - Requires nitro.js v0.5.0+ for handleFileUpload function
        - Upload progress available in state.uploadProgress
        - Preview URL available in state.filePreview (if preview=True)
    """
    attrs = []

    # Debug info
    if NITRO_DEBUG:
        debug_parts = [f"field='{field}'"]
        if accept:
            debug_parts.append(f"accept='{accept}'")
        if max_size:
            debug_parts.append(f"max_size={max_size}")
        if preview:
            debug_parts.append("preview=True")
        attrs.append(f'data-nitro-debug="nitro_file: {", ".join(debug_parts)}"')

    # Accept attribute
    if accept:
        attrs.append(f'accept="{accept}"')

    # Build options object
    options = {}
    if max_size:
        options["maxSize"] = f"'{max_size}'"
    if preview:
        options["preview"] = "true"

    # File upload handler
    if options:
        options_str = "{" + ", ".join(f"{k}: {v}" for k, v in options.items()) + "}"
        attrs.append(f"@change=\"handleFileUpload($event, '{field}', {options_str})\"")
    else:
        attrs.append(f"@change=\"handleFileUpload($event, '{field}')\"")

    return mark_safe(" ".join(attrs))


class NitroIfNode(Node):
    """
    Node for {% nitro_if %} template tag.

    Conditional rendering wrapper (x-if equivalent).
    """

    def __init__(self, condition, nodelist):
        self.condition = condition
        self.nodelist = nodelist

    def render(self, context):
        output = []

        # Alpine.js x-if template
        output.append(f'<template x-if="{self.condition}">')
        output.append("<div>")
        output.append(self.nodelist.render(context))
        output.append("</div>")
        output.append("</template>")

        return "".join(output)


@register.tag
def nitro_if(parser, token):
    """
    Conditional rendering wrapper (x-if equivalent).

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        {% nitro_if 'user.is_authenticated' %}
            <div>Welcome back!</div>
        {% end_nitro_if %}

        {% nitro_if 'count > 0' %}
            <div>You have {{ count }} items</div>
        {% end_nitro_if %}

        {% nitro_if 'isLoading' %}
            <div class="spinner">Loading...</div>
        {% end_nitro_if %}

    Args:
        condition: JavaScript expression to evaluate

    Returns:
        Wrapped content in Alpine x-if template

    Example:
        {% nitro_if 'user.is_authenticated' %}
            <div class="welcome">
                <h2>Welcome, {% nitro_text 'user.name' %}!</h2>
            </div>
        {% end_nitro_if %}

        Expands to:
        <template x-if="user.is_authenticated">
            <div>
                <div class="welcome">
                    <h2>Welcome, <span x-text="user.name">...</span>!</h2>
                </div>
            </div>
        </template>

    Note:
        - Content is completely removed from DOM when condition is false
        - For visibility toggling (hiding with CSS), use {% nitro_show %} instead
        - x-if requires a single root element (automatically wrapped in <div>)
    """
    try:
        # Parse: {% nitro_if 'condition' %}
        bits = token.split_contents()
        if len(bits) != 2:
            raise TemplateSyntaxError(
                f"{bits[0]} tag requires format: {{% nitro_if 'condition' %}}"
            )

        tag_name, condition = bits

        # Remove quotes from condition
        condition = condition.strip("'\"")

    except ValueError:
        raise TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires format: {{% nitro_if 'condition' %}}"
        ) from None

    # Parse until {% end_nitro_if %}
    nodelist = parser.parse(("end_nitro_if",))
    parser.delete_first_token()

    return NitroIfNode(condition, nodelist)


# ============================================================================
# FORM FIELD TEMPLATE TAGS - Complete Alpine.js Abstraction (v0.6.0)
# ============================================================================


@register.inclusion_tag("nitro/fields/input.html")
def nitro_input(field, label="", type="text", required=False, placeholder="", **kwargs):
    """
    Complete form input abstraction - no Alpine.js knowledge needed.

    Automatically handles:
    - edit_buffer vs create_buffer (adds ?. for edit_buffer)
    - Error validation styling
    - Consistent CSS classes
    - Labels and required indicators

    Usage:
        {% nitro_input field="create_buffer.name" label="Nombre" required=True %}
        {% nitro_input field="edit_buffer.email" label="Email" type="email" %}
        {% nitro_input field="edit_buffer.price" label="Precio" type="number" step="0.01" %}

    Args:
        field: Field path (e.g., 'create_buffer.name', 'edit_buffer.email')
        label: Field label (optional)
        type: Input type (text, number, email, date, etc.)
        required: Show required indicator
        placeholder: Placeholder text
        **kwargs: Additional HTML attributes (step, min, max, etc.)
    """
    # Use utility functions for safe field and error path
    # IMPORTANT: x-model needs the original field (without ?.) for write access
    # safe_field (with ?.) is only used for reading values in events
    safe_field, is_edit_buffer = build_safe_field(field)
    error_path = build_error_path(field)

    # Extract buffer name for null safety check (e.g., "edit_buffer" from "edit_buffer.name")
    buffer_name = field.split(".")[0] if "." in field else ""

    return {
        "field": field,
        "safe_field": safe_field,
        "error_path": error_path,
        "label": label,
        "type": type,
        "required": required,
        "placeholder": placeholder,
        "extra_attrs": " ".join(f'{k}="{v}"' for k, v in kwargs.items()),
        "debug": NITRO_DEBUG,
        "is_edit_buffer": is_edit_buffer,
        "buffer_name": buffer_name,
    }


@register.inclusion_tag("nitro/fields/select.html")
def nitro_select(field, label="", choices=None, required=False, multi=False, **kwargs):
    """
    Complete form select abstraction - no Alpine.js knowledge needed.

    Usage:
        {% nitro_select field="create_buffer.status" label="Estado" choices=status_choices %}
        {% nitro_select field="edit_buffer.property_type" label="Tipo" choices=property_types %}
        {% nitro_select field="create_buffer.tags" label="Tags" choices=tag_choices multi=True %}

    Args:
        field: Field path
        label: Field label
        choices: List of (value, display) tuples or [{'value': ..., 'label': ...}]
        required: Show required indicator
        multi: If True, allows multiple selection (field should be a list)
    """
    # Use utility functions for safe field and error path
    safe_field, is_edit_buffer = build_safe_field(field)
    error_path = build_error_path(field)

    # Extract buffer name for null safety check
    buffer_name = field.split(".")[0] if "." in field else ""

    # Normalize choices format
    normalized_choices = []
    if choices:
        for choice in choices:
            if isinstance(choice, (list, tuple)):
                normalized_choices.append({"value": choice[0], "label": choice[1]})
            elif isinstance(choice, dict):
                normalized_choices.append(choice)

    return {
        "field": field,
        "safe_field": safe_field,
        "error_path": error_path,
        "label": label,
        "choices": normalized_choices,
        "required": required,
        "multi": multi,
        "extra_attrs": " ".join(f'{k}="{v}"' for k, v in kwargs.items()),
        "debug": NITRO_DEBUG,
        "is_edit_buffer": is_edit_buffer,
        "buffer_name": buffer_name,
    }


@register.inclusion_tag("nitro/fields/dynamic_select.html")
def nitro_dynamic_select(
    field,
    options_var,
    option_value="id",
    option_label="name",
    label="",
    required=False,
    placeholder="",
    on_change=None,
    on_change_param=None,
    **kwargs,
):
    """
    Dynamic select with options from Alpine state (x-for).

    Use this for selects where options come from component state (provinces,
    municipalities, landlords, etc.) instead of static choices.

    Usage:
        {% nitro_dynamic_select field='create_buffer.province_id' options_var='provinces' label='Provincia' %}
        {% nitro_dynamic_select field='sector_id' options_var='sectors' on_change='load_data' on_change_param='sector_id' %}
        {% nitro_dynamic_select field='landlord_id' options_var='landlords' option_value='id' option_label='full_name' %}

    Args:
        field: Field path for x-model binding
        options_var: Alpine state variable containing the options array
        option_value: Property name for option value (default: 'id')
        option_label: Property name for option display text (default: 'name')
        label: Field label
        required: Show required indicator
        placeholder: Placeholder text for empty option
        on_change: Method to call when selection changes (instead of _sync_field)
        on_change_param: Parameter name to pass to on_change method (uses field value)
        **kwargs: Additional HTML attributes

    Example:
        State: provinces = [{"id": 1, "name": "Santo Domingo"}, ...]

        {% nitro_dynamic_select field='province_id' options_var='provinces'
           on_change='load_municipalities' on_change_param='province_id' %}

        Generates:
        <select x-model="province_id"
                @change="call('load_municipalities', {province_id: $event.target.value})">
            <template x-for="opt in provinces" :key="opt.id">
                <option :value="opt.id" x-text="opt.name"></option>
            </template>
        </select>
    """
    safe_field, is_edit_buffer = build_safe_field(field)
    error_path = build_error_path(field)

    # Extract buffer name for null safety check
    buffer_name = field.split(".")[0] if "." in field else ""

    # Build change handler
    if on_change:
        param_name = on_change_param or field.split(".")[-1]
        change_handler = f"call('{on_change}', {{{param_name}: $event.target.value}})"
    else:
        # Default: sync field to server
        change_handler = f"call('_sync_field', {{field: '{field}', value: $event.target.value}}, null, {{silent: true}})"

    return {
        "field": field,
        "safe_field": safe_field,
        "error_path": error_path,
        "options_var": options_var,
        "option_value": option_value,
        "option_label": option_label,
        "label": label,
        "required": required,
        "placeholder": placeholder or "-- Seleccionar --",
        "change_handler": change_handler,
        "extra_attrs": " ".join(f'{k}="{v}"' for k, v in kwargs.items()),
        "debug": NITRO_DEBUG,
        "is_edit_buffer": is_edit_buffer,
        "buffer_name": buffer_name,
    }


@register.inclusion_tag("nitro/fields/checkbox.html")
def nitro_checkbox(field, label="", **kwargs):
    """
    Complete form checkbox abstraction - no Alpine.js knowledge needed.

    Usage:
        {% nitro_checkbox field="create_buffer.is_active" label="Activo" %}
        {% nitro_checkbox field="edit_buffer.is_vendor" label="Es Vendor" %}

    Args:
        field: Field path
        label: Checkbox label
    """
    is_edit_buffer = "edit_buffer" in field
    safe_field = field.replace(".", "?.") if is_edit_buffer else field

    # Extract buffer name for null safety check
    buffer_name = field.split(".")[0] if "." in field else ""

    # For checkboxes, we need special handling for @change (silent mode to prevent loading flash)
    # If edit_buffer, wrap in null check
    # Also track changes for dirty state
    change_handler = (
        f"if({field.split('.')[0]}) {{ trackChange('{field}'); {field} = $el.checked }}"
        if is_edit_buffer
        else f"trackChange('{field}'); {field} = $el.checked; call('_sync_field', {{field: '{field}', value: {field}}}, null, {{silent: true}})"
    )

    return {
        "field": field,
        "safe_field": safe_field,
        "label": label,
        "change_handler": change_handler,
        "is_edit_buffer": is_edit_buffer,
        "buffer_name": buffer_name,
        "extra_attrs": " ".join(f'{k}="{v}"' for k, v in kwargs.items()),
        "debug": NITRO_DEBUG,
    }


@register.inclusion_tag("nitro/fields/textarea.html")
def nitro_textarea(field, label="", required=False, rows=3, placeholder="", **kwargs):
    """
    Complete form textarea abstraction - no Alpine.js knowledge needed.

    Usage:
        {% nitro_textarea field="create_buffer.description" label="Descripción" rows=5 %}
        {% nitro_textarea field="edit_buffer.notes" label="Notas" required=True %}

    Args:
        field: Field path
        label: Field label
        required: Show required indicator
        rows: Number of rows
        placeholder: Placeholder text
    """
    # Use utility functions for safe field and error path
    safe_field, is_edit_buffer = build_safe_field(field)
    error_path = build_error_path(field)

    # Extract buffer name for null safety check
    buffer_name = field.split(".")[0] if "." in field else ""

    return {
        "field": field,
        "safe_field": safe_field,
        "error_path": error_path,
        "label": label,
        "required": required,
        "rows": rows,
        "placeholder": placeholder,
        "extra_attrs": " ".join(f'{k}="{v}"' for k, v in kwargs.items()),
        "debug": NITRO_DEBUG,
        "is_edit_buffer": is_edit_buffer,
        "buffer_name": buffer_name,
    }


@register.inclusion_tag("nitro/fields/phone.html")
def nitro_phone(field, label="", required=False, placeholder="", **kwargs):
    """
    Phone input with automatic formatting mask (XXX-XXX-XXXX).

    Usage:
        {% nitro_phone field="form_buffer.phone" label="Teléfono" %}
        {% nitro_phone field="form_buffer.whatsapp" label="WhatsApp" placeholder="809-555-1234" %}

    Args:
        field: Field path
        label: Field label
        required: Show required indicator
        placeholder: Placeholder text (default: 809-555-1234)
    """
    safe_field, is_edit_buffer = build_safe_field(field)
    error_path = build_error_path(field)
    buffer_name = field.split(".")[0] if "." in field else ""

    return {
        "field": field,
        "safe_field": safe_field,
        "error_path": error_path,
        "label": label,
        "required": required,
        "placeholder": placeholder,
        "extra_attrs": " ".join(f'{k}="{v}"' for k, v in kwargs.items()),
        "debug": NITRO_DEBUG,
        "is_edit_buffer": is_edit_buffer,
        "buffer_name": buffer_name,
    }


# ============================================================================
# TRUE ZERO-JS TEMPLATE TAGS (v0.7.0)
# ============================================================================
# These tags implement the TRUE Zero-JavaScript philosophy:
# - All logic defined in Python kwargs, not JavaScript expressions
# - Developers never write JS ternaries or Alpine expressions
# - Templates are pure Django with Nitro tags

# Import Zero-JS tags from dedicated module (at end to avoid circular imports)
from nitro.templatetags.nitro_zero import (  # noqa: E402
    nitro_badge,
    nitro_call,
    nitro_count,
    nitro_date,
    nitro_format,
    nitro_plural,
    nitro_switch,
    nitro_visible,
)
from nitro.templatetags.nitro_zero import (  # noqa: E402
    nitro_class as nitro_class_zero,
)

# Register Zero-JS tags
register.simple_tag(nitro_switch)
register.simple_tag(nitro_class_zero, name='nitro_css')  # Value→CSS mapping
register.simple_tag(nitro_visible)  # Use negate=True instead of nitro_hidden
register.simple_tag(nitro_plural)
register.simple_tag(nitro_count)
register.simple_tag(nitro_format)
register.simple_tag(nitro_date)
register.simple_tag(nitro_badge)
# nitro_for is in main tags (better SEO), nitro_each removed
register.simple_tag(takes_context=True)(nitro_call)


# ============================================================================
# SHORTHAND ALIASES (v0.7.0 DX Improvement)
# ============================================================================
# Shorter aliases for common tags - inspired by Django Unicorn's DX
# Use n_ prefix instead of nitro_ for faster typing

# Core tags
register.simple_tag(nitro_model, name='n_model')
register.simple_tag(nitro_action, name='n_action')
register.simple_tag(nitro_show, name='n_show')
register.simple_tag(nitro_class, name='n_class')
register.simple_tag(nitro_attr, name='n_attr')
register.simple_tag(nitro_text, name='n_text')
register.simple_tag(nitro_bind, name='n_bind')

# Form field tags
register.inclusion_tag("nitro/fields/input.html")(nitro_input)
register.inclusion_tag("nitro/fields/input.html", name='n_input')(nitro_input)
register.inclusion_tag("nitro/fields/select.html", name='n_select')(nitro_select)
register.inclusion_tag("nitro/fields/checkbox.html", name='n_checkbox')(nitro_checkbox)
register.inclusion_tag("nitro/fields/textarea.html", name='n_textarea')(nitro_textarea)
register.inclusion_tag("nitro/fields/phone.html", name='n_phone')(nitro_phone)

# Action/event tags
register.simple_tag(nitro_toggle, name='n_toggle')
register.simple_tag(nitro_set, name='n_set')
register.simple_tag(nitro_key, name='n_key')
register.simple_tag(nitro_disabled, name='n_disabled')
register.simple_tag(nitro_file, name='n_file')

# Zero-JS tags
register.simple_tag(nitro_switch, name='n_switch')
register.simple_tag(nitro_class_zero, name='n_css')
register.simple_tag(nitro_visible, name='n_visible')
register.simple_tag(nitro_badge, name='n_badge')
register.simple_tag(nitro_rating, name='n_rating')
register.simple_tag(nitro_transition, name='n_transition')
register.simple_tag(nitro_cloak, name='n_cloak')
register.simple_tag(nitro_stop, name='n_stop')
