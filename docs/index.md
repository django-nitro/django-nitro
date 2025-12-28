# Django Nitro 🚀

**Build reactive Django components with AlpineJS - No JavaScript required**

Django Nitro is a modern library for building reactive, stateful components in Django applications. Inspired by Django Unicorn and Laravel Livewire, but built on top of AlpineJS and Django Ninja for a lightweight, performant experience.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2+](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)

## Why Django Nitro?

- ✅ **Zero JavaScript** - Write reactive UIs entirely in Python
- ✅ **Type-Safe** - Full Pydantic integration with generics for bulletproof state management
- ✅ **Secure by Default** - Built-in integrity verification prevents client-side tampering
- ✅ **Lightweight** - AlpineJS (~15KB) vs Morphdom (~50KB)
- ✅ **Fast** - Django Ninja API layer for optimal performance
- ✅ **DRY** - Pre-built CRUD operations and security mixins

## Quick Example

```python
from pydantic import BaseModel
from nitro.base import NitroComponent
from nitro.registry import register_component

class CounterState(BaseModel):
    count: int = 0

@register_component
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    state_class = CounterState

    def get_initial_state(self, **kwargs):
        return CounterState(count=0)

    def increment(self):
        self.state.count += 1
        self.success(f"Count: {self.state.count}")
```

```html
<!-- templates/components/counter.html -->
<div>
    <h2 x-text="count"></h2>
    <button @click="call('increment')" :disabled="isLoading">
        Increment
    </button>
</div>
```

**That's it!** No JavaScript required, fully reactive.

## Features

### Component Types

- **[NitroComponent](components/nitro-component.md)** - Base component for custom logic
- **[ModelNitroComponent](components/model-nitro-component.md)** - Django ORM integration
- **[CrudNitroComponent](components/crud-nitro-component.md)** - Pre-built CRUD operations
- **[BaseListComponent](components/base-list-component.md)** - Pagination, search, and filters

### Security Mixins (v0.3.0)

- **[OwnershipMixin](security/ownership-mixin.md)** - Filter to current user's data
- **[TenantScopedMixin](security/tenant-scoped-mixin.md)** - Multi-tenant isolation
- **[PermissionMixin](security/permission-mixin.md)** - Custom permission framework

## Getting Started

[Installation →](getting-started/installation.md){ .md-button .md-button--primary }
[Quick Start →](getting-started/quick-start.md){ .md-button }
[Examples →](examples/counter.md){ .md-button }

## Community

- **[GitHub](https://github.com/django-nitro/django-nitro)** - Source code and issues
- **[Examples](examples/counter.md)** - Live demos and code samples
- **[Contributing](contributing.md)** - Help improve Django Nitro

---

**Built with ❤️ for the Django community**
