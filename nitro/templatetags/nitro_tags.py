"""
Django Nitro 0.8 - Template tags for HTMX + Alpine.

HTMX Action Tags:
    {% nitro_search target='#list' placeholder='Buscar...' %}
    {% nitro_filter field='status' options=opts target='#list' %}
    {% nitro_pagination page_obj target='#list' %}
    {% nitro_sort 'name' 'Nombre' target='#list' %}
    {% nitro_delete url=delete_url target='#list' confirm='Eliminar?' %}

Form Tags:
    {% nitro_field form.name %}
    {% nitro_select form.category search_url='/api/search/' %}
    {% nitro_inline_create name='tenant' model_name='Inquilino' create_url='/url/' %}

Component Tags:
    {% nitro_tabs id='tabs' target='#content' %}...{% end_nitro_tabs %}
    {% nitro_modal id='my-modal' title='Titulo' %}...{% end_nitro_modal %}
    {% nitro_slideover id='panel' title='Panel' %}...{% end_nitro_slideover %}
    {% nitro_empty_state icon='🏠' title='Sin datos' %}
    {% nitro_stats_card icon='💰' label='Ingresos' value=total %}
    {% nitro_avatar user size='md' %}
    {% nitro_gallery photos=photo_list columns=3 aspect_ratio='4:3' %}
    {% nitro_inspection_checklist inspection=inspection areas=areas editable=True %}
    {% nitro_inspection_compare inspection1=move_in inspection2=move_out %}

Display Filters:
    {{ value|status_badge }}
    {{ value|priority_badge }}
    {{ amount|currency:'USD' }}
    {{ phone|phone_format }}
    {{ date|relative_date }}
    {{ uuid|truncate_id:8 }}
    {{ 3|rating }}
    {{ count|pluralize_es:'propiedad,propiedades' }}

Utility Tags:
    {% nitro_transition 'fade' %}
    {% nitro_transition 'slide-up' '200' %}
    {% nitro_key 'meta.k' "$dispatch('focus-search')" %}
"""

from django import template
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import datetime, date

register = template.Library()


# =============================================================================
# HTMX ACTION TAGS
# =============================================================================

@register.inclusion_tag('nitro/components/search_bar.html', takes_context=True)
def nitro_search(context, target='#list-content', placeholder='Buscar...', name='q'):
    """Search input with HTMX debounce."""
    request = context.get('request')
    current_value = ''
    if request:
        current_value = request.GET.get(name, '')
    return {
        'target': target,
        'placeholder': placeholder,
        'name': name,
        'current_value': current_value,
        'request_path': request.path if request else '',
    }


@register.inclusion_tag('nitro/components/filter_select.html', takes_context=True)
def nitro_filter(context, field, options, target='#list-content', label='', all_label='Todos'):
    """Filter dropdown with HTMX."""
    request = context.get('request')
    current_value = ''
    if request:
        current_value = request.GET.get(field, '')
    return {
        'field': field,
        'options': options,
        'target': target,
        'label': label,
        'all_label': all_label,
        'current_value': current_value,
        'request_path': request.path if request else '',
    }


@register.simple_tag(takes_context=True)
def nitro_delete(context, url, target='#list-content', confirm='', swap='outerHTML'):
    """Generate hx-delete attributes for a delete button."""
    attrs = f'hx-delete="{escape(url)}" hx-target="{escape(target)}" hx-swap="{escape(swap)}"'
    if confirm:
        attrs += f' hx-confirm="{escape(confirm)}"'
    return mark_safe(attrs)


@register.simple_tag(takes_context=True)
def nitro_form(context, url='', target='#list-content', method='post', swap='outerHTML', encoding=''):
    """Generate hx-* attributes for an HTMX form."""
    method_lower = method.lower()
    hx_method = f'hx-{method_lower}'
    attrs = f'{hx_method}="{escape(url)}" hx-target="{escape(target)}" hx-swap="{escape(swap)}"'
    if encoding:
        attrs += f' hx-encoding="{escape(encoding)}"'
    return mark_safe(attrs)


@register.inclusion_tag('nitro/components/pagination.html', takes_context=True)
def nitro_pagination(context, page_obj, target='#list-content'):
    """Render HTMX-powered pagination."""
    request = context.get('request')
    # Preserve current query parameters
    params = request.GET.copy() if request else {}
    params.pop('page', None)  # Remove page param, we'll add it per-link
    query_string = params.urlencode()
    return {
        'page_obj': page_obj,
        'target': target,
        'query_string': query_string,
        'request_path': request.path if request else '',
    }


@register.simple_tag(takes_context=True)
def nitro_sort(context, field, label, current_sort='', target='#list-content'):
    """Render a sort button with toggle direction."""
    request = context.get('request')
    if not current_sort and request:
        current_sort = request.GET.get('sort', '')

    # Determine next sort direction
    if current_sort == field:
        next_sort = f'-{field}'
        indicator = ' <span class="text-primary-500">&#9650;</span>'  # up arrow
    elif current_sort == f'-{field}':
        next_sort = field
        indicator = ' <span class="text-primary-500">&#9660;</span>'  # down arrow
    else:
        next_sort = field
        indicator = ''

    # Build URL preserving other params
    params = request.GET.copy() if request else {}
    params['sort'] = next_sort
    url = f'{request.path}?{params.urlencode()}' if request else f'?sort={next_sort}'

    html = (
        f'<button type="button" hx-get="{escape(url)}" hx-target="{escape(target)}" '
        f'hx-push-url="true" class="text-xs font-medium text-gray-500 hover:text-gray-700 '
        f'uppercase tracking-wider cursor-pointer">'
        f'{escape(label)}{indicator}</button>'
    )
    return mark_safe(html)


# =============================================================================
# FORM FIELD TAG
# =============================================================================

@register.inclusion_tag('nitro/components/form_field.html')
def nitro_field(field, label='', help_text='', css_class=''):
    """Render a Django form field with Tailwind styling."""
    if not hasattr(field, 'field'):
        # Not a valid BoundField — return safe defaults
        return {
            'field': field,
            'label': label or '',
            'help_text': help_text or '',
            'css_class': css_class,
            'is_required': False,
            'errors': [],
            'field_type': 'input',
        }
    return {
        'field': field,
        'label': label or field.label,
        'help_text': help_text or (field.help_text if hasattr(field, 'help_text') else ''),
        'css_class': css_class,
        'is_required': field.field.required,
        'errors': field.errors if hasattr(field, 'errors') else [],
        'field_type': _get_field_type(field),
    }


def _get_field_type(field):
    """Determine field type for styling."""
    widget_class = field.field.widget.__class__.__name__ if hasattr(field, 'field') else ''
    if widget_class in ('CheckboxInput',):
        return 'checkbox'
    if widget_class in ('Textarea',):
        return 'textarea'
    if widget_class in ('Select', 'SelectMultiple'):
        return 'select'
    if widget_class in ('FileInput', 'ClearableFileInput'):
        return 'file'
    return 'input'


@register.inclusion_tag('nitro/components/select_field.html')
def nitro_select(field, placeholder='Buscar...', search_url='', label='',
                 help_text='', css_class='', parent_input='', cascade_param='parent'):
    """
    Searchable select dropdown (like Select2).

    Usage:
        {# Client-side search (small lists) #}
        {% nitro_select form.landlord placeholder='Buscar propietario...' %}

        {# Server-side search (large lists) #}
        {% nitro_select form.municipality search_url='/geo/search/?level=6' %}

        {# Cascade: child depends on parent selection #}
        {% nitro_select form.municipality search_url='/geo/search/?level=6' parent_input='input[name="province"]' cascade_param='parent' %}
    """
    import json as _json

    # Guard: if field is not a valid BoundField, return safe defaults
    if not hasattr(field, 'field'):
        return {
            'field': field,
            'field_name': '',
            'field_id': '',
            'choices': [],
            'options_json': '[]',
            'current_value': '',
            'current_label': '',
            'placeholder': placeholder,
            'search_url': search_url,
            'parent_input': parent_input,
            'cascade_param': cascade_param,
            'label': label or '',
            'help_text': help_text or '',
            'css_class': css_class,
            'is_required': False,
            'errors': [],
        }

    choices = []
    if hasattr(field.field, 'queryset') and field.field.queryset is not None:
        choices = [(str(obj.pk), str(obj)) for obj in field.field.queryset[:200]]
    elif hasattr(field.field, 'choices'):
        choices = [(str(k), str(v)) for k, v in field.field.choices if k != '' and k is not None]
    elif hasattr(field.field.widget, 'choices'):
        # Fallback: choices set on the widget (e.g. UUIDField with Select widget)
        choices = [(str(k), str(v)) for k, v in field.field.widget.choices if k != '' and k is not None]

    current_value = ''
    current_label = ''
    raw_value = field.value()
    if raw_value:
        current_value = str(raw_value)
        for val, lbl in choices:
            if val == current_value:
                current_label = lbl
                break

    options_json = _json.dumps([{'value': v, 'label': l} for v, l in choices])

    return {
        'field': field,
        'field_name': field.html_name,
        'field_id': field.id_for_label,
        'choices': choices,
        'options_json': options_json,
        'current_value': current_value,
        'current_label': current_label,
        'placeholder': placeholder,
        'search_url': search_url,
        'parent_input': parent_input,
        'cascade_param': cascade_param,
        'label': label or field.label,
        'help_text': help_text or (field.help_text if hasattr(field, 'help_text') else ''),
        'css_class': css_class,
        'is_required': field.field.required,
        'errors': field.errors if hasattr(field, 'errors') else [],
    }


# =============================================================================
# ALPINE UI TAGS
# =============================================================================

@register.inclusion_tag('nitro/components/toast.html')
def nitro_toast():
    """Toast notification container. Include once in base.html."""
    return {}


@register.inclusion_tag('nitro/components/lazy.html', takes_context=True)
def nitro_lazy(context, url, placeholder='spinner', height='200px', trigger='revealed'):
    """
    Lazy-load a section via HTMX IntersectionObserver.

    Usage:
        {% nitro_lazy url='/leasing/dashboard-stats/' placeholder='skeleton' height='120px' %}
    """
    return {
        'url': url,
        'placeholder': placeholder,
        'height': height,
        'trigger': trigger,
    }


@register.simple_tag
def nitro_scripts():
    """Include HTMX, nitro.js, and alpine-components.js scripts."""
    from django.templatetags.static import static
    import time
    # Cache busting version (change when JS is updated)
    v = '0.8.0-beta'
    nitro_js = static('nitro/nitro.js')
    alpine_js = static('nitro/alpine-components.js')
    html = (
        f'<script src="https://unpkg.com/htmx.org@2.0.4"></script>\n'
        f'<script src="https://unpkg.com/idiomorph@0.3.0/dist/idiomorph-ext.min.js"></script>\n'
        f'<script>htmx.config.defaultSwapStyle = "morph";</script>\n'
        f'<script src="{nitro_js}?v={v}"></script>\n'
        f'<script src="{alpine_js}?v={v}"></script>'
    )
    return mark_safe(html)


@register.simple_tag
def nitro_open_modal(modal_id):
    """Generate Alpine attributes to open a modal."""
    return mark_safe(
        f"@click=\"$dispatch('open-modal', '{escape(modal_id)}')\" "
        f"type=\"button\""
    )


@register.simple_tag
def nitro_close_modal(modal_id=''):
    """Generate Alpine attributes to close a modal."""
    if modal_id:
        return mark_safe(f"@click=\"$dispatch('close-modal', '{escape(modal_id)}')\" type=\"button\"")
    return mark_safe("@click=\"open = false\" type=\"button\"")


@register.inclusion_tag('nitro/components/confirm.html')
def nitro_confirm():
    """Confirm dialog. Include once in base.html."""
    return {}


@register.inclusion_tag('nitro/components/empty_state.html')
def nitro_empty(icon='', title='', message='', action_text='', action_url='', action_click=''):
    """Empty state placeholder."""
    return {
        'icon': icon,
        'title': title,
        'message': message,
        'action_text': action_text,
        'action_url': action_url,
        'action_click': action_click,
    }


# =============================================================================
# BLOCK TAG: nitro_modal / end_nitro_modal
# =============================================================================

class NitroModalNode(template.Node):
    """Renders a modal wrapper around child content."""

    def __init__(self, nodelist, modal_id, title, size):
        self.nodelist = nodelist
        self.modal_id = modal_id
        self.title = title
        self.size = size

    def render(self, context):
        modal_id = self.modal_id.resolve(context) if hasattr(self.modal_id, 'resolve') else self.modal_id
        title = self.title.resolve(context) if hasattr(self.title, 'resolve') else self.title
        size = self.size.resolve(context) if hasattr(self.size, 'resolve') else self.size

        inner_content = self.nodelist.render(context)

        size_class = {
            'sm': 'max-w-md',
            'md': 'max-w-lg',
            'lg': 'max-w-2xl',
            'xl': 'max-w-4xl',
        }.get(size, 'max-w-lg')

        return (
            f'<div x-data="nitroModal(\'{escape(modal_id)}\')" '
            f'x-show="open" x-cloak '
            f'class="fixed inset-0 z-50 overflow-y-auto" '
            f'@open-modal.window="if ($event.detail === \'{escape(modal_id)}\') open = true" '
            f'@close-modal.window="if ($event.detail === \'{escape(modal_id)}\') open = true; open = false">\n'
            f'  <div class="flex items-center justify-center min-h-screen px-4 py-6">\n'
            f'    <div x-show="open" x-transition:enter="ease-out duration-200" '
            f'x-transition:enter-start="opacity-0" x-transition:enter-end="opacity-100" '
            f'x-transition:leave="ease-in duration-150" x-transition:leave-start="opacity-100" '
            f'x-transition:leave-end="opacity-0" '
            f'@click="open = false" class="fixed inset-0 bg-gray-500/75"></div>\n'
            f'    <div x-show="open" x-transition:enter="ease-out duration-200" '
            f'x-transition:enter-start="opacity-0 translate-y-4 sm:scale-95" '
            f'x-transition:enter-end="opacity-100 translate-y-0 sm:scale-100" '
            f'x-transition:leave="ease-in duration-150" '
            f'x-transition:leave-start="opacity-100 translate-y-0 sm:scale-100" '
            f'x-transition:leave-end="opacity-0 translate-y-4 sm:scale-95" '
            f'@click.stop class="relative bg-white rounded-lg shadow-xl {size_class} w-full p-6">\n'
            f'      <div class="flex items-center justify-between mb-4">\n'
            f'        <h3 class="text-lg font-semibold text-gray-900">{escape(title)}</h3>\n'
            f'        <button @click="open = false" type="button" class="text-gray-400 hover:text-gray-600">\n'
            f'          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>'
            f'</svg>\n'
            f'        </button>\n'
            f'      </div>\n'
            f'      {inner_content}\n'
            f'    </div>\n'
            f'  </div>\n'
            f'</div>'
        )


@register.tag('nitro_modal')
def do_nitro_modal(parser, token):
    """
    Block tag for modal dialogs.

    Usage:
        {% nitro_modal id='create-property' title='Nueva Propiedad' %}
            <form>...</form>
        {% end_nitro_modal %}

    With variable title:
        {% trans "Nueva Propiedad" as modal_title %}
        {% nitro_modal id='create-property' title=modal_title %}
    """
    bits = token.split_contents()
    tag_name = bits[0]

    # Parse keyword arguments
    kwargs = {}
    for bit in bits[1:]:
        if '=' in bit:
            key, val = bit.split('=', 1)
            val_clean = val.strip("'\"")
            if val.startswith("'") or val.startswith('"'):
                # String literal
                kwargs[key] = val_clean
            else:
                # Variable reference
                kwargs[key] = template.Variable(val_clean)

    modal_id = kwargs.get('id', 'modal')
    title = kwargs.get('title', '')
    size = kwargs.get('size', 'md')

    nodelist = parser.parse(('end_nitro_modal',))
    parser.delete_first_token()

    return NitroModalNode(nodelist, modal_id, title, size)


# =============================================================================
# BLOCK TAG: nitro_slideover / end_nitro_slideover
# =============================================================================

class NitroSlideoverNode(template.Node):
    """Renders a slide-over panel (right-side drawer) around child content."""

    def __init__(self, nodelist, slideover_id, title, size):
        self.nodelist = nodelist
        self.slideover_id = slideover_id
        self.title = title
        self.size = size

    def render(self, context):
        sid = self.slideover_id.resolve(context) if hasattr(self.slideover_id, 'resolve') else self.slideover_id
        title = self.title.resolve(context) if hasattr(self.title, 'resolve') else self.title
        size = self.size.resolve(context) if hasattr(self.size, 'resolve') else self.size

        inner_content = self.nodelist.render(context)

        size_class = {
            'sm': 'max-w-sm',
            'md': 'max-w-md',
            'lg': 'max-w-lg',
            'xl': 'max-w-2xl',
        }.get(size, 'max-w-lg')

        return (
            f'<div x-data="nitroSlideover(\'{escape(sid)}\')" '
            f'x-show="open" x-cloak '
            f'class="fixed inset-0 z-50 overflow-hidden">\n'
            # Backdrop
            f'  <div x-show="open" '
            f'x-transition:enter="ease-out duration-300" '
            f'x-transition:enter-start="opacity-0" '
            f'x-transition:enter-end="opacity-100" '
            f'x-transition:leave="ease-in duration-200" '
            f'x-transition:leave-start="opacity-100" '
            f'x-transition:leave-end="opacity-0" '
            f'@click="open = false" '
            f'class="fixed inset-0 bg-gray-500/75"></div>\n'
            # Panel - mobile: full screen, desktop: right sidebar
            f'  <div class="fixed inset-y-0 right-0 flex {size_class} w-full max-h-screen">\n'
            f'    <div x-show="open" '
            f'x-transition:enter="transform transition ease-out duration-300" '
            f'x-transition:enter-start="translate-x-full" '
            f'x-transition:enter-end="translate-x-0" '
            f'x-transition:leave="transform transition ease-in duration-200" '
            f'x-transition:leave-start="translate-x-0" '
            f'x-transition:leave-end="translate-x-full" '
            f'class="relative w-full bg-white shadow-xl flex flex-col max-h-screen">\n'
            # Header - fixed at top
            f'      <div class="flex-shrink-0 flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200">\n'
            f'        <h2 class="text-base sm:text-lg font-semibold text-gray-900 truncate pr-2">{escape(title)}</h2>\n'
            f'        <button @click="open = false" type="button" '
            f'class="flex-shrink-0 text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100">\n'
            f'          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">'
            f'<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>'
            f'</svg>\n'
            f'        </button>\n'
            f'      </div>\n'
            # Body - scrollable with safe area for mobile
            f'      <div class="flex-1 overflow-y-auto overscroll-contain px-4 sm:px-6 py-4 pb-safe">\n'
            f'        {inner_content}\n'
            f'      </div>\n'
            f'    </div>\n'
            f'  </div>\n'
            f'</div>'
        )


@register.tag('nitro_slideover')
def do_nitro_slideover(parser, token):
    """
    Block tag for slide-over panels.

    Usage:
        {% nitro_slideover id='create-lease' title='Nuevo Contrato' size='lg' %}
            <form>...</form>
        {% end_nitro_slideover %}

    With variable title (for i18n):
        {% trans "Nuevo Contrato" as slideover_title %}
        {% nitro_slideover id='create-lease' title=slideover_title size='lg' %}
    """
    bits = token.split_contents()

    kwargs = {}
    for bit in bits[1:]:
        if '=' in bit:
            key, val = bit.split('=', 1)
            val_clean = val.strip("'\"")
            if val.startswith("'") or val.startswith('"'):
                # String literal
                kwargs[key] = val_clean
            else:
                # Variable reference
                kwargs[key] = template.Variable(val_clean)

    slideover_id = kwargs.get('id', 'slideover')
    title = kwargs.get('title', '')
    size = kwargs.get('size', 'md')

    nodelist = parser.parse(('end_nitro_slideover',))
    parser.delete_first_token()

    return NitroSlideoverNode(nodelist, slideover_id, title, size)


@register.simple_tag
def nitro_open_slideover(slideover_id):
    """Generate attributes to open a slide-over."""
    return mark_safe(
        f"onclick=\"Nitro.openSlideover('{escape(slideover_id)}')\" "
        f"type=\"button\""
    )


@register.simple_tag
def nitro_close_slideover(slideover_id=''):
    """Generate attributes to close a slide-over."""
    if slideover_id:
        return mark_safe(f"onclick=\"Nitro.closeSlideover('{escape(slideover_id)}')\" type=\"button\"")
    return mark_safe("@click=\"open = false\" type=\"button\"")


# =============================================================================
# EDIT FORM BLOCK TAG
# =============================================================================

class NitroEditFormNode(template.Node):
    """Renders a form with proper HTMX attributes for edit slidelovers."""

    def __init__(self, nodelist, url_name, slideover, pk_var):
        self.nodelist = nodelist
        self.url_name = url_name
        self.slideover = slideover
        self.pk_var = pk_var

    def render(self, context):
        from django.urls import reverse

        # Resolve URL
        url_name = self.url_name.resolve(context) if hasattr(self.url_name, 'resolve') else self.url_name
        slideover = self.slideover.resolve(context) if hasattr(self.slideover, 'resolve') else self.slideover

        # Get pk from object in context or from explicit pk variable
        if self.pk_var:
            pk = self.pk_var.resolve(context)
        else:
            obj = context.get('object')
            pk = obj.pk if obj else ''

        # Build URL
        try:
            url = reverse(url_name, kwargs={'pk': pk})
        except Exception:
            url = ''

        inner_content = self.nodelist.render(context)

        # Get CSRF token
        from django.middleware.csrf import get_token
        request = context.get('request')
        csrf_token = get_token(request) if request else ''

        return (
            f'<form hx-post="{escape(url)}" hx-target="this" hx-swap="outerHTML">\n'
            f'  <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">\n'
            f'  <input type="hidden" name="_slideover" value="{escape(slideover)}">\n'
            f'  {inner_content}\n'
            f'</form>'
        )


@register.tag('nitro_edit_form')
def do_nitro_edit_form(parser, token):
    """
    Block tag for edit forms in slidelovers.

    Automatically handles:
    - HTMX post with proper swap behavior
    - CSRF token
    - Form validation error display (re-renders form on error)

    Usage (uses object.pk from context)::

        {% nitro_edit_form 'leasing:property_update' slideover='edit-property' %}
            {% include "leasing/partials/property_form.html" with is_edit=True %}
        {% end_nitro_edit_form %}

    With explicit pk::

        {% nitro_edit_form 'leasing:property_update' pk=object.id slideover='edit-property' %}
            ...
        {% end_nitro_edit_form %}
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise template.TemplateSyntaxError(
            "nitro_edit_form requires at least a URL name argument"
        )

    url_name = bits[1].strip("'\"")
    kwargs = {}
    for bit in bits[2:]:
        if '=' in bit:
            key, val = bit.split('=', 1)
            val_clean = val.strip("'\"")
            if val_clean != val.strip():
                # Was quoted - it's a literal
                kwargs[key] = val_clean
            else:
                # Variable reference
                kwargs[key] = template.Variable(val_clean)

    slideover = kwargs.get('slideover', 'edit-item')
    pk_var = kwargs.get('pk')

    nodelist = parser.parse(('end_nitro_edit_form',))
    parser.delete_first_token()

    return NitroEditFormNode(nodelist, url_name, slideover, pk_var)


# =============================================================================
# FORM FOOTER TAG
# =============================================================================

@register.inclusion_tag('nitro/components/form_footer.html', takes_context=True)
def nitro_form_footer(context, slideover='', label='', cancel_label='Cancelar'):
    """
    Render form error block + cancel/submit footer.

    Usage::

        {% nitro_form_footer slideover='create-property' label='Crear Propiedad' %}
        {% nitro_form_footer slideover='edit-property' label='Guardar Cambios' %}
    """
    form = context.get('form')
    if not label:
        label = 'Guardar Cambios' if context.get('is_edit') else 'Guardar'
    return {
        'form': form,
        'slideover': slideover,
        'label': label,
        'cancel_label': cancel_label,
    }


# =============================================================================
# CASCADE TAG (for HTMX cascading dropdowns)
# =============================================================================

@register.simple_tag
def nitro_cascade(url, child_target, include_self=True):
    """
    Generate HTMX attributes for a cascading dropdown.
    Place on the parent <select> element.

    Usage:
        <select name="province" {% nitro_cascade url='/geo/options/?level=6' child_target='#id_municipality' %}>
            ...
        </select>

    When the parent select changes, HTMX fetches new <option> elements
    from the URL and swaps them into the child target.
    """
    attrs = (
        f'hx-get="{escape(url)}" '
        f'hx-trigger="change" '
        f'hx-target="{escape(child_target)}" '
        f'hx-swap="innerHTML"'
    )
    if include_self:
        attrs += ' hx-include="this"'
    return mark_safe(attrs)


# =============================================================================
# DISPLAY / FORMAT FILTERS
# =============================================================================

@register.filter
def currency(value, currency_code=None):
    """
    Format number as currency.

    Usage: {{ amount|currency }} or {{ amount|currency:'USD' }}

    Default currency is configured via NITRO_DEFAULT_CURRENCY setting.
    """
    from nitro.utils.currency import format_currency as _fmt
    return _fmt(value, currency_code)


@register.filter
def status_badge(value, mapping=''):
    """
    Render a status badge with colors.

    Usage: {{ item.status|status_badge }}
    Or with mapping: {{ item.status|status_badge:"active:green,draft:gray,expired:red" }}
    """
    # Default color mappings
    color_map = {
        # Lease/general status
        'active': ('Activo', 'green'),
        'draft': ('Borrador', 'gray'),
        'expired': ('Vencido', 'red'),
        'cancelled': ('Cancelado', 'red'),
        'pending': ('Pendiente', 'yellow'),
        'completed': ('Completado', 'green'),
        # Property status
        'available': ('Disponible', 'green'),
        'rented': ('Alquilada', 'blue'),
        'maintenance_only': ('Solo Mantenimiento', 'yellow'),
        'occupied': ('Ocupada', 'purple'),
        # Payment status
        'paid': ('Pagado', 'green'),
        'overdue': ('Atrasado', 'red'),
        'partial': ('Parcial', 'yellow'),
        # Work order status
        'scheduled': ('Programado', 'blue'),
        'in_progress': ('En Progreso', 'blue'),
        # Approval
        'approved': ('Aprobado', 'green'),
        'rejected': ('Rechazado', 'red'),
        # Inspection
        'move_in': ('Entrada', 'blue'),
        'move_out': ('Salida', 'purple'),
        'routine': ('Rutina', 'gray'),
        'damage': ('Daños', 'red'),
        # Renewal
        'proposed': ('Propuesto', 'blue'),
        'negotiating': ('En Negociación', 'yellow'),
        'accepted': ('Aceptado', 'green'),
        # Deposit
        'received': ('Recibido', 'green'),
        'deduction': ('Deducción', 'red'),
        'refund': ('Devolución', 'yellow'),
    }

    # Parse custom mapping if provided
    if mapping:
        for pair in mapping.split(','):
            parts = pair.strip().split(':')
            if len(parts) == 2:
                color_map[parts[0].strip()] = (parts[0].strip(), parts[1].strip())

    str_value = str(value).lower().strip() if value else ''
    label, color = color_map.get(str_value, (str(value), 'gray'))

    color_classes = {
        'green': 'bg-green-100 text-green-800',
        'red': 'bg-red-100 text-red-800',
        'yellow': 'bg-yellow-100 text-yellow-800',
        'blue': 'bg-blue-100 text-blue-800',
        'purple': 'bg-purple-100 text-purple-800',
        'gray': 'bg-gray-100 text-gray-800',
    }
    classes = color_classes.get(color, 'bg-gray-100 text-gray-800')

    return mark_safe(
        f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {classes}">'
        f'{escape(label)}</span>'
    )


@register.filter
def phone_format(value):
    """Format phone number: (809) 555-1234"""
    if not value:
        return ''
    digits = ''.join(c for c in str(value) if c.isdigit())
    if len(digits) == 10:
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
    if len(digits) == 11 and digits[0] == '1':
        return f'+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}'
    return str(value)


@register.filter
def truncate_id(value, length=8):
    """Truncate UUID for display."""
    s = str(value)
    return s[:length] if len(s) > length else s


@register.filter
def priority_badge(value):
    """
    Render a priority badge with colors.

    Usage: {{ ticket.priority|priority_badge }}
    """
    priority_map = {
        'low': ('Baja', 'gray'),
        'medium': ('Media', 'yellow'),
        'high': ('Alta', 'orange'),
        'urgent': ('Urgente', 'red'),
    }

    str_value = str(value).lower().strip() if value else ''
    label, color = priority_map.get(str_value, (str(value), 'gray'))

    color_classes = {
        'gray': 'bg-gray-100 text-gray-800',
        'yellow': 'bg-yellow-100 text-yellow-800',
        'orange': 'bg-orange-100 text-orange-800',
        'red': 'bg-red-100 text-red-800',
    }
    classes = color_classes.get(color, 'bg-gray-100 text-gray-800')

    return mark_safe(
        f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {classes}">'
        f'{escape(label)}</span>'
    )


# =============================================================================
# TABS TAG (HTMX-powered tab navigation)
# =============================================================================

class NitroTabsNode(template.Node):
    """Renders HTMX-powered tab navigation."""

    def __init__(self, nodelist, tabs_id, target):
        self.nodelist = nodelist
        self.tabs_id = tabs_id
        self.target = target

    def render(self, context):
        tabs_id = self.tabs_id.resolve(context) if hasattr(self.tabs_id, 'resolve') else self.tabs_id
        target = self.target.resolve(context) if hasattr(self.target, 'resolve') else self.target

        # Collect tabs from context set by nitro_tab tags
        context['_nitro_tabs'] = []
        context['_nitro_tabs_target'] = target
        self.nodelist.render(context)
        tabs = context.get('_nitro_tabs', [])

        if not tabs:
            return ''

        request = context.get('request')
        current_tab = request.GET.get('tab', '') if request else ''
        request_path = request.path if request else ''

        # If no tab matches current, default to first or the one marked active
        active_tab = current_tab
        if not active_tab:
            for tab in tabs:
                if tab.get('active'):
                    active_tab = tab['name']
                    break
            if not active_tab and tabs:
                active_tab = tabs[0]['name']

        html_parts = [
            f'<div id="{escape(tabs_id)}" class="border-b border-gray-200 mb-4">',
            '  <nav class="-mb-px flex space-x-6 overflow-x-auto" aria-label="Tabs">',
        ]
        for tab in tabs:
            is_active = tab['name'] == active_tab
            active_classes = 'border-primary-500 text-primary-600' if is_active else 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            url = f'{request_path}?tab={escape(tab["name"])}'
            html_parts.append(
                f'    <button type="button" '
                f'hx-get="{url}" hx-target="{escape(target)}" hx-push-url="true" '
                f'class="whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm {active_classes}">'
                f'{escape(tab["label"])}</button>'
            )
        html_parts.append('  </nav>')
        html_parts.append('</div>')

        return '\n'.join(html_parts)


@register.tag('nitro_tabs')
def do_nitro_tabs(parser, token):
    """
    Block tag for HTMX tab navigation.

    Usage:
        {% nitro_tabs id='property-tabs' target='#tab-content' %}
            {% nitro_tab name='info' label='Información' active=True %}
            {% nitro_tab name='leases' label='Contratos' %}
            {% nitro_tab name='photos' label='Fotos' %}
        {% end_nitro_tabs %}
    """
    bits = token.split_contents()
    kwargs = {}
    for bit in bits[1:]:
        if '=' in bit:
            key, val = bit.split('=', 1)
            val = val.strip("'\"")
            kwargs[key] = val

    tabs_id = kwargs.get('id', 'tabs')
    target = kwargs.get('target', '#tab-content')

    nodelist = parser.parse(('end_nitro_tabs',))
    parser.delete_first_token()

    return NitroTabsNode(nodelist, tabs_id, target)


@register.simple_tag(takes_context=True)
def nitro_tab(context, name='', label='', active=False):
    """Register a tab within a nitro_tabs block. Does not render anything."""
    tabs = context.get('_nitro_tabs')
    if tabs is not None:
        tabs.append({'name': name, 'label': label, 'active': active})
    return ''


# =============================================================================
# DATE INPUT TAG
# =============================================================================

@register.simple_tag(takes_context=True)
def nitro_date_input(context, name, value='', target='#list-content', label='', css_class='', auto_submit=False):
    """
    Date input for filtering.

    Usage:
        {% nitro_date_input name='period_start' value=period_start label='Desde' %}
        {% nitro_date_input name='start' value=start auto_submit=True %}  {# Auto-submits on change #}

    Args:
        auto_submit: If True, triggers HTMX request on change. Default False to prevent loops.
    """
    request = context.get('request')
    if not value and request:
        value = request.GET.get(name, '')
    request_path = request.path if request else ''

    label_html = ''
    if label:
        label_html = f'<label for="id_{escape(name)}" class="block text-sm font-medium text-gray-700 mb-1">{escape(label)}</label>'

    extra_class = f' {css_class}' if css_class else ''

    # Only add hx-* attrs if auto_submit is enabled (prevents infinite loops)
    htmx_attrs = ''
    if auto_submit:
        htmx_attrs = f'hx-get="{request_path}" hx-trigger="change" hx-target="{escape(target)}" hx-include=".nitro-filter-input" hx-push-url="true" '

    html = (
        f'{label_html}'
        f'<input type="date" id="id_{escape(name)}" name="{escape(name)}" value="{escape(value)}" '
        f'{htmx_attrs}'
        f'class="nitro-filter-input px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 '
        f'focus:ring-primary-500 focus:border-primary-500{extra_class}">'
    )
    return mark_safe(html)


# =============================================================================
# ADDITIONAL COMPONENT TAGS
# =============================================================================

@register.inclusion_tag('nitro/components/stats_card.html')
def nitro_stats_card(icon='', label='', value='', change='', change_type='neutral', href=''):
    """
    Stats card for dashboards.

    Usage:
        {% nitro_stats_card icon='💰' label='Ingresos' value=total change='+12%' change_type='positive' %}
    """
    return {
        'icon': icon,
        'label': label,
        'value': value,
        'change': change,
        'change_type': change_type,  # 'positive', 'negative', 'neutral'
        'href': href,
    }


@register.inclusion_tag('nitro/components/avatar.html')
def nitro_avatar(user=None, name='', image_url='', size='md'):
    """
    User avatar with initials fallback.

    Usage:
        {% nitro_avatar user size='md' %}
        {% nitro_avatar name='Juan Perez' size='lg' %}
    """
    if user:
        name = user.get_full_name() or getattr(user, 'username', '')
        image_url = getattr(user, 'avatar_url', '') or ''

    initials = ''.join([n[0].upper() for n in name.split()[:2]]) if name else '?'

    sizes = {
        'xs': 'w-6 h-6 text-xs',
        'sm': 'w-8 h-8 text-sm',
        'md': 'w-10 h-10 text-base',
        'lg': 'w-12 h-12 text-lg',
        'xl': 'w-16 h-16 text-xl',
    }

    return {
        'name': name,
        'image_url': image_url,
        'initials': initials,
        'size_class': sizes.get(size, sizes['md']),
    }


@register.inclusion_tag('nitro/components/export_buttons.html', takes_context=True)
def nitro_export_buttons(context, label='Exportar'):
    """
    Render CSV/Excel export buttons that preserve current filters.

    Usage:
        {% nitro_export_buttons %}
    """
    request = context.get('request')
    params = request.GET.copy() if request else {}
    params.pop('export', None)
    return {
        'label': label,
        'query_string': params.urlencode(),
        'request': request,
    }


@register.inclusion_tag('nitro/components/detail_tabs.html', takes_context=True)
def nitro_detail_tabs(context, target='#tab-content'):
    """
    Render declarative tabs for NitroModelView detail views.

    Usage:
        {% nitro_detail_tabs target='#tab-content' %}
        <div id="tab-content">{% include active_tab_template %}</div>
    """
    return {
        'tabs': context.get('tabs', []),
        'target': target,
        'request': context.get('request'),
    }


@register.inclusion_tag('nitro/components/empty_state.html')
def nitro_empty_state(icon='', title='No hay datos', message='', action_text='', action_url='', action_click=''):
    """
    Empty state placeholder (alias for nitro_empty with better defaults).

    Usage:
        {% nitro_empty_state icon='🏠' title='Sin propiedades' message='Agrega tu primera propiedad' action_text='Crear' action_url='/leasing/properties/new/' %}
    """
    return {
        'icon': icon,
        'title': title,
        'message': message,
        'action_text': action_text,
        'action_url': action_url,
        'action_click': action_click,
    }


# =============================================================================
# ADDITIONAL DISPLAY FILTERS
# =============================================================================

@register.inclusion_tag('nitro/components/file_upload.html')
def nitro_file_upload(upload_url='', field_name='file', accept='', multiple=False,
                      label='', hint='', icon='photo', max_size_mb=10,
                      refresh_target='', refresh_tab='', **kwargs):
    """
    Reusable drag-and-drop file upload component.

    Usage:
        {# Photo upload with auto-submit to endpoint #}
        {% nitro_file_upload upload_url='/leasing/upload-property-photos/' field_name='photos' accept='image/*' multiple=True extra_property_id=property.id %}

        {# Document upload (single file) #}
        {% nitro_file_upload upload_url=upload_url field_name='file' icon='document' accept='.pdf,.doc,.docx' %}

        {# File input for a form (no auto-upload, just file selection) #}
        {% nitro_file_upload field_name='photos' accept='image/*' multiple=True %}
    """
    if not label:
        label = 'Arrastra archivos aqui o haz clic para seleccionar' if multiple else 'Arrastra un archivo aqui o haz clic para seleccionar'
    if not hint:
        hint = f'Maximo {max_size_mb} MB por archivo.'
    return {
        'upload_url': upload_url,
        'field_name': field_name,
        'accept': accept,
        'multiple': multiple,
        'label': label,
        'hint': hint,
        'icon': icon,
        'max_size_mb': max_size_mb,
        'refresh_target': refresh_target,
        'refresh_tab': refresh_tab,
        'extra_fields': kwargs,
    }


@register.inclusion_tag('nitro/components/image_cropper.html')
def nitro_image_cropper(name, current_image='', aspect_ratio='1:1', min_width=100,
                        max_size_mb=5, preview_size='150px', label='', help_text='',
                        required=False):
    """
    Image cropper with Cropper.js for selecting and cropping images.

    Lazy-loads Cropper.js from CDN. Stores cropped result as base64 in hidden input.

    Usage:
        {# Basic avatar upload with 1:1 ratio #}
        {% nitro_image_cropper name='avatar' label='Foto de perfil' %}

        {# Cover image with 16:9 ratio #}
        {% nitro_image_cropper name='cover' aspect_ratio='16:9' preview_size='300px' %}

        {# Free-form cropping #}
        {% nitro_image_cropper name='photo' aspect_ratio='free' label='Foto' %}

        {# With existing image #}
        {% nitro_image_cropper name='avatar' current_image=user.avatar_url aspect_ratio='1:1' %}

    Args:
        name: Form field name for the hidden input containing base64 data
        current_image: URL or base64 of current image to display
        aspect_ratio: '1:1', '16:9', '4:3', or 'free' for no constraint
        min_width: Minimum width of cropped image in pixels
        max_size_mb: Maximum file size in MB
        preview_size: CSS size for preview (e.g., '150px', '200px')
        label: Label text above the component
        help_text: Help text below the component
        required: Whether field is required (shows asterisk)

    Events dispatched:
        - image-cropped: When crop is applied, with { data: base64String }
        - image-cleared: When image is removed
    """
    return {
        'name': name,
        'current_image': current_image or '',
        'aspect_ratio': aspect_ratio,
        'min_width': min_width,
        'max_size_mb': max_size_mb,
        'preview_size': preview_size,
        'label': label,
        'help_text': help_text,
        'required': required,
    }


@register.filter
def relative_date(value):
    """
    Show relative date in Spanish (hoy, ayer, hace X dias).

    Usage: {{ some_date|relative_date }}
    """
    from nitro.utils.dates import relative_date as _rel
    return _rel(value)


# =============================================================================
# TRANSITION PRESETS
# =============================================================================

@register.simple_tag
def nitro_transition(preset='fade', duration='300'):
    """
    Named transition presets for Alpine.js.

    Usage:
        <div x-show="open" {% nitro_transition 'fade' %}>...</div>
        <div x-show="open" {% nitro_transition 'slide-up' %}>...</div>
        <div x-show="open" {% nitro_transition 'scale' '200' %}>...</div>
    """
    presets = {
        'fade': {
            'enter': f'transition ease-out duration-{duration}',
            'enter_start': 'opacity-0',
            'enter_end': 'opacity-100',
            'leave': f'transition ease-in duration-{duration}',
            'leave_start': 'opacity-100',
            'leave_end': 'opacity-0',
        },
        'slide-up': {
            'enter': f'transition ease-out duration-{duration}',
            'enter_start': 'opacity-0 translate-y-4',
            'enter_end': 'opacity-100 translate-y-0',
            'leave': f'transition ease-in duration-{duration}',
            'leave_start': 'opacity-100 translate-y-0',
            'leave_end': 'opacity-0 translate-y-4',
        },
        'slide-down': {
            'enter': f'transition ease-out duration-{duration}',
            'enter_start': 'opacity-0 -translate-y-4',
            'enter_end': 'opacity-100 translate-y-0',
            'leave': f'transition ease-in duration-{duration}',
            'leave_start': 'opacity-100 translate-y-0',
            'leave_end': 'opacity-0 -translate-y-4',
        },
        'slide-right': {
            'enter': f'transform transition ease-out duration-{duration}',
            'enter_start': 'translate-x-full',
            'enter_end': 'translate-x-0',
            'leave': f'transform transition ease-in duration-{duration}',
            'leave_start': 'translate-x-0',
            'leave_end': 'translate-x-full',
        },
        'slide-left': {
            'enter': f'transform transition ease-out duration-{duration}',
            'enter_start': '-translate-x-full',
            'enter_end': 'translate-x-0',
            'leave': f'transform transition ease-in duration-{duration}',
            'leave_start': 'translate-x-0',
            'leave_end': '-translate-x-full',
        },
        'scale': {
            'enter': f'transition ease-out duration-{duration}',
            'enter_start': 'opacity-0 scale-95',
            'enter_end': 'opacity-100 scale-100',
            'leave': f'transition ease-in duration-{duration}',
            'leave_start': 'opacity-100 scale-100',
            'leave_end': 'opacity-0 scale-95',
        },
    }

    p = presets.get(preset, presets['fade'])

    attrs = (
        f'x-transition:enter="{p["enter"]}" '
        f'x-transition:enter-start="{p["enter_start"]}" '
        f'x-transition:enter-end="{p["enter_end"]}" '
        f'x-transition:leave="{p["leave"]}" '
        f'x-transition:leave-start="{p["leave_start"]}" '
        f'x-transition:leave-end="{p["leave_end"]}"'
    )
    return mark_safe(attrs)


# =============================================================================
# RATING FILTER
# =============================================================================

@register.filter
def rating(value, max_stars=5):
    """
    Display star rating as SVG stars.

    Usage:
        {{ 3|rating }}        → ★★★☆☆
        {{ 4.5|rating }}      → ★★★★½
        {{ 2|rating:10 }}     → ★★☆☆☆☆☆☆☆☆
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0

    try:
        max_stars = int(max_stars)
    except (TypeError, ValueError):
        max_stars = 5

    full = int(value)
    has_half = (value - full) >= 0.5
    empty = max_stars - full - (1 if has_half else 0)

    star_filled = (
        '<svg class="w-4 h-4 text-amber-400 inline-block" fill="currentColor" viewBox="0 0 20 20">'
        '<path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>'
        '</svg>'
    )
    star_half = (
        '<svg class="w-4 h-4 text-amber-400 inline-block" fill="currentColor" viewBox="0 0 20 20">'
        '<defs><linearGradient id="half"><stop offset="50%" stop-color="currentColor"/>'
        '<stop offset="50%" stop-color="#D1D5DB"/></linearGradient></defs>'
        '<path fill="url(#half)" d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>'
        '</svg>'
    )
    star_empty = (
        '<svg class="w-4 h-4 text-gray-300 inline-block" fill="currentColor" viewBox="0 0 20 20">'
        '<path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>'
        '</svg>'
    )

    stars = star_filled * full
    if has_half:
        stars += star_half
    stars += star_empty * empty

    return mark_safe(f'<span class="nitro-rating inline-flex items-center">{stars}</span>')


# =============================================================================
# DECLARATIVE TABLE TAGS & FILTERS
# =============================================================================

@register.filter
def table_cell(obj, column):
    """Resolve a column value from an object and apply display formatting.

    Usage in template: {{ obj|table_cell:column }}
    """
    from nitro.tables import get_field_value
    value = get_field_value(obj, column.field)

    if value is None:
        return mark_safe('<span class="text-gray-400">—</span>')

    display = column.display
    if display == 'currency':
        currency_code = None  # Will use NITRO_DEFAULT_CURRENCY setting
        if column.currency_field:
            currency_code = get_field_value(obj, column.currency_field)
        return currency(value, currency_code)
    elif display == 'status_badge':
        return status_badge(value)
    elif display == 'priority_badge':
        return priority_badge(value)
    elif display == 'phone_format':
        return phone_format(value)
    elif display == 'relative_date':
        return relative_date(value)
    elif display == 'truncate_id':
        return truncate_id(value)

    return escape(str(value))


@register.filter
def resolve_url(obj, url_name):
    """Resolve a Django URL with the object's pk.

    Usage in template: {{ obj|resolve_url:'leasing:property_detail' }}
    """
    from django.urls import reverse
    try:
        return reverse(url_name, args=[obj.pk])
    except Exception:
        return '#'


@register.filter
def get_subtitle(obj, column):
    """Get the subtitle field value for a column.

    Usage in template: {{ obj|get_subtitle:column }}
    """
    if not column.subtitle_field:
        return ''
    from nitro.tables import get_field_value
    value = get_field_value(obj, column.subtitle_field)
    return escape(str(value)) if value else ''


@register.filter
def has_icon_field(obj, column):
    """Check if the object has a truthy value for the column's icon_field.

    Usage in template: {{ obj|has_icon_field:column }}
    """
    if not column.icon_field:
        return False
    from nitro.tables import get_field_value
    value = get_field_value(obj, column.icon_field)
    return bool(value)


@register.filter
def quick_action_visible(obj, action):
    """Check if a quick action should be visible for the given object.

    Usage in template: {{ obj|quick_action_visible:action }}
    """
    return action.is_visible(obj)


@register.filter
def quick_action_url(obj, action):
    """Get the external URL for a quick action (e.g., WhatsApp link).

    Usage in template: {{ obj|quick_action_url:action }}
    """
    return action.get_url(obj)


@register.simple_tag
def quick_action_icon(icon_name):
    """Render the SVG icon for a quick action.

    Usage in template: {% quick_action_icon action.icon %}
    """
    from nitro.tables import QUICK_ACTION_ICONS
    svg_path = QUICK_ACTION_ICONS.get(icon_name, '')
    if not svg_path:
        # Fallback: generic circle icon
        svg_path = '<circle cx="12" cy="12" r="3" fill="currentColor"/>'
    return mark_safe(f'<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none">{svg_path}</svg>')


@register.inclusion_tag('nitro/components/table.html', takes_context=True)
def nitro_table(context, target='#list-content'):
    """
    Render a declarative table with desktop/mobile views from NitroListView context.

    Reads columns, row_actions, quick_actions, object_list, and page_obj from the template context.

    Usage:
        {% nitro_table target='#list-content' %}
    """
    return {
        'columns': context.get('columns', []),
        'row_actions': context.get('row_actions', []),
        'quick_actions': context.get('quick_actions', []),
        'object_list': context.get('object_list', []),
        'page_obj': context.get('page_obj'),
        'target': target,
        'request': context.get('request'),
        'current_sort': context.get('current_sort', ''),
    }


# =============================================================================
# KEYBOARD SHORTCUT TAG
# =============================================================================

@register.inclusion_tag('nitro/components/map.html')
def nitro_map(endpoint, height='400px', zoom=10, center_lat=18.47, center_lon=-69.97):
    """
    MapLibre GL map component with GeoJSON markers.

    Lazy-loads MapLibre JS/CSS when visible. Fetches markers from endpoint.

    Usage:
        {% nitro_map endpoint='/leasing/properties/map-data/' %}
        {% nitro_map endpoint=map_url height='500px' zoom=12 center_lat=18.50 center_lon=-69.90 %}
    """
    return {
        'endpoint': endpoint,
        'height': height,
        'zoom': zoom,
        'center_lat': center_lat,
        'center_lon': center_lon,
    }


@register.simple_tag
def nitro_key(key, action):
    """
    Bind keyboard shortcut to an Alpine action.

    Usage:
        <div {% nitro_key 'escape' 'open = false' %}>
        <div {% nitro_key 'ctrl.k' "$dispatch('focus-search')" %}>
        <body {% nitro_key 'meta.k' "$dispatch('focus-search')" %}>
    """
    return mark_safe(f'@keydown.{escape(key)}.window="{escape(action)}"')


# =============================================================================
# SPANISH PLURALIZATION FILTER
# =============================================================================

@register.filter
def pluralize_es(count, forms):
    """
    Spanish pluralization.

    Usage:
        {{ count }} {{ count|pluralize_es:'propiedad,propiedades' }}
        {{ count }} {{ count|pluralize_es:'orden,ordenes' }}
    """
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = 0

    parts = forms.split(',')
    if len(parts) != 2:
        return forms

    singular, plural = parts[0].strip(), parts[1].strip()
    return singular if count == 1 else plural


# =============================================================================
# WHATSAPP FILTER
# =============================================================================

# =============================================================================
# SIGNATURE PAD TAG
# =============================================================================

@register.inclusion_tag('nitro/components/signature_pad.html', takes_context=True)
def nitro_signature_pad(
    context,
    name='signature',
    label='Firma',
    required=True,
    width=400,
    height=200,
    line_color='#000000',
    line_width=2,
    background_color='#ffffff',
):
    """
    Touch-friendly signature capture pad.

    Usage:
        {% nitro_signature_pad name='tenant_signature' label='Firma del Inquilino' %}
        {% nitro_signature_pad name='signature' required=False width=500 height=250 %}

    The component saves the signature as a base64 PNG in a hidden input.
    Supports mouse and touch input, with retina display support.

    Args:
        name: Form field name for the hidden input containing base64 data
        label: Label text above the component
        required: Whether the field is required (shows asterisk)
        width: Canvas width in pixels (default 400)
        height: Canvas height in pixels (default 200)
        line_color: Stroke color in hex format (default #000000)
        line_width: Stroke width in pixels (default 2)
        background_color: Canvas background color (default #ffffff)

    Events dispatched:
        - signature-saved: When signature is drawn and saved, with { data: base64String, timestamp: ISO string }
        - signature-cleared: When signature is cleared
    """
    return {
        'name': name,
        'label': label,
        'required': required,
        'width': width,
        'height': height,
        'line_color': line_color,
        'line_width': line_width,
        'background_color': background_color,
        'request': context.get('request'),
    }


# =============================================================================
# DOCUMENT VIEWER TAG
# =============================================================================

@register.inclusion_tag('nitro/components/document_viewer.html', takes_context=True)
def nitro_document_viewer(
    context,
    content=None,
    pdf_url=None,
    title='',
    show_toolbar=True,
    height='600px',
):
    """
    Document viewer with zoom and scroll.

    Usage:
        {% nitro_document_viewer content=document.rendered_content title="Contrato" %}
        {% nitro_document_viewer pdf_url=document.pdf_file.url %}
        {% nitro_document_viewer content=html_content show_toolbar=False height="400px" %}

    Args:
        content: HTML content to display in a styled container
        pdf_url: URL to a PDF file (uses native browser PDF viewer)
        title: Document title shown in toolbar
        show_toolbar: Whether to show zoom/print/download controls (default True)
        height: Height of the viewer container (default 600px)

    Features:
        - For HTML content: rendered in a scrollable styled div
        - For PDF: embedded with native browser PDF viewer
        - Zoom controls (+/- and fit to width)
        - Print button
        - Download button (for PDF)
    """
    return {
        'content': content,
        'pdf_url': pdf_url,
        'title': title,
        'show_toolbar': show_toolbar,
        'height': height,
        'request': context.get('request'),
    }


@register.filter
def whatsapp_clean(phone):
    """
    Clean phone number for WhatsApp wa.me links.

    Removes spaces, dashes, parentheses. Adds country code if missing.

    Usage:
        <a href="https://wa.me/{{ tenant.whatsapp|default:tenant.phone|whatsapp_clean }}">WhatsApp</a>
    """
    if not phone:
        return ''
    # Keep only digits
    digits = ''.join(c for c in str(phone) if c.isdigit())
    if not digits:
        return ''
    # Add country code if 10 digits (assume DR/US)
    if len(digits) == 10:
        digits = '1' + digits
    # Remove leading 00 if present (international format)
    if digits.startswith('00'):
        digits = digits[2:]
    return digits


@register.simple_tag
def whatsapp_link(phone, message=''):
    """
    Generate a WhatsApp wa.me link with optional pre-filled message.

    Usage:
        {% whatsapp_link tenant.phone %}
        {% whatsapp_link tenant.phone "Hola, este es un recordatorio de pago." %}
        {% whatsapp_link phone=tenant.whatsapp message=reminder_message %}

    Returns:
        Full WhatsApp URL string, or empty string if phone is invalid.

    Example output:
        https://wa.me/18095551234?text=Hola%20Juan
    """
    import urllib.parse

    if not phone:
        return ''

    # Clean phone number
    digits = ''.join(c for c in str(phone) if c.isdigit())
    if not digits:
        return ''

    # Add country code if 10 digits (assume DR/US)
    if len(digits) == 10:
        digits = '1' + digits

    # Remove leading 00 if present (international format)
    if digits.startswith('00'):
        digits = digits[2:]

    base_url = f'https://wa.me/{digits}'

    if message:
        encoded = urllib.parse.quote(str(message))
        return f'{base_url}?text={encoded}'

    return base_url


# =============================================================================
# GLOBAL SEARCH TAG
# =============================================================================

@register.inclusion_tag('nitro/components/global_search.html')
def nitro_global_search(placeholder='Buscar...', empty_hint='Escribe para buscar'):
    """
    Global search modal triggered by Cmd+K / Ctrl+K.

    Include once in base.html before closing body tag:
        {% nitro_global_search %}
        {% nitro_global_search placeholder='Search tenants, properties...' %}

    Features:
        - Toggle with Cmd+K / Ctrl+K keyboard shortcut
        - Debounced search as you type (min 2 chars)
        - Keyboard navigation (up/down arrows, Enter to select, Escape to close)
        - Results grouped by type
        - Recent searches stored in localStorage

    Args:
        placeholder: Placeholder text for the search input
        empty_hint: Hint text shown when search is empty
    """
    return {
        'placeholder': placeholder,
        'empty_hint': empty_hint,
    }


# =============================================================================
# PHOTO GALLERY TAG
# =============================================================================

@register.inclusion_tag('nitro/components/inline_create.html', takes_context=True)
def nitro_inline_create(
    context,
    name,
    model_name,
    create_url,
    options=None,
    placeholder='Seleccionar o crear nuevo...',
    label='',
    required=False,
    value=None,
    display_field='name',
    value_field='id',
    search_url=None,
    help_text='',
    css_class='',
):
    """
    Inline entity creation with search and quick-create.

    This component provides a searchable dropdown that allows users to:
    - Search and select from existing options
    - Create a new entity inline without leaving the current form

    Usage:
        {# With static options #}
        {% nitro_inline_create name='tenant' model_name='Inquilino' create_url='/leasing/tenant/inline-create/' options=tenant_options %}

        {# With server-side search #}
        {% nitro_inline_create name='landlord' model_name='Propietario' create_url='/leasing/landlord/inline-create/' search_url='/leasing/landlords/search/' %}

    Args:
        name: Form field name for the hidden input
        model_name: Display name of the entity being created (e.g., 'Inquilino')
        create_url: URL endpoint for creating new entities (POST)
        options: List of dicts with 'value' and 'label' keys (for client-side search)
        placeholder: Placeholder text for the search input
        label: Label for the field
        required: Whether the field is required
        value: Initial selected value
        display_field: Field name for display text in created entity response
        value_field: Field name for value in created entity response
        search_url: URL for server-side search (returns {results: [{value, label}, ...]})
        help_text: Help text below the field
        css_class: Additional CSS classes for the container
    """
    import json as _json

    # Build options JSON
    if options is None:
        options = []
    options_json = _json.dumps([
        {'value': str(o.get('value', o.get('id', ''))), 'label': str(o.get('label', o.get('name', '')))}
        for o in options
    ])

    # Find current label if value is set
    current_label = ''
    if value:
        for o in options:
            if str(o.get('value', o.get('id', ''))) == str(value):
                current_label = str(o.get('label', o.get('name', '')))
                break

    return {
        'name': name,
        'model_name': model_name,
        'create_url': create_url,
        'options': options,
        'options_json': options_json,
        'placeholder': placeholder,
        'label': label,
        'required': required,
        'value': value or '',
        'current_label': current_label,
        'display_field': display_field,
        'value_field': value_field,
        'search_url': search_url or '',
        'help_text': help_text,
        'css_class': css_class,
        'request': context.get('request'),
    }


@register.inclusion_tag('nitro/components/gallery.html')
def nitro_gallery(photos, columns=3, gap=2, aspect_ratio='4:3', enable_lightbox=True,
                  empty_title='', empty_message=''):
    """
    Photo gallery with lightbox.

    Args:
        photos: List of photo dicts with keys:
            - url: Full-size image URL (required)
            - thumbnail_url: Thumbnail URL (optional, defaults to url)
            - caption: Photo caption (optional)
            - alt: Alt text (optional)
            - category: Category label e.g. "Exterior", "Cocina" (optional)
            - is_main: Boolean, marks the primary/featured photo (optional)
        columns: Number of grid columns (2, 3, 4, or 5)
        gap: Gap between items (1, 2, 3, or 4)
        aspect_ratio: Aspect ratio for thumbnails ('1:1', '4:3', '16:9', '3:2')
        enable_lightbox: Enable click-to-zoom lightbox (default True)
        empty_title: Title for empty state
        empty_message: Message for empty state

    Usage:
        {% nitro_gallery photos=property.photos.all %}
        {% nitro_gallery photos=photo_list columns=4 aspect_ratio='1:1' %}

    Photo dict example:
        photos = [
            {'url': '/media/photo1.jpg', 'category': 'Exterior', 'is_main': True},
            {'url': '/media/photo2.jpg', 'thumbnail_url': '/media/photo2_thumb.jpg', 'caption': 'Vista del salon'},
        ]
    """
    import json as _json

    # Process photos into a consistent format
    processed_photos = []
    if photos:
        for photo in photos:
            if isinstance(photo, dict):
                processed_photos.append({
                    'url': photo.get('url', ''),
                    'thumbnail_url': photo.get('thumbnail_url', photo.get('url', '')),
                    'caption': photo.get('caption', ''),
                    'alt': photo.get('alt', photo.get('caption', '')),
                    'category': photo.get('category', ''),
                    'is_main': bool(photo.get('is_main', False)),
                })
            elif hasattr(photo, 'url'):
                # Handle model instances (e.g., PropertyPhoto)
                processed_photos.append({
                    'url': getattr(photo, 'url', '') or (photo.image.url if hasattr(photo, 'image') and photo.image else ''),
                    'thumbnail_url': getattr(photo, 'thumbnail_url', '') or getattr(photo, 'url', '') or (photo.image.url if hasattr(photo, 'image') and photo.image else ''),
                    'caption': getattr(photo, 'caption', '') or getattr(photo, 'description', ''),
                    'alt': getattr(photo, 'alt', '') or getattr(photo, 'caption', '') or getattr(photo, 'description', ''),
                    'category': getattr(photo, 'category', '') or getattr(photo, 'photo_type', ''),
                    'is_main': bool(getattr(photo, 'is_main', False) or getattr(photo, 'is_primary', False)),
                })

    # Grid column classes (responsive)
    column_classes = {
        2: 'grid-cols-1 sm:grid-cols-2',
        3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
        4: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4',
        5: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5',
    }
    grid_classes = column_classes.get(int(columns), column_classes[3])

    # Aspect ratio classes
    aspect_classes = {
        '1:1': 'aspect-square',
        '4:3': 'aspect-[4/3]',
        '3:2': 'aspect-[3/2]',
        '16:9': 'aspect-video',
    }
    aspect_class = aspect_classes.get(aspect_ratio, aspect_classes['4:3'])

    # Convert photos to JSON for Alpine.js
    photos_json = _json.dumps(processed_photos)

    return {
        'photos': processed_photos,
        'photos_json': photos_json,
        'columns': columns,
        'gap': gap,
        'grid_classes': grid_classes,
        'aspect_class': aspect_class,
        'enable_lightbox': enable_lightbox,
        'empty_title': empty_title,
        'empty_message': empty_message,
    }


# =============================================================================
# DICTIONARY HELPER FILTER
# =============================================================================

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.

    Usage:
        {{ my_dict|get_item:key_var }}
        {{ condition_counts|get_item:'excellent' }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, None)
