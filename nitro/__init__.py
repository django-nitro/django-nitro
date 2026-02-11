"""Django Nitro 0.8 - Server-rendered views with HTMX + Alpine."""

__version__ = "0.8.0"


def __getattr__(name):
    """Lazy imports to avoid AppRegistryNotReady during app loading."""
    if name in ("NitroView", "NitroListView", "NitroModelView", "NitroFormView"):
        from nitro.views import NitroView, NitroListView, NitroModelView, NitroFormView
        return locals()[name]
    if name in ("OrganizationMixin", "PermissionMixin"):
        from nitro.mixins import OrganizationMixin, PermissionMixin
        return locals()[name]
    if name in ("NitroFormMixin", "NitroModelForm", "NitroForm",
                "PhoneField", "CedulaField", "CurrencyField"):
        from nitro.forms import (
            NitroFormMixin, NitroModelForm, NitroForm,
            PhoneField, CedulaField, CurrencyField,
        )
        return locals()[name]
    if name in ("NitroWizard", "WizardStep"):
        from nitro.wizards import NitroWizard, WizardStep
        return locals()[name]
    raise AttributeError(f"module 'nitro' has no attribute {name!r}")


__all__ = [
    "NitroView",
    "NitroListView",
    "NitroModelView",
    "NitroFormView",
    "OrganizationMixin",
    "PermissionMixin",
    "NitroFormMixin",
    "NitroModelForm",
    "NitroForm",
    "PhoneField",
    "CedulaField",
    "CurrencyField",
    "NitroWizard",
    "WizardStep",
]
