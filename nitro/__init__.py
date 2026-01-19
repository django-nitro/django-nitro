"""Django Nitro - Reactive components for Django with AlpineJS."""

# Base components
from nitro.base import (
    CrudNitroComponent,
    ModelNitroComponent,
    NitroComponent,
)

# Cache (v0.7.0)
from nitro.cache import (
    CacheMixin,
    cache_action,
)

# Configuration (v0.4.0)
from nitro.conf import (
    get_all_settings,
    get_setting,
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

__version__ = "0.7.0"

__all__ = [
    # Base
    "NitroComponent",
    "ModelNitroComponent",
    "CrudNitroComponent",
    # Cache (v0.7.0)
    "CacheMixin",
    "cache_action",
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
    # Configuration
    "get_setting",
    "get_all_settings",
]
