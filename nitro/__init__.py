"""Django Nitro - Reactive components for Django with AlpineJS."""

# Base components
from nitro.base import (
    NitroComponent,
    ModelNitroComponent,
    CrudNitroComponent,
)

# List components (v0.2.1)
from nitro.list import (
    PaginationMixin,
    SearchMixin,
    FilterMixin,
    BaseListState,
    BaseListComponent,
)

# Registry
from nitro.registry import register_component

__version__ = "0.2.1"

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
    # Registry
    "register_component",
]
