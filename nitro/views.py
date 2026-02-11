"""
Django Nitro 0.8 - Server-rendered views with HTMX + Alpine.

Replaces the Pydantic state + JSON dispatch architecture with
standard Django CBVs that return HTML partials for HTMX requests.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


# =============================================================================
# Tab dataclass for NitroModelView declarative tabs
# =============================================================================

@dataclass
class Tab:
    """Declarative tab definition for detail views.

    Usage::

        tabs = [
            Tab('info', 'General', 'leasing/partials/property_info_tab.html'),
            Tab('payments', 'Pagos', 'leasing/partials/property_payments_tab.html',
                badge_count=lambda obj: obj.payments.filter(status='pending').count(),
                badge_color='amber'),
        ]
    """
    name: str
    label: str
    template: str
    badge_count: Optional[object] = None  # callable(obj) -> int
    badge_color: str = 'gray'  # 'gray', 'primary', 'red', 'amber', 'green'


class NitroView(LoginRequiredMixin, TemplateView):
    """
    Base view for all Nitro 0.8 views.

    Features:
    - HTMX detection via django-htmx middleware
    - Automatic full-page vs partial rendering
    - Toast notifications via HX-Trigger header
    - HTMX redirect/refresh helpers
    """

    template_name = None        # Full page template
    partial_template = None     # Partial for HTMX swaps

    @property
    def is_htmx(self):
        return getattr(self.request, 'htmx', False) and self.request.htmx

    def get_template_names(self):
        if self.is_htmx and self.partial_template:
            return [self.partial_template]
        return [self.template_name]

    def render_response(self, context=None, **kwargs):
        """Render the appropriate template (full page or partial)."""
        if context is None:
            context = self.get_context_data(**kwargs)
        template = self.get_template_names()[0]
        from django.template.loader import render_to_string
        html = render_to_string(template, context, request=self.request)
        return HttpResponse(html)

    def htmx_redirect(self, url):
        """
        Send HTMX redirect (client-side redirect).

        Security: Only allows internal URLs to prevent open redirect attacks.
        External URLs are blocked and will redirect to home instead.
        """
        from django.utils.http import url_has_allowed_host_and_scheme

        # Validate URL is safe (internal only)
        if not url_has_allowed_host_and_scheme(
            url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure()
        ):
            # Log attempted redirect to external URL
            import logging
            logger = logging.getLogger('security')
            logger.warning(
                f"Blocked open redirect attempt to: {url} from {self.request.path}"
            )
            url = '/'  # Redirect to home instead

        response = HttpResponse(status=204)
        response['HX-Redirect'] = url
        return response

    def htmx_refresh(self):
        """Tell HTMX to refresh the page."""
        response = HttpResponse(status=204)
        response['HX-Refresh'] = 'true'
        return response

    def toast(self, message, level='success'):
        """
        Add a toast notification via HX-Trigger header.
        Works with the nitro.js toast listener.
        """
        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({
            'showToast': {'message': message, 'type': level}
        })
        return response

    def toast_with_html(self, html, message, level='success'):
        """Return HTML content with a toast trigger."""
        response = HttpResponse(html)
        response['HX-Trigger'] = json.dumps({
            'showToast': {'message': message, 'type': level}
        })
        return response

    def success(self, message):
        return self.toast(message, 'success')

    def error(self, message):
        return self.toast(message, 'error')


class NitroListView(NitroView):
    """List view with search, filters, sorting, pagination, and declarative tables."""

    model = None
    search_fields = []
    filter_fields = []
    sortable_fields = []
    paginate_by = 20
    select_related = []
    prefetch_related = []
    default_sort = '-created_at'
    columns = []
    row_actions = []
    quick_actions = []
    bulk_actions = []

    def get_queryset(self):
        """Build the base queryset with select/prefetch related."""
        qs = self.model.objects.all()
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        if self.prefetch_related:
            qs = qs.prefetch_related(*self.prefetch_related)
        return qs

    def apply_search(self, qs):
        """Apply search from ?q= parameter."""
        query = self.request.GET.get('q', '').strip()
        if not query or not self.search_fields:
            return qs

        # Try unaccent search (PostgreSQL) with fallback
        try:
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f'{field}__unaccent__icontains': query})
            return qs.filter(q_objects)
        except Exception:
            # Fallback to icontains without unaccent
            q_objects = Q()
            for field in self.search_fields:
                q_objects |= Q(**{f'{field}__icontains': query})
            return qs.filter(q_objects)

    def apply_filters(self, qs):
        """Apply filters from query parameters matching filter_fields."""
        for field in self.filter_fields:
            value = self.request.GET.get(field, '').strip()
            if value:
                qs = qs.filter(**{field: value})
        return qs

    def apply_sort(self, qs):
        """Apply sorting from ?sort= parameter."""
        sort = self.request.GET.get('sort', '').strip()
        if sort:
            # Validate sort field (strip leading -)
            field_name = sort.lstrip('-')
            if field_name in self.sortable_fields:
                return qs.order_by(sort)
        if self.default_sort:
            return qs.order_by(self.default_sort)
        return qs

    def get_filtered_queryset(self):
        """Apply search, filters, and sorting to queryset."""
        qs = self.get_queryset()
        qs = self.apply_search(qs)
        qs = self.apply_filters(qs)
        qs = self.apply_sort(qs)
        return qs

    def get_page_obj(self, queryset=None):
        """Paginate the queryset."""
        if queryset is None:
            queryset = self.get_filtered_queryset()
        paginator = Paginator(queryset, self.paginate_by)
        page_number = self.request.GET.get('page', 1)
        return paginator.get_page(page_number)

    def get_filter_options(self):
        """Override to provide filter dropdown options.

        Returns dict like:
            {
                'status': [('available', 'Disponible'), ('rented', 'Alquilada')],
                'property_type': [('apartment', 'Apartamento'), ...],
            }
        """
        return {}

    def get_current_filters(self):
        """Get current filter values from request."""
        filters = {}
        for field in self.filter_fields:
            filters[field] = self.request.GET.get(field, '')
        return filters

    def get_current_sort(self):
        """Get current sort value from request."""
        return self.request.GET.get('sort', self.default_sort or '')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_obj = self.get_page_obj()
        context.update({
            'page_obj': page_obj,
            'object_list': page_obj.object_list,
            'filter_options': self.get_filter_options(),
            'current_filters': self.get_current_filters(),
            'current_search': self.request.GET.get('q', ''),
            'current_sort': self.get_current_sort(),
            'sortable_fields': self.sortable_fields,
        })
        if self.columns:
            context['columns'] = self.columns
        if self.row_actions:
            context['row_actions'] = self.row_actions
        if self.quick_actions:
            context['quick_actions'] = self.quick_actions
        if self.bulk_actions:
            context['bulk_actions'] = self.bulk_actions
            context['has_bulk_actions'] = True
        return context

    def post(self, request, *args, **kwargs):
        """Handle bulk actions."""
        action = request.POST.get('bulk_action', '')
        selected_ids = request.POST.getlist('selected_ids')

        if not action or not selected_ids:
            return self.toast('Selecciona al menos un elemento', 'warning')

        # Validate action exists
        valid_actions = {a.name for a in self.bulk_actions}
        if action not in valid_actions:
            return self.toast('Acción no válida', 'error')

        # Call handler method: handle_bulk_{action}
        handler = getattr(self, f'handle_bulk_{action}', None)
        if not handler:
            return self.toast(f'Sin handler para: {action}', 'error')

        try:
            qs = self.get_queryset().filter(pk__in=selected_ids)
            result = handler(qs, selected_ids)
            if isinstance(result, HttpResponse):
                return result
            return self.htmx_refresh()
        except Exception as e:
            logger.error(f'Bulk action {action} failed: {e}')
            return self.toast(f'Error: {str(e)}', 'error')


class NitroModelView(NitroView):
    """Detail view for a single model instance with optional declarative tabs."""

    model = None
    pk_url_kwarg = 'pk'
    slug_field = 'id'
    tabs = []
    default_tab = None

    def get_object(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(self.model, **{self.slug_field: pk})

    def get_current_tab(self):
        """Get the current tab from ?tab= parameter, validated against defined tabs."""
        if not self.tabs:
            return None
        tab_name = self.request.GET.get('tab', '').strip()
        tab_names = {t.name for t in self.tabs}
        if tab_name in tab_names:
            return tab_name
        if self.default_tab and self.default_tab in tab_names:
            return self.default_tab
        return self.tabs[0].name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['object'] = obj

        if self.tabs:
            current_tab = self.get_current_tab()
            tabs_data = []
            active_tab_template = None
            for tab in self.tabs:
                tab_data = {
                    'name': tab.name,
                    'label': tab.label,
                    'template': tab.template,
                    'badge_color': tab.badge_color,
                    'badge_count': None,
                    'active': tab.name == current_tab,
                }
                if callable(tab.badge_count):
                    try:
                        tab_data['badge_count'] = tab.badge_count(obj)
                    except Exception:
                        tab_data['badge_count'] = None
                if tab.name == current_tab:
                    active_tab_template = tab.template
                tabs_data.append(tab_data)

            context['tabs'] = tabs_data
            context['current_tab'] = current_tab
            context['active_tab_template'] = active_tab_template

        return context

    def get_template_names(self):
        # For HTMX tab requests, render only the partial tab template
        if self.is_htmx and self.tabs and self.request.GET.get('tab'):
            current_tab = self.get_current_tab()
            for tab in self.tabs:
                if tab.name == current_tab:
                    return [tab.template]
        return super().get_template_names()

    def get_success_url(self):
        """Override to specify redirect URL after actions."""
        raise NotImplementedError("Subclasses must implement get_success_url()")


class NitroFormView(NitroView):
    """
    Form view for create/edit with HTMX support.
    Handles both GET (render form) and POST (process form).
    """

    form_class = None
    success_url = None

    def get_form_class(self):
        return self.form_class

    def get_form_kwargs(self):
        kwargs = {}
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        return kwargs

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = self.get_form()
        return context

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        """Handle valid form. Override for custom save logic."""
        self.object = form.save()
        if self.is_htmx:
            return self.success('Guardado exitosamente')
        from django.shortcuts import redirect
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        """Re-render the form with errors."""
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self):
        if self.success_url:
            return self.success_url
        raise NotImplementedError("Provide success_url or override get_success_url()")


# =============================================================================
# CRUD Views - Eliminate boilerplate for standard HTMX + slideover patterns
# =============================================================================

class NitroCreateView(NitroFormView):
    """
    CRUD Create view with HTMX slideover + toast pattern.

    Handles:
    - Form kwargs with company (via pass_company_to_form)
    - Save with company assignment (via assign_company)
    - HTMX response: toast + close slideover + page refresh
    - Non-HTMX fallback redirect

    Minimal config::

        class PropertyCreateView(CompanyMixin, NitroCreateView):
            model = Property
            form_class = PropertyForm

    Optional config::

        slideover_id = 'create-property'    # default: 'create-{model_name}'
        success_message = 'Creado'          # default: '{verbose_name} creado exitosamente'
        list_url_name = 'leasing:property_list'  # for non-HTMX redirect
        pass_company_to_form = True         # passes organization to form kwargs['company']
        assign_company = True               # sets obj.company = organization on save
    """

    model = None
    slideover_id = None
    success_message = None
    list_url_name = None
    pass_company_to_form = True
    assign_company = True

    def get_slideover_id(self):
        if self.slideover_id:
            return self.slideover_id
        if self.model:
            return f'create-{self.model._meta.model_name}'
        return 'create'

    def get_success_message(self):
        if self.success_message:
            return self.success_message
        if self.model:
            return f'{self.model._meta.verbose_name} creado exitosamente'
        return 'Creado exitosamente'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.pass_company_to_form and hasattr(self, 'organization'):
            kwargs['company'] = self.organization
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        if self.assign_company and hasattr(self, 'organization'):
            org = self.organization
            if org and hasattr(obj, 'company'):
                obj.company = org
        self.save_object(obj, form)

        if self.is_htmx:
            response = HttpResponse(status=204)
            response['HX-Trigger'] = json.dumps({
                'showToast': {'message': self.get_success_message(), 'type': 'success'},
                'closeSlideover': self.get_slideover_id(),
            })
            response['HX-Refresh'] = 'true'
            return response

        if self.list_url_name:
            from django.shortcuts import redirect
            return redirect(self.list_url_name)
        return self.htmx_refresh()

    def save_object(self, obj, form):
        """Override for custom save logic (M2M, extra fields, etc.)."""
        obj.save()

    def form_invalid(self, form):
        return self.render_to_response({'form': form})


class NitroUpdateView(NitroFormView):
    """
    CRUD Update view with HTMX slideover + toast pattern.

    Handles:
    - Object loading with company filtering (via get_company_object if available)
    - Form kwargs with instance + company
    - Context with is_edit=True and object
    - HTMX response: toast + close slideover + page refresh
    - form_invalid with is_edit context preserved

    Minimal config::

        class PropertyUpdateView(CompanyMixin, NitroUpdateView):
            model = Property
            form_class = PropertyForm

    Optional config::

        slideover_id = 'edit-property'      # default: 'edit-{model_name}'
        success_message = 'Actualizado'     # default: '{verbose_name} actualizado exitosamente'
        pass_company_to_form = True         # passes organization to form kwargs['company']
    """

    model = None
    slideover_id = None
    success_message = None
    pass_company_to_form = True

    def get_slideover_id(self):
        if self.slideover_id:
            return self.slideover_id
        if self.model:
            return f'edit-{self.model._meta.model_name}'
        return 'edit'

    def get_success_message(self):
        if self.success_message:
            return self.success_message
        if self.model:
            return f'{self.model._meta.verbose_name} actualizado exitosamente'
        return 'Actualizado exitosamente'

    def get_object(self):
        if hasattr(self, 'get_company_object'):
            return self.get_company_object(self.model, pk=self.kwargs['pk'])
        return get_object_or_404(self.model, pk=self.kwargs['pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        if self.pass_company_to_form and hasattr(self, 'organization'):
            kwargs['company'] = self.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['object'] = self.get_object()
        return context

    def form_valid(self, form):
        form.save()
        if self.is_htmx:
            response = HttpResponse(status=204)
            response['HX-Trigger'] = json.dumps({
                'showToast': {'message': self.get_success_message(), 'type': 'success'},
                'closeSlideover': self.get_slideover_id(),
            })
            response['HX-Refresh'] = 'true'
            return response
        from django.shortcuts import redirect
        return redirect(self.request.path)

    def form_invalid(self, form):
        return self.render_to_response({
            'form': form, 'is_edit': True, 'object': self.get_object()
        })


class NitroDeleteView(LoginRequiredMixin, View):
    """
    CRUD Delete view with HTMX toast + redirect/refresh.

    Handles:
    - Object loading with company filtering
    - Delete validation via can_delete()
    - Hard delete or soft delete (is_active=False)
    - HTMX response: toast + redirect or refresh

    Minimal config::

        class PropertyDeleteView(CompanyMixin, NitroDeleteView):
            model = Property

    With validation::

        def can_delete(self, obj):
            if obj.leases.filter(status='active').exists():
                return False, 'Tiene contratos activos'
            return True, None

    Soft delete::

        class UserDeleteView(CompanyMixin, NitroDeleteView):
            model = UserPermission
            soft_delete = True

    Optional config::

        success_message = 'Eliminado'       # default: '{verbose_name} eliminado exitosamente'
        redirect_url = '/leasing/properties/'  # HX-Redirect, else HX-Refresh
        soft_delete = False                  # if True, sets is_active=False
        soft_delete_field = 'is_active'      # field to set False for soft delete
    """

    model = None
    success_message = None
    redirect_url = None
    soft_delete = False
    soft_delete_field = 'is_active'

    def get_success_message(self):
        if self.success_message:
            return self.success_message
        if self.model:
            return f'{self.model._meta.verbose_name} eliminado exitosamente'
        return 'Eliminado exitosamente'

    def get_object(self, pk):
        if hasattr(self, 'get_company_object'):
            return self.get_company_object(self.model, pk=pk)
        return get_object_or_404(self.model, pk=pk)

    def can_delete(self, obj):
        """Override to add validation. Return (can_delete, error_message)."""
        return True, None

    def perform_delete(self, obj):
        """Override for custom delete logic."""
        if self.soft_delete:
            setattr(obj, self.soft_delete_field, False)
            obj.save(update_fields=[self.soft_delete_field])
        else:
            obj.delete()

    def post(self, request, pk):
        obj = self.get_object(pk)

        can, error = self.can_delete(obj)
        if not can:
            response = HttpResponse(status=204)
            response['HX-Trigger'] = json.dumps({
                'showToast': {'message': error, 'type': 'error'},
            })
            return response

        self.perform_delete(obj)

        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({
            'showToast': {'message': self.get_success_message(), 'type': 'success'},
        })
        if self.redirect_url:
            response['HX-Redirect'] = self.redirect_url
        else:
            response['HX-Refresh'] = 'true'
        return response


# =============================================================================
# INLINE EDIT - Edit individual cells in tables
# =============================================================================

class NitroInlineEditView(LoginRequiredMixin, View):
    """
    Inline cell editing for NitroListView tables.

    Renders a single table cell as an editable input on GET,
    saves the value on POST, and returns the updated cell.

    Usage::

        class PropertyInlineEditView(CompanyMixin, NitroInlineEditView):
            model = Property
            editable_fields = {
                'status': {'type': 'select', 'choices': Property.STATUS},
                'target_rent': {'type': 'number', 'min': 0, 'step': '0.01'},
                'name': {'type': 'text'},
            }

    URL pattern::

        path('properties/<uuid:pk>/inline-edit/<str:field>/',
             PropertyInlineEditView.as_view(),
             name='property_inline_edit'),

    In templates, use the nitro_inline_cell tag or add data attributes::

        <td class="group">
            <span hx-get="{% url 'leasing:property_inline_edit' pk=obj.pk field='status' %}"
                  hx-target="closest td"
                  hx-swap="innerHTML"
                  class="cursor-pointer hover:bg-primary-50 px-2 py-1 rounded transition">
                {{ obj.get_status_display }}
            </span>
        </td>
    """

    model = None
    editable_fields = {}  # {field_name: {type, choices?, min?, max?, step?}}

    def get_object(self, pk):
        if hasattr(self, 'get_company_object'):
            return self.get_company_object(self.model, pk=pk)
        return get_object_or_404(self.model, pk=pk)

    def get(self, request, pk, field):
        """Return editable input for the field."""
        if field not in self.editable_fields:
            return HttpResponse('Field not editable', status=400)

        obj = self.get_object(pk)
        config = self.editable_fields[field]
        current_value = getattr(obj, field, '')

        from django.template.loader import render_to_string
        html = render_to_string('nitro/components/inline_edit.html', {
            'object': obj,
            'field': field,
            'config': config,
            'current_value': current_value,
            'save_url': request.path,
        }, request=request)

        return HttpResponse(html)

    def post(self, request, pk, field):
        """Save the edited value and return the updated cell."""
        if field not in self.editable_fields:
            return HttpResponse('Field not editable', status=400)

        obj = self.get_object(pk)
        new_value = request.POST.get('value', '').strip()
        config = self.editable_fields[field]

        # Basic validation
        try:
            if config.get('type') == 'number':
                from decimal import Decimal, InvalidOperation
                try:
                    new_value = Decimal(new_value) if new_value else None
                except InvalidOperation:
                    return self._error_response('Valor numérico inválido')

            if config.get('choices'):
                valid_values = [str(c[0]) for c in config['choices']]
                if str(new_value) not in valid_values:
                    return self._error_response('Valor no válido')

            setattr(obj, field, new_value)
            obj.save(update_fields=[field, 'updated_at'] if hasattr(obj, 'updated_at') else [field])

        except Exception as e:
            return self._error_response(str(e))

        # Return updated cell display
        from django.template.loader import render_to_string
        html = render_to_string('nitro/components/inline_cell.html', {
            'object': obj,
            'field': field,
            'value': getattr(obj, field),
            'config': config,
            'edit_url': request.path,
        }, request=request)

        response = HttpResponse(html)
        response['HX-Trigger'] = json.dumps({
            'showToast': {'message': 'Actualizado', 'type': 'success'},
        })
        return response

    def _error_response(self, message):
        response = HttpResponse(status=422)
        response['HX-Trigger'] = json.dumps({
            'showToast': {'message': message, 'type': 'error'},
        })
        return response
