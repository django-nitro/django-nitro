# Changelog

All notable changes to Django Nitro will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.1] - 2026-01-04

### Fixed

#### Critical Bug Fixes
- **BaseListComponent now automatically applies security mixin filters** - `OwnershipMixin` and `TenantScopedMixin` now work without requiring manual override of `get_base_queryset()`. The component automatically detects and applies `filter_by_owner()` and `filter_by_tenant()` methods if present.
- **Fixed `{% nitro_for %}` Alpine.js initialization error** - Changed from `x-show="false"` to `style="display: none;"` to prevent "Cannot set properties of null (setting '_x_dataStack')" error during Alpine.js initialization.
- **Added custom JSON encoder for Django model fields** - Implemented `NitroJSONEncoder` to handle common Django field types (UUID, datetime, date, Decimal) that were causing serialization errors. No more manual type conversions needed.

#### Template & Context Improvements
- **State variables now unpacked to root template context** - Templates can now use `{{ items }}` instead of `{{ state.items }}`. Both syntaxes work for backward compatibility.

#### Testing & Dependencies
- **Fixed `test_sync_field_nonexistent_field_debug` test** - Added proper `override_settings(DEBUG=True)` decorator to ensure DEBUG mode validation works correctly.
- **Added `email-validator` dependency** - Required for Pydantic's `EmailStr` validation to work properly. Fixes import errors when using email fields in component state.
- **Fixed Pydantic v2 validation in `_sync_field()` method** - Updated to use `model_validate()` instead of `setattr()` to ensure proper validation of field values. This fixes validation errors not being caught when syncing fields with invalid values.

### Changed
- `BaseListComponent.get_base_queryset()` now includes auto-detection and application of security mixin filters
- Template rendering context now includes both unpacked state variables (root level) and nested `state` object for compatibility

### Documentation
- Updated `BaseListComponent` docstring to reflect automatic mixin filter application
- Added documentation for `NitroJSONEncoder` class

## [0.5.0] - 2025-12-29

### Added

#### Advanced Zero JavaScript Mode Template Tags
- **`{% nitro_attr %}`** - Dynamic attribute binding for any HTML attribute
  - Usage: `<img {% nitro_attr 'src' 'product.image_url' %}>`
  - Supports src, href, placeholder, and any custom attribute
- **`{% nitro_if %}`** - Conditional rendering wrapper (x-if equivalent)
  - Usage: `{% nitro_if 'user.is_authenticated' %} ... {% end_nitro_if %}`
  - Completely removes/adds DOM elements based on condition
- **`{% nitro_disabled %}`** - Dynamic disabled state binding
  - Usage: `<button {% nitro_disabled 'isProcessing || !isValid' %}>`
  - Supports complex boolean expressions
- **`{% nitro_file %}`** - File upload with progress tracking and validation
  - Usage: `<input type="file" {% nitro_file 'avatar' accept='image/*' preview=True %}>`
  - Features: file size validation, image preview, progress tracking
  - Client-side validation before upload
  - Custom events: `nitro:file-upload-start`, `nitro:file-upload-complete`, `nitro:file-error`, `nitro:file-preview`

#### Nested Field Support
- **Dot Notation in `nitro_model`** - Support for nested state fields
  - Usage: `<input {% nitro_model 'user.profile.email' %}>`
  - Works with deeply nested objects (3+ levels)
  - Automatic path validation in DEBUG mode
  - Server-side `_sync_field()` method handles nested updates

#### File Upload System
- **`_handle_file_upload()` Method** - Override to handle file uploads
  - Automatically called by `{% nitro_file %}` template tag
  - Receives field name and Django UploadedFile object
  - Default implementation provides helpful warnings
- **Client-side File Handling** in `nitro.js`:
  - `handleFileUpload()` function with validation and preview
  - File size validation with human-readable messages
  - Image preview generation for image files
  - Upload progress tracking with state updates
  - Automatic error handling and user feedback

### Enhanced

#### Template Tags System
- All Zero JS Mode tags now support more complex expressions
- Better error messages in DEBUG mode
- Consistent API across all template tags

#### JavaScript Client (`nitro.js`)
- File upload support with progress tracking
- File size parsing utilities (`_parseFileSize`, `_formatFileSize`)
- New DOM events for file operations
- Enhanced error handling for uploads

### Testing
- Added comprehensive test suite for v0.5.0 features
- Tests for all new template tags (`nitro_attr`, `nitro_if`, `nitro_disabled`, `nitro_file`)
- Tests for nested field support in `_sync_field()`
- Tests for file upload handler default implementation

### Debugging Tools
- **NITRO_DEBUG Mode** - HTML debug attributes on all template tags
  - Shows field names, parameters, and configuration
  - Enabled via `NITRO = {'DEBUG': True}` in settings
  - `data-nitro-debug` attributes visible in browser DevTools
- **Django Debug Toolbar Panel** - Server-side debugging
  - Shows all components rendered in a request
  - Tracks action calls with payloads
  - Monitors events emitted
  - Displays full component state
  - Installation: Add `nitro.debug_toolbar_panel.NitroDebugPanel` to `DEBUG_TOOLBAR_PANELS`
- **Client-Side Debug Logging** - Browser console debugging
  - Set `window.NITRO_DEBUG = true` for detailed logs
  - Logs component initialization, action calls, state updates
  - Event tracking in browser console

### Documentation
- Added examples for all new template tags
- Documented nested field syntax and limitations
- File upload guide with examples
- Complete debugging guide (debugging.md)
- Updated API reference with new methods

## [0.4.0] - 2025-12-29

### Added

#### Configuration System
- **Global Configuration** via Django settings (`NITRO` dict)
- `get_setting()` and `get_all_settings()` functions for centralized config
- Configurable toast notifications (enabled, position, duration, style)
- Component-level configuration overrides

#### Toast Notifications
- **Native Toast System** without external dependencies
- Professional toast styles with `nitro.css` (6 positions, 3 styles, animations)
- **Custom Toast Adapter** support via `window.NitroToastAdapter`
- Automatic toast display for `success()` and `error()` messages
- Component-level toast configuration (position, duration, style)

#### Event System
- **Inter-component Communication** via DOM events
- `emit(event_name, data)` method for custom events
- `refresh_component(component_id)` helper for triggering refreshes
- Built-in events: `nitro:message`, `nitro:action-complete`, `nitro:error`
- Custom events dispatched from server with full data payloads

#### Smart State Updates (Opt-in)
- **State Diffing** for efficient updates with `smart_updates = True`
- Intelligent list operations (added/removed/updated) for items with `id` field
- Client-side diff application reduces payload size
- Optimized for components with large lists (500+ items)

#### CLI Scaffolding
- **`startnitro` Management Command** for rapid component generation
- `python manage.py startnitro ComponentName --app myapp`
- Support for simple, list, and CRUD components with `--list` and `--crud` flags
- Auto-generates component files, templates, and state schemas
- Follows project conventions and best practices

#### SEO-Friendly Template Tags
- **`{% nitro_scripts %}`** tag for including CSS and JS
- **`{% nitro_for %}`** for SEO-optimized loops with Alpine.js hydration
- **`{% nitro_text %}`** for static content with reactive bindings
- Hybrid rendering: static HTML (SEO) + Alpine.js (reactivity)
- Fully optional - traditional `x-for` and `x-text` still work

### Changed
- `render()` now includes `toast_config` in initial payload
- `process_action()` now returns `events`, `toast_config`, and optional `partial` flag
- `nitro.js` completely rewritten with toast system, event dispatching, and diff application
- Enhanced debug mode with detailed console logging for events and state changes

### Fixed
- Created missing `nitro/templatetags/__init__.py` for proper Django template tag recognition
- Added documentation about `from_attributes=True` requirement in model schemas

### Documentation
- New `TOAST_ADAPTERS.md` with integration examples (SweetAlert2, Toastify, Notyf)
- Updated API reference with new methods and configuration options
- Added examples for event system and smart updates
- CLI command usage documentation

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





