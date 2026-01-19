# Changelog

All notable changes to Django Nitro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-01-19

### Philosophy Change: True Zero-JavaScript + DX Improvements

This release fundamentally changes Nitro's approach. Previous versions wrapped JavaScript
in template tags, still requiring developers to know JS syntax. **Version 0.7.0 is truly
Zero-JS** - all logic is defined in Python, no JavaScript knowledge required.

### Added - DX Improvements

- **Auto-infer `state_class`** - No more redundant `state_class = MyState` when using Generics:
  ```python
  # Before
  class Counter(NitroComponent[CounterState]):
      state_class = CounterState  # REDUNDANT!

  # After (v0.7.0)
  class Counter(NitroComponent[CounterState]):
      pass  # state_class inferred automatically
  ```

- **`CacheMixin`** - Component state and HTML caching for performance:
  ```python
  from nitro import CacheMixin, NitroComponent

  class MyComponent(CacheMixin, NitroComponent[MyState]):
      cache_enabled = True
      cache_ttl = 300  # 5 minutes
      cache_html = True  # Also cache rendered HTML
  ```

- **`@cache_action` decorator** - Cache expensive action results:
  ```python
  from nitro.cache import cache_action

  @cache_action(ttl=120)
  def load_expensive_data(self):
      return expensive_calculation()
  ```

- **`nitro_phone` / `n_phone`** - Phone input with automatic XXX-XXX-XXXX mask:
  ```django
  {% n_phone field="form.phone" label="Teléfono" %}
  ```

- **Unaccent search** - Accent-insensitive search (PostgreSQL):
  ```python
  # "maria" now finds "María", "jose" finds "José"
  class MyList(BaseListComponent[MyState]):
      search_fields = ['name', 'email']
      use_unaccent = True  # Default: True
  ```

- **`nitro_text` as attribute** - Now outputs just the attribute, not a full element:
  ```django
  <!-- Before (broken with extra attributes) -->
  {% nitro_text 'name' %}  <!-- Output: <span x-text="name"></span> -->

  <!-- After (works anywhere) -->
  <h1 {% nitro_text 'name' %} class="font-bold"></h1>
  ```

### Added - Zero-JS Template Tags

New tags where ALL logic is defined in Python kwargs:

- **`{% nitro_switch %}`** - Conditional text based on field value
  ```django
  {% nitro_switch 'item.status' active='Activo' expired='Vencido' default='Borrador' %}
  ```

- **`{% nitro_css %}`** - Conditional CSS classes
  ```django
  <div {% nitro_css 'item.status' active='bg-green-100' expired='bg-red-100' %}>
  ```

- **`{% nitro_badge %}`** - Combined text + styling for status badges
  ```django
  {% nitro_badge 'status' active='Activo:bg-green-100' expired='Vencido:bg-red-100' %}
  ```

- **`{% nitro_visible %}`** / **`{% nitro_hidden %}`** - Boolean visibility
  ```django
  <div {% nitro_visible 'item.is_active' %}>Shown when active</div>
  ```

- **`{% nitro_plural %}`** - Singular/plural text
  ```django
  {% nitro_plural 'count' singular='item' plural='items' zero='No items' %}
  ```

- **`{% nitro_count %}`** - Count with label
  ```django
  {% nitro_count 'items.length' singular='propiedad' plural='propiedades' %}
  ```

- **`{% nitro_format %}`** - Value formatting (currency, numbers)
  ```django
  {% nitro_format 'price' format_type='currency' prefix='$' %}
  ```

- **`{% nitro_date %}`** - Date formatting
  ```django
  {% nitro_date 'created_at' empty='Sin fecha' %}
  ```

- **`{% nitro_each %}`** - Zero-JS iteration
  ```django
  {% nitro_each 'items' as 'item' %}...{% end_nitro_each %}
  ```

- **`{% nitro_call %}`** - Call component Python methods
  ```django
  {% nitro_call 'get_status_display' item %}
  ```

### Deprecated

The following tags still work but are deprecated (will be removed in v1.0):

| Deprecated Tag | Replacement | Reason |
|---------------|-------------|--------|
| `{% nitro_bind "js expr" %}` | `{% nitro_switch %}` | Required JS knowledge |
| `{% nitro_class_map "js obj" %}` | `{% nitro_css %}` | Required JS knowledge |

### Migration Examples

**Before (v0.6.x):**
```django
{% nitro_bind "item.status === 'active' ? 'Activo' : 'Inactivo'" %}
{% nitro_class_map "{'bg-green-100': item.status === 'active'}" %}
```

**After (v0.7.0):**
```django
{% nitro_switch 'item.status' active='Activo' default='Inactivo' %}
{% nitro_css 'item.status' active='bg-green-100' %}
```

## [0.6.2] - 2025-12-15

### Fixed
- Fixed issue with optional fields in Pydantic schemas
- Improved error messages for missing components

## [0.6.1] - 2025-12-10

### Added
- Support for custom error templates
- Debug toolbar panel for Nitro components

### Fixed
- Fixed issue with file uploads in nested forms

## [0.6.0] - 2025-12-01

### Added
- **Migration System** - Automatic migration helpers for component updates
- **COMPONENTS.md** - Component documentation generator
- **Enhanced Security** - CSRF validation improvements
- **Pydantic V2 Support** - Full compatibility with Pydantic v2

### Changed
- Improved component rendering performance
- Better TypeScript type hints in generated JS

## [0.5.0] - 2025-11-15

### Added
- `NitroList` base component for paginated lists
- `SearchMixin`, `FilterMixin`, `PaginationMixin`
- Slide-over panel support
- Toast notifications system

## [0.4.0] - 2025-11-01

### Added
- Configuration system via `settings.NITRO`
- Custom template directory support
- Component caching options

## [0.3.0] - 2025-10-15

### Added
- Security mixins: `OwnershipMixin`, `TenantScopedMixin`, `PermissionMixin`
- Multi-tenant support

## [0.2.0] - 2025-10-01

### Added
- `BaseListComponent` for CRUD lists
- Pagination support
- Search functionality

## [0.1.0] - 2025-09-15

### Added
- Initial release
- `NitroComponent` base class
- `ModelNitroComponent` for model-backed components
- Template tags: `nitro_component`, `nitro_scripts`, `nitro_model`, `nitro_action`
- Alpine.js integration
- Pydantic state management
