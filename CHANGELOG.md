# Changelog

All notable changes to Django Nitro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  - Comprehensive README files for each example

### Changed
- Reorganized examples into separate standalone projects
- **Documentation Site** - Added MkDocs Material documentation
  - Auto-deployed to GitHub Pages
  - Comprehensive guides for all features
  - Security mixins documentation
  - Examples and tutorials

### Fixed
- Updated GitHub Actions to use v4/v5 (artifact-actions deprecation)

## [0.2.1] - 2025-12-28

### Added
- Support for Django 6.0 and Python 3.14
### Fixed
- Fix the Github reference in pyproject.toml file

## [0.2.0] - 2025-12-27

### Added
- `BaseListComponent` for CRUD list views with pagination, search, and filters
- `PaginationMixin` for Django queryset pagination
- `SearchMixin` for full-text search across configurable fields
- `FilterMixin` for dynamic queryset filtering
- `BaseListState` with complete pagination metadata (total_count, showing_start, showing_end, etc.)
- Navigation methods: `next_page()`, `previous_page()`, `go_to_page()`, `set_per_page()`
- Search and filter management: `search_items()`, `set_filters()`, `clear_filters()`
- Automatic page reset when search/filters change
- Full integration with existing `CrudNitroComponent` functionality

## [0.1.0] - 2024-XX-XX

### Added
- Initial release of Django Nitro
- `NitroComponent` base class for reactive components
- `ModelNitroComponent` for Django ORM integration
- `CrudNitroComponent` with pre-built CRUD operations
- AlpineJS integration via `nitro.js`
- Django Ninja API endpoint for component dispatch
- Pydantic-based state validation with full type safety
- Built-in integrity verification for secure fields
- Automatic state synchronization between server and client
- Support for component actions with parameters
- Messages system for success/error notifications
- Field-level error handling
- Example project with Property and Tenant management

### Security
- HMAC-based integrity tokens to prevent client-side tampering
- Automatic protection for `id` fields and foreign keys
- CSRF token integration with Django





