# Changelog

All notable changes to Django Nitro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-01-18

### Added
- **New Template Tags**:
  - `{% nitro_class_map %}` - Conditional CSS classes for complex Tailwind class names
  - `{% nitro_bind %}` - Bind text using x-text for ternary operators and complex expressions
  - `{% nitro_if %}` / `{% end_nitro_if %}` - Server-side conditional blocks with Alpine reactivity
  - `{% nitro_for %}` / `{% end_nitro_for %}` - Server-side loops with Alpine x-for integration
  - `{% nitro_text %}` - Server-rendered text with live Alpine updates
  - `{% nitro_attr %}` - Dynamic attribute binding

- **Enhanced Form Components**:
  - `{% nitro_file %}` - File upload with preview, validation, and progress
  - `{% nitro_checkbox %}` - Styled checkbox with proper binding
  - `{% nitro_textarea %}` - Auto-expanding textarea support

- **Component Communication**:
  - `emit()` method for cross-component events
  - `refresh_component()` to refresh other components by name
  - Event handling with `@nitro-event` directives

- **Security Enhancements**:
  - Improved CSRF token handling
  - Better error messages without exposing internals

### Changed
- Improved `nitro_action` with `stop` and `prevent` modifiers
- Better error handling in component dispatch
- Cleaner Alpine.js integration with `x-cloak` support
- Optimized JavaScript bundle size

### Fixed
- Fixed template tag parsing for nested quotes
- Fixed state serialization for complex Pydantic models
- Fixed component registry thread safety

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
