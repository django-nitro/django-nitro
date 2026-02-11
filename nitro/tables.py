"""
Django Nitro 0.8 - Declarative table definitions.

Usage::

    from nitro.tables import Column, RowAction

    class PropertyListView(CompanyMixin, NitroListView):
        columns = [
            Column('name', 'Nombre', sortable=True, link='leasing:property_detail', subtitle_field='address'),
            Column('property_type', 'Tipo'),
            Column('landlord.legal_name', 'Propietario'),
            Column('target_rent', 'Renta', display='currency', sortable=True),
            Column('status', 'Estado', display='status_badge'),
        ]
        row_actions = [
            RowAction('edit', 'Editar', url_name='leasing:property_update', method='get', slideover='edit-item'),
            RowAction('delete', 'Eliminar', url_name='leasing:property_delete', method='post',
                      confirm='¿Eliminar?', css_class='text-red-600 hover:text-red-800'),
        ]

Template::

    {% nitro_table target='#list-content' %}
"""

from dataclasses import dataclass


@dataclass
class Column:
    """Column definition for declarative tables.

    Args:
        field: Model field path (supports dotted: 'landlord.legal_name').
        label: Column header label.
        sortable: Enable sorting on this column.
        display: Display filter to apply ('currency', 'status_badge', 'phone_format',
                 'relative_date', 'priority_badge', 'truncate_id').
        link: URL name for linking the cell value (e.g. 'leasing:property_detail').
        css_class: Extra CSS classes for the column.
        mobile: Whether to show this column on mobile cards.
        mobile_label: Whether to show the label on mobile cards.
        subtitle_field: Secondary field to display below the main value (e.g. 'email').
        currency_field: Field path for currency code when display='currency' (e.g. 'rent_currency').
        icon: Icon type to show conditionally ('location' for map pin).
        icon_field: Field to check for truthiness to show the icon.
        icon_link: URL name for the icon link (receives obj.pk as arg).
    """
    field: str
    label: str
    sortable: bool = False
    display: str = ''
    link: str = ''
    css_class: str = ''
    mobile: bool = True
    mobile_label: bool = True
    subtitle_field: str = ''
    currency_field: str = ''
    icon: str = ''
    icon_field: str = ''
    icon_link: str = ''


@dataclass
class RowAction:
    """Row action definition for declarative tables.

    Args:
        name: Action identifier.
        label: Display text.
        url_name: Django URL name (receives obj.pk as arg).
        method: 'get' (slideover/HTMX), 'post' (HTMX post), 'link' (regular navigation).
        confirm: Confirmation message for destructive actions.
        slideover: Slideover ID to open (for method='get').
        css_class: Extra CSS classes for the action button.
        icon: Icon name for the action button (optional).
        target: Link target for method='link' (e.g., '_blank' for new tab).
    """
    name: str
    label: str
    url_name: str
    method: str = 'get'
    confirm: str = ''
    slideover: str = ''
    css_class: str = ''
    icon: str = ''
    target: str = ''


@dataclass
class BulkAction:
    """Declarative bulk action for NitroListView tables.

    Usage::

        bulk_actions = [
            BulkAction('activate', 'Activar seleccionados'),
            BulkAction('export', 'Exportar', icon='download'),
            BulkAction('delete', 'Eliminar', confirm='¿Eliminar seleccionados?',
                       css_class='text-red-600'),
        ]

    Args:
        name: Action identifier (used in POST and handler method name).
        label: Display text for the button.
        confirm: Confirmation message (optional).
        icon: Icon name for the button (optional).
        css_class: Extra CSS classes for the button.
    """
    name: str
    label: str
    confirm: str = ''
    icon: str = ''
    css_class: str = ''


@dataclass
class QuickAction:
    """Quick action icon button shown on row hover.

    Usage::

        quick_actions = [
            QuickAction('whatsapp', icon='whatsapp', url_name='leasing:whatsapp_tenant',
                        tooltip='WhatsApp', css_class='text-green-600',
                        condition=lambda obj: obj.has_active_lease),
            QuickAction('payment', icon='payment', hx_get='leasing:rent_payment_create',
                        slideover='payment', tooltip='Registrar pago'),
            QuickAction('ticket', icon='ticket', url_name='tickets:ticket_create',
                        tooltip='Crear ticket'),
        ]

    Args:
        name: Action identifier.
        icon: Icon name ('whatsapp', 'email', 'edit', 'delete', 'payment', 'ticket',
              'view', 'assign', 'status', 'phone', 'envelope', 'pencil', 'trash',
              'dollar', 'wrench', 'eye', 'user-plus', 'clock').
        url_name: Django URL name (receives obj.pk as arg). For external links.
        hx_post: URL name for HTMX POST request.
        hx_get: URL name for HTMX GET request (e.g., for slideovers).
        slideover: Slideover ID to open (used with hx_get).
        confirm: Confirmation message for destructive actions.
        tooltip: Tooltip text shown on hover.
        css_class: Extra CSS classes for the button.
        condition: Callable that receives the object and returns True if action should show.
                   E.g., lambda obj: obj.can_edit or lambda obj: obj.phone is not None.
        external_url: Callable that receives obj and returns an external URL (e.g., wa.me).
    """
    name: str
    icon: str = ''
    url_name: str = ''
    hx_post: str = ''
    hx_get: str = ''
    slideover: str = ''
    confirm: str = ''
    tooltip: str = ''
    css_class: str = ''
    condition: callable = None
    external_url: callable = None

    def is_visible(self, obj):
        """Check if the action should be visible for the given object."""
        if self.condition is None:
            return True
        try:
            return self.condition(obj)
        except Exception:
            return False

    def get_url(self, obj):
        """Resolve the URL for the given object."""
        if self.external_url:
            try:
                return self.external_url(obj)
            except Exception:
                return None
        return None


# Pre-defined icon SVG paths for common actions
QUICK_ACTION_ICONS = {
    'whatsapp': '''<path fill-rule="evenodd" d="M18.403 5.633A8.919 8.919 0 0 0 12.053 3c-4.948 0-8.976 4.027-8.978 8.977 0 1.582.413 3.126 1.198 4.488L3 21.116l4.759-1.249a8.981 8.981 0 0 0 4.29 1.093h.004c4.947 0 8.975-4.027 8.977-8.977a8.926 8.926 0 0 0-2.627-6.35zM12.053 19.445h-.003a7.453 7.453 0 0 1-3.798-1.041l-.272-.162-2.824.741.753-2.753-.177-.282a7.448 7.448 0 0 1-1.141-3.971c.002-4.114 3.349-7.461 7.465-7.461a7.413 7.413 0 0 1 5.275 2.188 7.42 7.42 0 0 1 2.183 5.279c-.002 4.114-3.349 7.462-7.461 7.462zm4.093-5.589c-.225-.113-1.327-.655-1.533-.73-.205-.075-.354-.112-.504.112s-.58.729-.711.879-.262.168-.486.056-.947-.349-1.804-1.113c-.667-.595-1.117-1.329-1.248-1.554s-.014-.346.099-.458c.101-.1.224-.262.336-.393.112-.131.149-.224.224-.374s.038-.281-.019-.393c-.056-.113-.505-1.217-.692-1.666-.182-.435-.366-.377-.504-.384-.13-.006-.28-.008-.43-.008s-.392.056-.598.28c-.205.225-.784.767-.784 1.871s.803 2.171.916 2.321c.112.15 1.582 2.415 3.832 3.387.536.231.954.369 1.279.473.537.171 1.026.146 1.413.089.431-.064 1.327-.542 1.514-1.066.187-.524.187-.973.131-1.067-.056-.093-.205-.149-.43-.261z"/>''',
    'email': '''<path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'envelope': '''<path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'edit': '''<path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'pencil': '''<path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'delete': '''<path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'trash': '''<path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'payment': '''<path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'dollar': '''<path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'ticket': '''<path d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'wrench': '''<path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'view': '''<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'eye': '''<path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'assign': '''<path d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'user-plus': '''<path d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'status': '''<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'clock': '''<path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'phone': '''<path d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'history': '''<path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'document': '''<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
    'building': '''<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>''',
}


def get_field_value(obj, field_path):
    """Resolve a dotted field path on a model instance.

    Examples:
        get_field_value(property, 'name') -> property.name
        get_field_value(property, 'landlord.legal_name') -> property.landlord.legal_name
    """
    value = obj
    for attr in field_path.split('.'):
        if value is None:
            return None
        value = getattr(value, attr, None)
    if callable(value):
        value = value()
    return value
