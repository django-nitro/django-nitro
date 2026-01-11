"""
Nitro Components - Reusable UI patterns

This module provides template tags for common UI patterns in Nitro apps:
- Toggle buttons with show/hide states
- Submit buttons with loading states
- Expandable panels
- Form fields with consistent styling

Usage:
    {% load nitro_components %}
"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def toggle_btn(state_var, action_name, open_text='+ Create', close_text='✕ Cancel', css_class=''):
    """
    Generate a toggle button that shows different text based on state.

    Args:
        state_var: State variable to check (e.g., 'show_create_form')
        action_name: Nitro action to call on click
        open_text: Text when panel is closed
        close_text: Text when panel is open
        css_class: Additional CSS classes

    Usage:
        {% toggle_btn 'show_create_form' 'toggle_create_form' '+ Create' '✕ Cancel' 'btn-primary w-full' %}
    """
    default_class = 'w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg active:scale-95 transition-transform'
    final_class = css_class if css_class else default_class

    html = f'''<button @click="call('{action_name}')" class="{final_class}">
    <span x-show="!{state_var}">{open_text}</span>
    <span x-show="{state_var}">{close_text}</span>
</button>'''
    return mark_safe(html)


@register.simple_tag
def loading_btn(text='Save', loading_text='Saving...', css_class='', icon='💾'):
    """
    Generate a button with loading state. MUST be used with nitro_action separately.

    Args:
        text: Button text
        loading_text: Text shown during loading
        css_class: CSS classes
        icon: Optional icon/emoji

    Usage:
        <button {% nitro_action 'save_item' %} {% loading_btn 'Save Item' 'Saving...' 'btn-primary' '💾' %}></button>

    Or use the content:
        {% loading_btn 'Save Item' 'Saving...' 'btn-primary' '💾' %}
    """
    default_class = 'bg-blue-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg active:scale-95 transition-transform'
    final_class = css_class if css_class else default_class

    html = f'''class="{final_class}" :disabled="is_loading">
    <span x-show="!is_loading">{icon} {text}</span>
    <span x-show="is_loading" class="flex items-center justify-center gap-2">
        <span class="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
        {loading_text}
    </span'''
    return mark_safe(html)


@register.simple_tag
def panel_container(state_var='show_form', css_class=''):
    """
    Start an expandable panel container with Alpine transitions.

    Args:
        state_var: State variable that controls visibility
        css_class: Additional CSS classes

    Usage:
        {% panel_container 'show_create_form' 'bg-white rounded-lg shadow-sm p-4' %}
            <!-- Your form content -->
        </div>
    """
    default_class = 'bg-white rounded-lg shadow-sm p-4'
    final_class = css_class if css_class else default_class

    html = f'<div x-show="{state_var}" class="{final_class}" x-transition>'
    return mark_safe(html)


@register.simple_tag
def form_field(label, field_type='text', placeholder='', help_text='', required=False, **kwargs):
    """
    Generate a consistent form field with label and styling.

    Args:
        label: Field label
        field_type: Input type (text, number, date, email, etc.)
        placeholder: Placeholder text
        help_text: Optional help text below field
        required: Whether field is required
        **kwargs: Additional attributes (step, min, max, etc.)

    Usage:
        {% form_field 'Email Address' 'email' 'user@example.com' 'We will never share your email' True %}

    Note: You still need to add {% nitro_model %} separately for data binding.
    """
    req_indicator = ' *' if required else ''
    attrs = ' '.join([f'{k}="{v}"' for k, v in kwargs.items()])

    html = f'''<div>
    <label class="block text-sm font-medium text-gray-700 mb-1">{label}{req_indicator}</label>
    <input type="{field_type}"
           placeholder="{placeholder}"
           {attrs}
           class="w-full rounded-lg border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
    {f'<p class="text-xs text-gray-500 mt-1">{help_text}</p>' if help_text else ''}
</div>'''
    return mark_safe(html)


@register.simple_tag
def card(title='', subtitle='', css_class='', border_color=''):
    """
    Start a card container with optional title.

    Args:
        title: Card title
        subtitle: Card subtitle
        css_class: Additional CSS classes
        border_color: Optional left border color (e.g., 'border-green-500')

    Usage:
        {% card 'Payment Details' 'Invoice #1234' '' 'border-blue-500' %}
            <!-- Card content -->
        </div>
    """
    default_class = 'bg-white rounded-lg shadow-sm p-4'
    border_class = f' border-l-4 {border_color}' if border_color else ''
    final_class = f'{default_class}{border_class} {css_class}'.strip()

    title_html = f'<h3 class="font-bold text-gray-900 mb-2">{title}</h3>' if title else ''
    subtitle_html = f'<p class="text-sm text-gray-600 mb-3">{subtitle}</p>' if subtitle else ''

    html = f'''<div class="{final_class}">
    {title_html}
    {subtitle_html}'''
    return mark_safe(html)


@register.simple_tag
def empty_state(icon='📦', title='No Items', message='', action_text='', action_call=''):
    """
    Generate an empty state message with optional action button.

    Args:
        icon: Emoji or icon
        title: Main message
        message: Detailed message
        action_text: Button text (optional)
        action_call: Nitro action to call (optional)

    Usage:
        {% empty_state '📦' 'No Items Found' 'Create your first item' '+ Create' 'toggle_create_form' %}
    """
    action_html = f'''
    <button @click="call('{action_call}')"
            class="inline-block px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition">
        {action_text}
    </button>''' if action_text and action_call else ''

    html = f'''<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
    <div class="text-4xl mb-2">{icon}</div>
    <h3 class="font-bold text-gray-900 mb-2">{title}</h3>
    {f'<p class="text-sm text-gray-600 mb-4">{message}</p>' if message else ''}
    {action_html}
</div>'''
    return mark_safe(html)
