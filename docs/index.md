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
    # state_class auto-inferred from Generic (v0.7.0)

    def get_initial_state(self, **kwargs):
        return CounterState(count=0)

    def increment(self):
        self.state.count += 1
        self.success(f"Count: {self.state.count}")
```

```html
<!-- templates/components/counter.html -->
{% load nitro_tags %}

<div>
    <h2>{% nitro_text 'count' %}</h2>
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

### Security & Authentication

- **[OwnershipMixin](security/ownership-mixin.md)** - Filter to current user's data
- **[TenantScopedMixin](security/tenant-scoped-mixin.md)** - Multi-tenant isolation
- **[PermissionMixin](security/permission-mixin.md)** - Custom permission framework

### New in v0.7.0 ⭐

- **Auto-infer `state_class`** - No more redundant declarations when using Generics
- **CacheMixin** - Component state and HTML caching for performance
- **@cache_action decorator** - Cache expensive action results
- **Unaccent Search** - Accent-insensitive search for PostgreSQL (enabled by default)
- **True Zero-JS Template Tags** - All logic in Python kwargs:
  - `{% nitro_switch %}` - Conditional text based on field value
  - `{% nitro_css %}` - Conditional CSS classes
  - `{% nitro_badge %}` - Combined text + styling
  - `{% nitro_visible %}` / `{% nitro_hidden %}` - Boolean visibility
  - `{% nitro_plural %}` / `{% nitro_count %}` - Pluralization
  - `{% nitro_format %}` / `{% nitro_date %}` - Value formatting

### Previous Releases

#### v0.6.0

- **Form Field Template Tags** - `{% nitro_input %}`, `{% nitro_select %}`, `{% nitro_checkbox %}`, `{% nitro_textarea %}`
- **Default Debounce (200ms)** - Automatic debouncing on `nitro_model`
- **Django 5.2 Support** - Compatible using `django-template-partials`

#### v0.4.0

- **[Toast Notifications](core-concepts/TOAST_ADAPTERS.md)** - Native toasts or integrate your favorite library
- **[Events System](core-concepts/events.md)** - Component-to-component communication with `emit()` and `refresh_component()`
- **[CLI Scaffolding](core-concepts/cli-tools.md)** - Generate components with `python manage.py startnitro`
- **[SEO Template Tags](core-concepts/template-tags.md)** - Server-side rendering with `{% nitro_for %}` and `{% nitro_text %}`
- **[Smart State Updates](core-concepts/smart-updates.md)** - Performance optimization with state diffing for large lists
- **Configuration System** - Centralized NITRO settings with fallbacks

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
