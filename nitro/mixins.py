"""
Django Nitro 0.8 - Reusable mixins for multi-tenancy and permissions.

These are generic, framework-level mixins. Projects customize them
by subclassing and setting org_field, get_organization(), etc.
"""

import logging

logger = logging.getLogger(__name__)


class OrganizationMixin:
    """
    Generic multi-tenant mixin. Works for companies, ONGs, schools, etc.

    Subclass and implement get_organization() for your project.

    Usage:
        class CompanyMixin(OrganizationMixin):
            org_field = 'company'

            def get_organization(self):
                # your logic to get the user's company
                return self.request.user.company
    """

    org_field = 'company'   # FK field name on models

    _cached_organization = None
    _org_loaded = False

    @property
    def organization(self):
        """Cached organization for the current request."""
        if not self._org_loaded:
            self._cached_organization = self.get_organization()
            self._org_loaded = True
        return self._cached_organization

    def get_organization(self):
        """
        Return the organization for the current user.
        Must be implemented by subclasses.
        """
        raise NotImplementedError(
            "Subclasses must implement get_organization()"
        )

    def get_queryset(self):
        """Auto-filter queryset by organization."""
        qs = super().get_queryset()
        return self.filter_by_organization(qs)

    def filter_by_organization(self, qs):
        """Filter a queryset by the current organization."""
        org = self.organization
        if org is None:
            return qs
        # Try direct FK
        if hasattr(self, 'model') and self.model and hasattr(self.model, self.org_field):
            return qs.filter(**{self.org_field: org})
        return qs


class PermissionMixin:
    """
    Abstract RBAC mixin. Subclass and implement check_permission().

    Usage:
        class MyView(PermissionMixin, NitroListView):
            required_permission = ('properties', 'view_all')

            def check_permission(self, module, action):
                perm = self.request.user.get_permission()
                return perm.has_permission(module, action)
    """

    required_permission = None  # Tuple of (module, action) or None

    def check_permission(self, module, action):
        """Check if user has permission. Override in subclass."""
        raise NotImplementedError(
            "Subclasses must implement check_permission()"
        )

    def require_permission(self, module, action, msg=None):
        """Raise PermissionDenied if user lacks permission."""
        from django.core.exceptions import PermissionDenied
        if not self.check_permission(module, action):
            raise PermissionDenied(
                msg or f"No tienes permiso para {action} en {module}"
            )

    def dispatch(self, request, *args, **kwargs):
        if self.required_permission:
            module, action = self.required_permission
            self.require_permission(module, action)
        return super().dispatch(request, *args, **kwargs)
