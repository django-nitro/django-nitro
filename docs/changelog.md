# Changelog

All notable changes to Django Nitro are documented here.

For the complete changelog, see [CHANGELOG.md](https://github.com/django-nitro/django-nitro/blob/main/CHANGELOG.md) on GitHub.

## [0.7.0] - 2026-01-19

### Added - DX Improvements

- **Auto-infer `state_class`** - No more redundant declarations when using Generics
- **`CacheMixin`** - Component state and HTML caching for performance
- **`@cache_action` decorator** - Cache expensive action results
- **`nitro_phone` / `n_phone`** - Phone input with automatic XXX-XXX-XXXX mask
- **Unaccent search** - Accent-insensitive search for PostgreSQL (enabled by default)
- **`nitro_text` as attribute** - Now outputs just the attribute, works with other attributes

### Added - Zero-JS Template Tags

- `{% nitro_switch %}` - Conditional text based on field value
- `{% nitro_css %}` - Conditional CSS classes
- `{% nitro_badge %}` - Combined text + styling for status badges
- `{% nitro_visible %}` / `{% nitro_hidden %}` - Boolean visibility
- `{% nitro_plural %}` / `{% nitro_count %}` - Pluralization
- `{% nitro_format %}` / `{% nitro_date %}` - Value formatting
- `{% nitro_each %}` - Zero-JS iteration

### Fixed

- `_get_state_class()` for BaseListComponent - Generic type inference now works in classmethods

## [0.6.2] - 2026-01-16

### Fixed

#### Critical UI/UX Bug Fixes
- **Fixed loading indicator flash during field sync** - Added `silent` mode option to `call()` method
  - Background operations like `_sync_field` no longer show loading indicator
  - Usage: `call('action', payload, null, {silent: true})`
  - Improves perceived performance during typing

- **Fixed x-model binding in form field templates** - Changed from `safe_field` to `field`
  - `x-model` requires direct field access for write operations
  - `safe_field` (with optional chaining `?.`) only works for reading
  - Affects: `nitro_input`, `nitro_select`, `nitro_checkbox`, `nitro_textarea`

- **Fixed state flicker on field sync** - Improved merge behavior in `nitro.js`
  - `_sync_field` responses now skip state update (client already has correct value from x-model)
  - Prevents UI flicker when typing in form fields
  - Only validation errors are processed from sync responses

#### Performance Improvements
- **Added input debouncing to field templates** - 200ms debounce on input/textarea
  - Reduces server calls during rapid typing
  - Consistent with `nitro_model` default debounce behavior

### Changed
- `call()` method signature: `call(actionName, payload, file, options)` - added `options` parameter
- Form field templates now use proper x-model binding for two-way data flow

## [0.6.1] - 2026-01-13

### Added
- **Comprehensive Test Suite** - 24 new tests covering v0.6.0 features
  - Form field template tags tests (nitro_input, nitro_select, nitro_checkbox, nitro_textarea)
  - SEO template tags tests (nitro_text, nitro_for with XSS protection)
  - Component rendering tests (nitro_component, nitro_scripts)
  - Conditional rendering tests (nitro_if)
  - Utility functions tests with 100% coverage
  - Message handling tests (success, error, info, warning)

### Fixed
- **CI/CD Pipeline** - All checks now passing
  - Fixed ruff linting issues (import sorting, exception handling)
  - Applied consistent code formatting across all files
  - Fixed mkdocs build warnings and broken links
- **Test Compatibility** - Updated `test_process_action_invalid` to match graceful error handling
  - Changed from expecting `ValueError` exception to checking error response dict
  - Aligns with production behavior where errors return JSON instead of raising exceptions

### Improved
- **Test Coverage** - Significant coverage improvements
  - Overall coverage: 46% → 59% (+13%)
  - nitro_tags.py: 49% → 88% (+39%)
  - utils.py: 44% → 100% (+56%)
  - Total tests: 41 → 65 (+24 new tests)

### Documentation
- Updated all examples to use Nitro template tags instead of raw Alpine.js
  - Counter example now uses `{% nitro_text %}` for display
  - Contact form uses `{% nitro_input %}` and `{% nitro_textarea %}`
  - CRUD examples use form field tags throughout
- Fixed broken documentation links in smart-updates.md and zero-javascript-mode.md

## [0.6.0] - 2026-01-13

### Added
- **Form Field Template Tags** - Pre-built tags for common form fields
  - `{% nitro_input %}` - Text, email, number, date, tel inputs with error handling
  - `{% nitro_select %}` - Dropdown with choices support
  - `{% nitro_checkbox %}` - Checkbox with label
  - `{% nitro_textarea %}` - Multi-line text input
  - All tags include automatic error display and Bootstrap styling
  - Support for edit buffers and nested fields
- **Default Debounce (200ms)** - `nitro_model` now includes 200ms debounce by default
  - Reduces server load and improves performance
  - Use `no_debounce=True` to disable when instant sync is needed
- **Code Deduplication** - New `nitro/utils.py` module
  - `build_error_path()` - Builds Alpine.js error paths with optional chaining
  - `build_safe_field()` - Builds safe field paths for edit buffers
  - Eliminates ~48 lines of duplicated code across template tags
- **TypeAdapter Caching** - Performance optimization in `BaseListComponent`
  - Class-level cache for Pydantic TypeAdapter (~1-5ms saved per request)
  - Automatically applied in `get_initial_state()` and `refresh()` methods

### Changed
- Django 5.2 compatibility using `django-template-partials`
  - Install with: `pip install django-nitro[django52]`
  - Django 6.0+ uses built-in template partials
- Updated template tag implementations to use utility functions
- Improved form field templates with consistent styling

### Documentation
- Added comprehensive Form Field Template Tags section to README
- New contact-form example demonstrating all form field tags
- Updated examples README with learning path
- Added Django 5.2 compatibility instructions

## [0.5.1] - 2026-01-04

### Fixed
- **Security mixins now work automatically** - No manual `get_base_queryset()` override needed
- **Fixed Alpine.js initialization error** in `{% nitro_for %}` tag
- **State variables unpacked to root** - Use `{{ items }}` instead of `{{ state.items }}`
- **Custom JSON encoder** - Auto-handles UUID, datetime, date, Decimal
- **Pydantic v2 validation** - Field validation now works correctly
- **Added email-validator** dependency

### Documentation
- Updated security mixin docs with v0.5.1 automatic filtering
- Added NitroJSONEncoder documentation
- Updated BaseListComponent examples

## [0.3.0] - 2025-12-28

### Added
- **Security Mixins** for common authentication and authorization patterns
  - `OwnershipMixin` - Filter querysets to show only current user's data
  - `TenantScopedMixin` - Multi-tenant data isolation for SaaS applications
  - `PermissionMixin` - Framework for custom permission logic
- **Request User Helpers** in `NitroComponent` base class
  - `current_user` property - Shortcut to `request.user` with auth check
  - `is_authenticated` property - Check if user is authenticated
  - `require_auth()` method - Enforce authentication with error message
- **Examples Reorganization**
  - Moved `example/` to `examples/property-manager/`
  - Added `examples/counter/` - Simple counter example for beginners
  - Each example is now a standalone Django project

### Changed
- Reorganized examples into separate standalone projects
- Updated documentation with security patterns

### Fixed
- Updated GitHub Actions to v4/v5 (artifact-actions deprecation)

## [0.2.0] - 2025-12-27

### Added
- `BaseListComponent` for CRUD list views with pagination, search, and filters
- `PaginationMixin` for Django queryset pagination
- `SearchMixin` for full-text search across configurable fields
- `FilterMixin` for dynamic queryset filtering
- Navigation methods: `next_page()`, `previous_page()`, `go_to_page()`, `set_per_page()`

## [0.1.0] - Initial Release

### Added
- `NitroComponent` base class for reactive components
- `ModelNitroComponent` for Django ORM integration
- `CrudNitroComponent` with pre-built CRUD operations
- AlpineJS integration
- Django Ninja API endpoint
- Pydantic-based state validation
- Built-in integrity verification
- File upload support

[View full changelog →](https://github.com/django-nitro/django-nitro/blob/main/CHANGELOG.md)
