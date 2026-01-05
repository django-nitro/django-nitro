# Changelog

All notable changes to Django Nitro are documented here.

For the complete changelog, see [CHANGELOG.md](https://github.com/django-nitro/django-nitro/blob/main/CHANGELOG.md) on GitHub.

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
