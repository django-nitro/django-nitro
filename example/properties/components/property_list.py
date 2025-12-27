# properties/components/property_list.py
from django.db.models import Count, Q
from nitro.base import CrudNitroComponent
from nitro.registry import register_component
from properties.models import Property
from properties.schemas import PropertyListState, PropertySchema


@register_component
class PropertyList(CrudNitroComponent[PropertyListState]):
    """
    Property listing component with search and CRUD operations.

    Displays a list of properties with tenant counts, supports searching,
    and provides inline create/edit/delete functionality.

    Note: This is a demo component. In production, you should:
    - Add permission checks (e.g., check if request.user is authenticated)
    - Implement pagination for large datasets
    - Add rate limiting for search queries
    """
    template_name = "components/property_list.html"
    state_class = PropertyListState
    model = Property

    def get_initial_state(self, **kwargs):
        return self._build_list_state("")

    def refresh(self):
        self.state = self._build_list_state(self.state.search_query)

    def _build_list_state(self, query):
        """
        Build the state with filtered properties and tenant counts.

        Optimizes queries using prefetch_related to avoid N+1 problems.
        Validates search query length to prevent abuse.
        """
        # Validate search query length
        if query and len(query) > 100:
            query = query[:100]

        # Optimize query with prefetch to avoid N+1
        qs = Property.objects.prefetch_related('tenants').annotate(
            tenant_count=Count('tenants')
        ).order_by('-created_at')

        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(address__icontains=query))

        # Preserve UI buffers
        create_buffer = self.state.create_buffer if hasattr(self, 'state') else None
        edit_buffer = self.state.edit_buffer if hasattr(self, 'state') else None
        editing_id = self.state.editing_id if hasattr(self, 'state') else None

        new_state = PropertyListState(
            search_query=query,
            properties=[PropertySchema.model_validate(p) for p in qs]
        )

        if create_buffer: new_state.create_buffer = create_buffer
        if edit_buffer: new_state.edit_buffer = edit_buffer
        if editing_id: new_state.editing_id = editing_id

        return new_state

    def search(self):
        """Perform search with the current query."""
        self.refresh()