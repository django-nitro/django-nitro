# nitro/templatetags/nitro_zero.py
"""
Nitro Zero-JS Template Tags

TRUE "Zero JavaScript" template tags where ALL logic lives in Python.
Developers never write JavaScript expressions - they define mappings
and methods in their components.

Philosophy:
- No JS ternaries, no Alpine expressions in templates
- All conditional logic defined in Python (component or inline kwargs)
- Templates are pure Django with Nitro tags
- Alpine.js is an implementation detail, never exposed

Usage:
    {% load nitro_zero %}

    {# Conditional text based on field value #}
    {% nitro_switch 'item.status' active='Activo' expired='Vencido' default='Borrador' %}

    {# Conditional CSS classes #}
    {% nitro_class 'item.status' active='bg-green-100 text-green-700' expired='bg-red-100' %}

    {# Call a Python method for complex logic #}
    {% nitro_call 'get_status_badge' item %}

    {# Boolean show/hide - no JS expressions #}
    {% nitro_visible 'item.is_active' %}
    {% nitro_hidden 'item.is_deleted' %}
"""

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
import json

register = template.Library()


def _build_alpine_switch(field: str, mappings: dict, default: str = '') -> str:
    """
    Build Alpine.js switch expression from Python mappings.

    Converts Python dict to JS switch-like expression internally.
    The developer never sees or writes this JS.
    """
    if not mappings:
        return f'x-text="{field}"'

    # Build conditions array for cleaner JS
    conditions = []
    for value, display in mappings.items():
        if value != '_default':
            # Escape the display text for safety
            safe_display = escape(display).replace("'", "\\'")
            conditions.append(f"{field} === '{value}' ? '{safe_display}'")

    # Add default
    default_text = escape(default or mappings.get('_default', '')).replace("'", "\\'")

    if conditions:
        expr = " : ".join(conditions) + f" : '{default_text}'"
        return f'x-text="{expr}"'

    return f'x-text="{field}"'


def _build_alpine_class_switch(field: str, mappings: dict, default: str = '') -> str:
    """
    Build Alpine.js class binding from Python mappings.

    Converts Python dict to :class object internally.
    """
    if not mappings:
        return ''

    # Build class object
    class_obj = {}
    for value, classes in mappings.items():
        if value != '_default':
            class_obj[classes] = f"{field} === '{value}'"

    if default:
        # Default classes when no match - need to negate all conditions
        negations = [f"{field} !== '{v}'" for v in mappings.keys() if v != '_default']
        if negations:
            class_obj[default] = " && ".join(negations)

    # Convert to JS object string
    class_items = [f"'{k}': {v}" for k, v in class_obj.items()]
    return f":class=\"{{{', '.join(class_items)}}}\""


@register.simple_tag
def nitro_switch(field: str, default: str = '', **mappings):
    """
    Display text based on field value using Python-defined mappings.

    TRUE Zero-JS: You define the mappings in Python (kwargs), not JavaScript.

    Usage:
        {% nitro_switch 'item.status' active='Activo' expired='Vencido' default='Borrador' %}
        {% nitro_switch 'user.role' admin='Administrador' user='Usuario' guest='Invitado' %}

    Args:
        field: The state field path (e.g., 'item.status', 'user.role')
        default: Default text when no mapping matches
        **mappings: value='Display Text' pairs

    Returns:
        <span> element with server value and Alpine binding

    Example:
        {% nitro_switch 'lease.status' active='Activo' expired='Vencido' draft='Borrador' %}

        Renders (if status='active'):
        <span x-text="lease.status === 'active' ? 'Activo' : lease.status === 'expired' ? 'Vencido' : 'Borrador'">Activo</span>

    Note:
        The JavaScript is generated automatically - you never write it.
        All your logic stays in Python kwargs.
    """
    # Get server-side value for initial render (SEO)
    # In template context, we can't access the actual value,
    # so we render with Alpine binding that will hydrate

    alpine_attr = _build_alpine_switch(field, mappings, default)

    # Initial display will be handled by Alpine on hydration
    # For SEO, we could potentially pass initial value, but keeping simple for now
    return mark_safe(f'<span {alpine_attr}></span>')


@register.simple_tag
def nitro_class(field: str, default: str = '', **mappings):
    """
    Apply CSS classes based on field value using Python-defined mappings.

    TRUE Zero-JS: You define class mappings in Python, not JavaScript ternaries.

    Usage:
        {% nitro_class 'item.status' active='bg-green-100 text-green-700' expired='bg-red-100 text-red-700' %}
        {% nitro_class 'priority' high='text-red-600 font-bold' low='text-gray-500' %}

    Args:
        field: The state field path
        default: Default classes when no mapping matches
        **mappings: value='css-classes' pairs

    Returns:
        Alpine :class binding attribute

    Example:
        <span {% nitro_class 'item.status' active='bg-green-100' expired='bg-red-100' default='bg-gray-100' %}>
            Status
        </span>
    """
    return mark_safe(_build_alpine_class_switch(field, mappings, default))


@register.simple_tag
def nitro_visible(field: str, negate: bool = False):
    """
    Show element when boolean field is true.

    TRUE Zero-JS: Just pass the field name, no JS expressions.

    Usage:
        {% nitro_visible 'item.is_active' %}
        {% nitro_visible 'show_details' %}
        {% nitro_visible 'item.is_hidden' negate=True %}  {# Show when false #}

    Args:
        field: Boolean field path
        negate: If True, show when field is false

    Returns:
        x-show attribute
    """
    expr = f"!{field}" if negate else field
    return mark_safe(f'x-show="{expr}"')


# nitro_hidden REMOVED in v0.7.0 - Use nitro_visible with negate=True instead
# {% nitro_visible 'is_deleted' negate=True %}


@register.simple_tag
def nitro_plural(field: str, singular: str, plural: str, zero: str = None):
    """
    Display singular/plural text based on numeric field.

    TRUE Zero-JS: Define the words in Python, not JS.

    Usage:
        {% nitro_plural 'count' singular='item' plural='items' %}
        {% nitro_plural 'items.length' singular='propiedad' plural='propiedades' zero='Sin propiedades' %}

    Args:
        field: Numeric field path
        singular: Text for count=1
        plural: Text for count!=1
        zero: Optional text for count=0

    Returns:
        <span> with appropriate text binding
    """
    singular_escaped = escape(singular).replace("'", "\\'")
    plural_escaped = escape(plural).replace("'", "\\'")

    if zero:
        zero_escaped = escape(zero).replace("'", "\\'")
        expr = f"{field} === 0 ? '{zero_escaped}' : {field} === 1 ? '{singular_escaped}' : '{plural_escaped}'"
    else:
        expr = f"{field} === 1 ? '{singular_escaped}' : '{plural_escaped}'"

    return mark_safe(f'<span x-text="{expr}"></span>')


@register.simple_tag
def nitro_count(field: str, singular: str, plural: str, zero: str = None):
    """
    Display count with label (e.g., "5 items", "1 item", "No items").

    Usage:
        {% nitro_count 'items.length' singular='item' plural='items' zero='No items' %}

    Renders: "5 items" or "1 item" or "No items"
    """
    singular_escaped = escape(singular).replace("'", "\\'")
    plural_escaped = escape(plural).replace("'", "\\'")

    if zero:
        zero_escaped = escape(zero).replace("'", "\\'")
        expr = f"{field} === 0 ? '{zero_escaped}' : {field} + ' ' + ({field} === 1 ? '{singular_escaped}' : '{plural_escaped}')"
    else:
        expr = f"{field} + ' ' + ({field} === 1 ? '{singular_escaped}' : '{plural_escaped}')"

    return mark_safe(f'<span x-text="{expr}"></span>')


@register.simple_tag
def nitro_format(field: str, format_type: str = 'text', prefix: str = '', suffix: str = '', empty: str = ''):
    """
    Format a field value with common patterns.

    TRUE Zero-JS: Specify format type, not JS formatting code.

    Usage:
        {% nitro_format 'item.price' format_type='currency' prefix='$' %}
        {% nitro_format 'item.percentage' suffix='%' %}
        {% nitro_format 'item.date' empty='Sin fecha' %}

    Args:
        field: Field path
        format_type: 'text', 'currency', 'number', 'date'
        prefix: Text before value
        suffix: Text after value
        empty: Text when value is empty/null

    Returns:
        <span> with formatted value
    """
    prefix_escaped = escape(prefix).replace("'", "\\'")
    suffix_escaped = escape(suffix).replace("'", "\\'")
    empty_escaped = escape(empty).replace("'", "\\'")

    if format_type == 'currency':
        # Format as locale number
        value_expr = f"{field}?.toLocaleString() || '0'"
    elif format_type == 'number':
        value_expr = f"{field}?.toLocaleString() || '0'"
    else:
        value_expr = field

    if empty:
        expr = f"{field} ? '{prefix_escaped}' + {value_expr} + '{suffix_escaped}' : '{empty_escaped}'"
    else:
        expr = f"'{prefix_escaped}' + ({value_expr}) + '{suffix_escaped}'"

    return mark_safe(f'<span x-text="{expr}"></span>')


@register.simple_tag
def nitro_date(field: str, empty: str = ''):
    """
    Display a date field in locale format.

    Usage:
        {% nitro_date 'item.created_at' %}
        {% nitro_date 'lease.end_date' empty='Sin fecha' %}
    """
    empty_escaped = escape(empty).replace("'", "\\'")

    if empty:
        expr = f"{field} ? new Date({field}).toLocaleDateString() : '{empty_escaped}'"
    else:
        expr = f"{field} ? new Date({field}).toLocaleDateString() : ''"

    return mark_safe(f'<span x-text="{expr}"></span>')


@register.simple_tag
def nitro_badge(field: str, default_class: str = 'bg-gray-100 text-gray-700', **mappings):
    """
    Render a status badge with conditional styling.

    Combines nitro_switch (text) and nitro_class (styling) in one tag.

    Usage:
        {% nitro_badge 'item.status'
           active='Activo:bg-green-100 text-green-700'
           expired='Vencido:bg-red-100 text-red-700'
           default_class='bg-gray-100 text-gray-700' %}

    Format: value='DisplayText:css-classes'

    Args:
        field: Field path
        default_class: Default badge classes
        **mappings: value='Text:classes' pairs
    """
    # Parse mappings into text and class dicts
    text_map = {}
    class_map = {}
    default_text = ''

    for value, combined in mappings.items():
        if ':' in combined:
            text, classes = combined.split(':', 1)
            text_map[value] = text
            class_map[value] = classes
        else:
            text_map[value] = combined

    # Build the expressions
    text_attr = _build_alpine_switch(field, text_map, default_text)
    class_attr = _build_alpine_class_switch(field, class_map, default_class)

    base_classes = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"

    return mark_safe(f'<span class="{base_classes}" {class_attr} {text_attr}></span>')


# =============================================================================
# ITERATION TAGS (Zero-JS versions)
# =============================================================================

from django.template.base import Node, TemplateSyntaxError


class NitroEachNode(Node):
    """
    Zero-JS iteration: Server renders all items, Alpine handles updates.

    Unlike the old nitro_for, this doesn't require understanding x-for syntax.
    """

    def __init__(self, list_var, item_var, nodelist):
        self.list_var = list_var
        self.item_var = item_var
        self.nodelist = nodelist

    def render(self, context):
        # Resolve the list from context
        try:
            items = template.Variable(self.list_var).resolve(context)
        except template.VariableDoesNotExist:
            items = []

        output = []

        # Server-side render each item
        output.append(f'<template x-for="({self.item_var}, _idx) in {self.list_var}" :key="{self.item_var}.id || _idx">')

        # Render content with first item for structure (Alpine will re-render)
        if items:
            context.push({self.item_var: items[0], f'{self.item_var}_index': 0})
            output.append(self.nodelist.render(context))
            context.pop()
        else:
            # Empty state - render template for Alpine
            output.append(self.nodelist.render(context))

        output.append('</template>')

        return ''.join(output)


@register.tag('nitro_each')
def nitro_each(parser, token):
    """
    Iterate over a list with server-side rendering and Alpine reactivity.

    TRUE Zero-JS: Just specify list and item name, no x-for syntax needed.

    Usage:
        {% nitro_each 'items' as 'item' %}
            <div>{{ item.name }}</div>
        {% end_nitro_each %}

        {% nitro_each 'tenants' as 'tenant' %}
            <div>{% nitro_text 'tenant.full_name' %}</div>
        {% end_nitro_each %}

    Args:
        list_var: Name of the list in state (e.g., 'items', 'tenants')
        item_var: Name for each item (e.g., 'item', 'tenant')
    """
    bits = token.split_contents()

    if len(bits) != 4 or bits[2] != 'as':
        raise TemplateSyntaxError(
            f"{bits[0]} tag requires format: {{% nitro_each 'list' as 'item' %}}"
        )

    list_var = bits[1].strip("'\"")
    item_var = bits[3].strip("'\"")

    nodelist = parser.parse(('end_nitro_each',))
    parser.delete_first_token()

    return NitroEachNode(list_var, item_var, nodelist)


# =============================================================================
# COMPONENT METHOD CALLS
# =============================================================================

@register.simple_tag(takes_context=True)
def nitro_call(context, method_name: str, *args):
    """
    Call a component method and display the result.

    For complex logic that can't be expressed with simple mappings,
    define a method in your component and call it from the template.

    Usage:
        In component:
            def get_status_display(self, item):
                if item.expiring_soon:
                    return "⚠️ Por Vencer"
                return self.STATUS_LABELS.get(item.status, "Desconocido")

        In template:
            {% nitro_call 'get_status_display' item %}

    Note:
        This is for server-side rendering. For reactive updates,
        the component should include the computed value in its state.
    """
    # Get the component instance from context
    component = context.get('_nitro_component')
    if not component:
        return ''

    # Get the method
    method = getattr(component, method_name, None)
    if not method or not callable(method):
        return ''

    # Call with args
    try:
        result = method(*args)
        return escape(str(result)) if result else ''
    except Exception:
        return ''
