"""List components with pagination, search, and filtering for Django Nitro."""
from typing import Optional, TypeVar, Generic, Any
from pydantic import BaseModel, Field
from nitro.base import CrudNitroComponent


T = TypeVar('T', bound=BaseModel)


class PaginationMixin:
    """Mixin for pagination support in list components."""

    def paginate_queryset(self, queryset, page: int = 1, per_page: int = 20):
        """
        Paginate a Django queryset.

        Args:
            queryset: Django queryset to paginate
            page: Page number (1-indexed)
            per_page: Number of items per page

        Returns:
            Dictionary with pagination data:
            - items: List of items for current page
            - page: Current page number
            - num_pages: Total number of pages
            - has_previous: Whether there's a previous page
            - has_next: Whether there's a next page
            - previous_page_number: Previous page number or None
            - next_page_number: Next page number or None
        """
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

        paginator = Paginator(queryset, per_page)

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        return {
            'items': list(page_obj),
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        }


class SearchMixin:
    """Mixin for search functionality in list components."""

    search_fields: list[str] = []  # Override in subclass

    def apply_search(self, queryset, search_query: str):
        """
        Apply search to queryset using Q objects.

        Searches across all fields defined in search_fields using case-insensitive contains.

        Args:
            queryset: Django queryset to filter
            search_query: Search string

        Returns:
            Filtered queryset

        Example:
            class MyList(BaseListComponent):
                search_fields = ['name', 'email', 'description']
        """
        from django.db.models import Q

        if not search_query or not self.search_fields:
            return queryset

        query = Q()
        for field in self.search_fields:
            query |= Q(**{f"{field}__icontains": search_query})

        return queryset.filter(query)


class FilterMixin:
    """Mixin for filtering functionality in list components."""

    def apply_filters(self, queryset, filters: dict):
        """
        Apply filters to queryset.

        Automatically removes empty values (None, '', []) before filtering.

        Args:
            queryset: Django queryset to filter
            filters: Dictionary of field: value pairs

        Returns:
            Filtered queryset

        Example:
            call('set_filters', {category_id: 5, is_active: true})
        """
        if not filters:
            return queryset

        # Remove empty values
        filters = {k: v for k, v in filters.items() if v not in [None, '', []]}

        return queryset.filter(**filters)


class BaseListState(BaseModel):
    """
    Base state for list components with pagination, search, and filters.

    Use this as a base class for your list component states.

    IMPORTANT: You must override create_buffer and edit_buffer with specific types.
    The base class uses 'Any' which will cause errors during edit operations.

    Example:
        from pydantic import Field

        class CompanyFormSchema(BaseModel):
            name: str = ""
            email: str = ""

        class CompanyListState(BaseListState):
            items: list[CompanySchema] = []
            # MUST specify buffer types explicitly:
            create_buffer: CompanyFormSchema = Field(default_factory=CompanyFormSchema)
            edit_buffer: Optional[CompanyFormSchema] = None
    """
    # Items
    items: list[Any] = []

    # Search
    search: str = ""

    # Pagination
    page: int = 1
    per_page: int = 20
    num_pages: int = 1
    has_previous: bool = False
    has_next: bool = False
    previous_page_number: Optional[int] = None
    next_page_number: Optional[int] = None

    # Metadata for UX
    total_count: int = 0        # Total number of results (before pagination)
    showing_start: int = 0      # First item number on current page (e.g., 21)
    showing_end: int = 0        # Last item number on current page (e.g., 40)

    # Filters
    filters: dict = Field(default_factory=dict)

    # CRUD buffers (inherited from CrudNitroComponent)
    create_buffer: Optional[Any] = None
    edit_buffer: Optional[Any] = None
    editing_id: Optional[int] = None


class BaseListComponent(
    Generic[T],
    PaginationMixin,
    SearchMixin,
    FilterMixin,
    CrudNitroComponent[T]
):
    """
    Base component for CRUD list views with pagination, search, and filters.

    Combines all list functionality (pagination, search, filters) with CRUD operations
    from CrudNitroComponent.

    Attributes:
        per_page: Default number of items per page (default: 20)
        order_by: Default ordering (default: '-id')
        search_fields: List of model fields to search (default: [])

    Inherited CRUD methods:
        - create_item()
        - delete_item(id: int)
        - start_edit(id: int)
        - save_edit()
        - cancel_edit()

    List methods:
        - search_items(search: str)
        - set_filters(**filters)
        - clear_filters()
        - next_page()
        - previous_page()
        - go_to_page(page: int)
        - set_per_page(per_page: int)

    Example:
        class CompanyListState(BaseListState):
            items: list[CompanySchema] = []

        @register_component
        class CompanyList(BaseListComponent[CompanyListState]):
            state_class = CompanyListState
            model = Company
            search_fields = ['name', 'email']
            template_name = "components/company_list.html"
            per_page = 20
            order_by = '-created_at'
    """

    per_page: int = 20
    order_by: str = '-id'

    def get_initial_state(self, **kwargs):
        """
        Get initial state with paginated items.

        Accepts optional kwargs:
            - page: Page number (default: 1)
            - search: Search query (default: '')
            - filters: Filter dict (default: {})
            - per_page: Items per page (default: self.per_page)
        """
        page = kwargs.get('page', 1)
        search = kwargs.get('search', '')
        filters = kwargs.get('filters', {})
        per_page = kwargs.get('per_page', self.per_page)

        queryset = self.get_base_queryset(search=search, filters=filters)
        total_count = queryset.count()
        pagination_data = self.paginate_queryset(queryset, page, per_page)

        # Convert items to Pydantic schemas
        from pydantic import TypeAdapter
        schema_list = TypeAdapter(list[self.state_class.model_fields['items'].annotation.__args__[0]])
        items = schema_list.validate_python([
            item.__dict__ if hasattr(item, '__dict__') else item
            for item in pagination_data['items']
        ])

        # Calculate showing range for UX (e.g., "Showing 21-40 of 150")
        showing_start = (pagination_data['page'] - 1) * per_page + 1 if items else 0
        showing_end = showing_start + len(items) - 1 if items else 0

        return self.state_class(
            items=items,
            search=search,
            filters=filters,
            page=pagination_data['page'],
            per_page=per_page,
            num_pages=pagination_data['num_pages'],
            has_previous=pagination_data['has_previous'],
            has_next=pagination_data['has_next'],
            previous_page_number=pagination_data['previous_page_number'],
            next_page_number=pagination_data['next_page_number'],
            total_count=total_count,
            showing_start=showing_start,
            showing_end=showing_end,
        )

    def get_base_queryset(self, search: str = '', filters: dict = None):
        """
        Get base queryset with filters applied.

        Override this method to customize filtering logic.

        Args:
            search: Search query string
            filters: Dictionary of filters

        Returns:
            Filtered and ordered queryset

        Example:
            def get_base_queryset(self, search='', filters=None):
                # Only show items owned by current user
                qs = self.model.objects.filter(owner=self.request.user)

                if search:
                    qs = self.apply_search(qs, search)

                if filters:
                    qs = self.apply_filters(qs, filters)

                return qs.order_by(self.order_by)
        """
        queryset = self.model.objects.all()

        # Apply search
        if search:
            queryset = self.apply_search(queryset, search)

        # Apply filters
        if filters:
            queryset = self.apply_filters(queryset, filters)

        # Apply ordering
        if self.order_by:
            queryset = queryset.order_by(self.order_by)

        return queryset

    def get_queryset(self):
        """
        Get queryset using current state.

        Used after initialization to get the current queryset.
        """
        return self.get_base_queryset(
            search=self.state.search,
            filters=self.state.filters
        )

    def refresh(self):
        """
        Reload items from database.

        Updates all pagination metadata and item list from current queryset.
        """
        queryset = self.get_queryset()
        total_count = queryset.count()
        pagination_data = self.paginate_queryset(queryset, self.state.page, self.state.per_page)

        from pydantic import TypeAdapter
        schema_list = TypeAdapter(list[self.state_class.model_fields['items'].annotation.__args__[0]])
        items = schema_list.validate_python([
            item.__dict__ if hasattr(item, '__dict__') else item
            for item in pagination_data['items']
        ])

        # Calculate showing range
        showing_start = (pagination_data['page'] - 1) * self.state.per_page + 1 if items else 0
        showing_end = showing_start + len(items) - 1 if items else 0

        self.state.items = items
        self.state.page = pagination_data['page']
        self.state.num_pages = pagination_data['num_pages']
        self.state.has_previous = pagination_data['has_previous']
        self.state.has_next = pagination_data['has_next']
        self.state.previous_page_number = pagination_data['previous_page_number']
        self.state.next_page_number = pagination_data['next_page_number']
        self.state.total_count = total_count
        self.state.showing_start = showing_start
        self.state.showing_end = showing_end

    def search_items(self, search: str):
        """
        Update search query and refresh.

        Automatically resets to page 1.

        Args:
            search: Search query string

        Example:
            <input
                x-model="search"
                @input.debounce.300ms="call('search_items', {search: $el.value})"
            >
        """
        self.state.search = search
        self.state.page = 1  # Reset to first page when searching
        self.refresh()

    def set_filters(self, **filters):
        """
        Update filters and refresh.

        Automatically resets to page 1.

        Args:
            **filters: Filter key-value pairs

        Example:
            call('set_filters', {category_id: 5, is_active: true})
        """
        self.state.filters.update(filters)
        self.state.page = 1  # Reset to first page when filtering
        self.refresh()

    def clear_filters(self):
        """
        Clear all filters and search, then refresh.

        Resets to page 1.

        Example:
            <button @click="call('clear_filters')">Clear All</button>
        """
        self.state.filters = {}
        self.state.search = ""
        self.state.page = 1
        self.refresh()

    def go_to_page(self, page: int):
        """
        Navigate to specific page.

        Args:
            page: Page number to navigate to

        Example:
            call('go_to_page', {page: 3})
        """
        self.state.page = page
        self.refresh()

    def next_page(self):
        """
        Go to next page.

        Does nothing if already on last page.

        Example:
            <button
                @click="call('next_page')"
                :disabled="!has_next || isLoading"
            >
                Next
            </button>
        """
        if self.state.has_next:
            self.go_to_page(self.state.next_page_number)

    def previous_page(self):
        """
        Go to previous page.

        Does nothing if already on first page.

        Example:
            <button
                @click="call('previous_page')"
                :disabled="!has_previous || isLoading"
            >
                Previous
            </button>
        """
        if self.state.has_previous:
            self.go_to_page(self.state.previous_page_number)

    def set_per_page(self, per_page: int):
        """
        Change items per page and refresh.

        Automatically resets to page 1.

        Args:
            per_page: Number of items per page

        Example:
            <select
                x-model="per_page"
                @change="call('set_per_page', {per_page: parseInt($el.value)})"
            >
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
            </select>
        """
        self.state.per_page = per_page
        self.state.page = 1  # Reset to first page
        self.refresh()
