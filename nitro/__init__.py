"""Django Nitro - Reactive components for Django with AlpineJS."""

# Base components
from nitro.base import (
    CrudNitroComponent,
    ModelNitroComponent,
    NitroComponent,
)

# List components (v0.2.0)
from nitro.list import (
    BaseListComponent,
    BaseListState,
    FilterMixin,
    PaginationMixin,
    SearchMixin,
)

# Registry
from nitro.registry import register_component

# Security mixins (v0.3.0)
from nitro.security import (
    OwnershipMixin,
    PermissionMixin,
    TenantScopedMixin,
)

__version__ = "0.3.0"

__all__ = [
    # Base
    "NitroComponent",
    "ModelNitroComponent",
    "CrudNitroComponent",
    # List
    "PaginationMixin",
    "SearchMixin",
    "FilterMixin",
    "BaseListState",
    "BaseListComponent",
    # Security
    "OwnershipMixin",
    "TenantScopedMixin",
    "PermissionMixin",
    # Registry
    "register_component",
]
