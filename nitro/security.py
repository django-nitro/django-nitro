"""Security mixins for Django Nitro components.

This module provides reusable mixins for common security patterns:
- OwnershipMixin: Filter data by current user
- TenantScopedMixin: Multi-tenant data isolation
- PermissionMixin: Permission checking framework
"""
from typing import Optional


class OwnershipMixin:
    """
    Filter queryset to show only current user's data.

    Common pattern for user-scoped data like "My Orders", "My Documents", etc.

    Attributes:
        owner_field: Name of the ForeignKey field pointing to User model.
                    Default: 'user'. Override in subclass if different.

    Example:
        from nitro.security import OwnershipMixin
        from nitro.list import BaseListComponent

        class MyOrdersList(OwnershipMixin, BaseListComponent):
            model = Order
            owner_field = 'customer'  # if FK is named 'customer' instead of 'user'

            def get_base_queryset(self, search='', filters=None):
                # Start with user's data only
                qs = self.filter_by_owner(self.model.objects.all())

                if search:
                    qs = self.apply_search(qs, search)

                return qs.order_by(self.order_by)
    """

    owner_field: str = 'user'  # Override in subclass if needed

    def filter_by_owner(self, queryset):
        """
        Filter queryset to current user's data only.

        Args:
            queryset: Django queryset to filter

        Returns:
            Filtered queryset showing only current user's data.
            Returns empty queryset if user is not authenticated.

        Example:
            qs = Order.objects.all()
            qs = self.filter_by_owner(qs)  # Now only shows current user's orders
        """
        if not self.request or not self.request.user.is_authenticated:
            return queryset.none()

        filter_kwargs = {self.owner_field: self.request.user}
        return queryset.filter(**filter_kwargs)


class TenantScopedMixin:
    """
    Filter by tenant/organization for multi-tenant SaaS applications.

    Provides data isolation in multi-tenant architectures where users belong
    to organizations/companies and should only see their organization's data.

    Attributes:
        tenant_field: Name of the ForeignKey field pointing to the tenant model.
                     Default: 'organization'. Override in subclass.

    Example:
        from nitro.security import TenantScopedMixin
        from nitro.list import BaseListComponent

        class CompanyDocumentList(TenantScopedMixin, BaseListComponent):
            model = Document
            tenant_field = 'company'

            def get_user_tenant(self):
                # Get user's current company from session or profile
                return self.request.user.profile.current_company

            def get_base_queryset(self, search='', filters=None):
                # Automatically filtered to current company
                qs = self.filter_by_tenant(self.model.objects.all())
                return qs.order_by(self.order_by)
    """

    tenant_field: str = 'organization'  # Override in subclass

    def get_user_tenant(self):
        """
        Get the current user's tenant/organization.

        MUST be overridden in subclass to return the tenant object.

        Returns:
            The tenant/organization object for the current user,
            or None if user has no tenant.

        Raises:
            NotImplementedError: This method must be overridden.

        Example:
            def get_user_tenant(self):
                # From user profile
                return self.request.user.current_organization

                # Or from session
                org_id = self.request.session.get('active_company_id')
                return Company.objects.get(id=org_id)

                # Or from related model
                return self.request.user.company_membership.company
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_user_tenant() "
            "to return the current tenant/organization"
        )

    def filter_by_tenant(self, queryset):
        """
        Filter queryset by current tenant.

        Args:
            queryset: Django queryset to filter

        Returns:
            Filtered queryset showing only current tenant's data.
            Returns empty queryset if user has no tenant.

        Example:
            qs = Invoice.objects.all()
            qs = self.filter_by_tenant(qs)  # Only current company's invoices
        """
        tenant = self.get_user_tenant()
        if not tenant:
            return queryset.none()

        filter_kwargs = {self.tenant_field: tenant}
        return queryset.filter(**filter_kwargs)


class PermissionMixin:
    """
    Base mixin for permission checking in components.

    Provides a framework for implementing custom permission logic.
    Subclasses override check_permission() with their specific rules.

    Example:
        from nitro.security import PermissionMixin
        from nitro.base import CrudNitroComponent

        class InvoiceManager(PermissionMixin, CrudNitroComponent):
            model = Invoice

            def check_permission(self, action: str) -> bool:
                '''Check if user can perform action.'''
                user = self.request.user

                if action == 'create':
                    return user.has_perm('invoices.add_invoice')

                if action == 'delete':
                    return user.has_perm('invoices.delete_invoice')

                if action == 'edit':
                    # Custom logic: can only edit own invoices
                    return user.has_perm('invoices.change_invoice')

                return True  # Allow by default

            def delete_item(self, id: int):
                # Enforce permission before deleting
                if not self.enforce_permission('delete'):
                    return

                super().delete_item(id)

    Advanced Example (RBAC):
        class DocumentManager(PermissionMixin, CrudNitroComponent):
            def check_permission(self, action: str) -> bool:
                '''Role-based permissions.'''
                role = self.request.user.role

                permissions = {
                    'admin': ['create', 'edit', 'delete', 'view'],
                    'editor': ['create', 'edit', 'view'],
                    'viewer': ['view'],
                }

                return action in permissions.get(role, [])
    """

    def check_permission(self, action: str) -> bool:
        """
        Check if current user has permission for an action.

        MUST be overridden in subclass with your permission logic.

        Args:
            action: The action being performed (e.g., 'create', 'edit', 'delete', 'view')

        Returns:
            True if user has permission, False otherwise

        Raises:
            NotImplementedError: This method must be overridden.

        Example:
            def check_permission(self, action: str) -> bool:
                if action == 'delete':
                    return self.request.user.is_staff
                return True
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement check_permission(action) "
            "with your permission logic"
        )

    def enforce_permission(self, action: str, error_message: Optional[str] = None) -> bool:
        """
        Enforce permission check with user feedback.

        Calls check_permission() and shows error message if denied.

        Args:
            action: The action being performed
            error_message: Custom error message. Default: "Permission denied"

        Returns:
            True if permission granted, False if denied

        Example:
            def delete_item(self, id: int):
                if not self.enforce_permission('delete', "You cannot delete invoices"):
                    return  # Permission denied, error shown to user

                # Permission granted, proceed with deletion
                super().delete_item(id)
        """
        if not self.check_permission(action):
            message = error_message or "Permission denied"
            self.error(message)
            return False

        return True
