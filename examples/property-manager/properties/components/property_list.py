# properties/components/property_list.py
from django.db.models import Count
from properties.models import Property
from properties.schemas import PropertyListState

from nitro.list import BaseListComponent
from nitro.registry import register_component


@register_component
class PropertyList(BaseListComponent[PropertyListState]):
    """
    Property listing component with pagination, search, and CRUD operations.

    Demonstrates BaseListComponent with:
    - Automatic pagination (20 items per page)
    - Search across 'name' and 'address' fields
    - Inline create/edit/delete functionality
    - Optimized queries with prefetch_related

    Note: This is a demo component. In production, you should:
    - Add permission checks (e.g., check if request.user is authenticated)
    - Add rate limiting for search queries
    - Implement proper error handling
    """
    template_name = "components/property_list.html"
    model = Property
    # state_class auto-inferred from Generic[PropertyListState] (v0.7.0)

    # Configure search and pagination
    search_fields = ['name', 'address']
    per_page = 20
    order_by = '-created_at'

    def get_base_queryset(self, search='', filters=None):
        """
        Override to add tenant_count annotation and optimize queries.

        This is called automatically by BaseListComponent for both
        initial load and refresh operations.
        """
        # Start with base queryset
        qs = self.model.objects.prefetch_related('tenants').annotate(
            tenant_count=Count('tenants')
        )

        # Apply search (handled by SearchMixin)
        if search:
            qs = self.apply_search(qs, search)

        # Apply filters (handled by FilterMixin)
        if filters:
            qs = self.apply_filters(qs, filters)

        # Apply ordering
        return qs.order_by(self.order_by)

    # All these methods are inherited from BaseListComponent:
    # - Pagination: next_page(), previous_page(), go_to_page(), set_per_page()
    # - Search: search_items(search)
    # - Filters: set_filters(**filters), clear_filters()
    # - CRUD: create_item(), delete_item(), start_edit(), save_edit(), cancel_edit()
    # - Refresh: refresh()
