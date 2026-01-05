# nitro/templatetags/nitro_tags.py
from django import template
from django.template.base import Node, TemplateSyntaxError
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.templatetags.static import static
from django.conf import settings

from nitro.registry import get_component_class

register = template.Library()

# Debug mode flag
NITRO_DEBUG = getattr(settings, 'DEBUG', False) and getattr(
    settings, 'NITRO', {}
).get('DEBUG', False)


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
    css_path = static('nitro/nitro.css')
    js_path = static('nitro/nitro.js')

    return mark_safe(
        f'<link rel="stylesheet" href="{css_path}">\n'
        f'<script defer src="{js_path}"></script>'
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
        output.append('<div class="nitro-seo-content" style="display: none;">')
        for item in items:
            context.push({self.item_var: item})
            output.append(self.nodelist.render(context))
            context.pop()
        output.append('</div>')

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

        output.append('</template>')

        return ''.join(output)


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
        if len(bits) != 4 or bits[2] != 'as':
            raise TemplateSyntaxError(
                f"{bits[0]} tag requires format: "
                "{% nitro_for 'list_var' as 'item_var' %}"
            )

        tag_name, list_var, as_word, item_var = bits

        # Remove quotes from variables
        list_var = list_var.strip('\'"')
        item_var = item_var.strip('\'"')

    except ValueError:
        raise TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires format: "
            "{% nitro_for 'list_var' as 'item_var' %}"
        )

    # Parse until {% end_nitro_for %}
    nodelist = parser.parse(('end_nitro_for',))
    parser.delete_first_token()

    return NitroForNode(list_var, item_var, nodelist)


class NitroTextNode(Node):
    """
    Node for {% nitro_text %} template tag.

    Renders server-side value + Alpine.js x-text binding.
    """

    def __init__(self, var_name):
        self.var = template.Variable(var_name)
        self.var_name = var_name

    def render(self, context):
        # Get value from context
        try:
            value = self.var.resolve(context)
        except template.VariableDoesNotExist:
            value = ''

        # Render with both server value (SEO) and x-text binding (reactivity)
        # Escape value to prevent XSS in initial render
        return mark_safe(f'<span x-text="{self.var_name}">{escape(value)}</span>')


@register.tag
def nitro_text(parser, token):
    """
    SEO-friendly x-text binding.

    Renders static text on server (SEO) + Alpine.js x-text for reactivity.

    Usage:
        {% nitro_text 'item.name' %}

    Results in:
        <span x-text="item.name">John Doe</span>

    - SEO crawlers see "John Doe"
    - Alpine updates the content when state changes

    Example:
        <div class="card">
            <h3>{% nitro_text 'item.name' %}</h3>
            <p>Email: {% nitro_text 'item.email' %}</p>
        </div>
    """
    try:
        tag_name, var_name = token.split_contents()
        # Remove quotes
        var_name = var_name.strip('\'"')
    except ValueError:
        raise TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires a single argument: "
            "{% nitro_text 'variable_name' %}"
        )

    return NitroTextNode(var_name)


# ============================================================================
# ZERO JAVASCRIPT MODE - Wire-like Template Tags (v0.4.0)
# ============================================================================

@register.simple_tag
def nitro_model(field, debounce=None, lazy=False, on_change=None):
    """
    Auto-sync bidirectional binding (wire:model equivalent).

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        {% nitro_model 'email' %}
        {% nitro_model 'search' debounce='300ms' %}
        {% nitro_model 'password' lazy=True %}
        {% nitro_model 'email' on_change='validate_email' %}

    Args:
        field: Field name from state (e.g., 'email', 'search')
        debounce: Debounce time (e.g., '300ms', '1s')
        lazy: If True, sync on blur instead of input
        on_change: Optional action to call after sync

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
    event = '@blur' if lazy else '@input'
    if debounce:
        event += f'.debounce.{debounce}'

    # Auto-sync call
    sync_call = f"call('_sync_field', {{field: '{field}', value: {field}}})"

    # Add optional on_change callback
    if on_change:
        sync_call += f"; call('{on_change}')"

    attrs.append(f'{event}="{sync_call}"')

    # Add error styling
    attrs.append(f":class=\"{{'border-red-500': errors.{field}}}\"")

    return mark_safe(' '.join(attrs))


@register.simple_tag
def nitro_action(action, **kwargs):
    """
    Action button (wire:click equivalent).

    Hides Alpine syntax for "Zero JavaScript" mode.

    Usage:
        {% nitro_action 'submit' %}
        {% nitro_action 'delete' id='item.id' %}
        {% nitro_action 'update' id='task.id' status='completed' %}

    Args:
        action: Action method name
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
    """
    attrs = []

    # Debug info
    if NITRO_DEBUG:
        debug_info = f"nitro_action: action='{action}'"
        if kwargs:
            params_str = ', '.join(f'{k}={v}' for k, v in kwargs.items())
            debug_info += f", params=({params_str})"
        attrs.append(f'data-nitro-debug="{debug_info}"')

    # Build params object
    if kwargs:
        params = '{' + ', '.join(f'{k}: {v}' for k, v in kwargs.items()) + '}'
        click_handler = f"call('{action}', {params})"
    else:
        click_handler = f"call('{action}')"

    attrs.append(f'@click="{click_handler}"')

    # Auto-disable during loading
    attrs.append(':disabled="isLoading"')

    return mark_safe(' '.join(attrs))


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
        return ''

    class_obj = '{' + ', '.join(f"'{k}': {v}" for k, v in conditions.items()) + '}'
    return mark_safe(f':class="{class_obj}"')


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

    return mark_safe(' '.join(attrs))


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

    return mark_safe(' '.join(attrs))


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
        options['maxSize'] = f"'{max_size}'"
    if preview:
        options['preview'] = 'true'

    # File upload handler
    if options:
        options_str = '{' + ', '.join(f'{k}: {v}' for k, v in options.items()) + '}'
        attrs.append(f'@change="handleFileUpload($event, \'{field}\', {options_str})"')
    else:
        attrs.append(f'@change="handleFileUpload($event, \'{field}\')"')

    return mark_safe(' '.join(attrs))


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
        output.append('<div>')
        output.append(self.nodelist.render(context))
        output.append('</div>')
        output.append('</template>')

        return ''.join(output)


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
                f"{bits[0]} tag requires format: "
                "{% nitro_if 'condition' %}"
            )

        tag_name, condition = bits

        # Remove quotes from condition
        condition = condition.strip('\'"')

    except ValueError:
        raise TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires format: "
            "{% nitro_if 'condition' %}"
        )

    # Parse until {% end_nitro_if %}
    nodelist = parser.parse(('end_nitro_if',))
    parser.delete_first_token()

    return NitroIfNode(condition, nodelist)
