# Changelog

All notable changes to Django Nitro.

## [0.8.0] - 2026-02-11

### 🚀 Complete Architecture Rewrite

v0.8.0 is a ground-up rewrite replacing the component-based architecture with standard Django views + HTMX.

### Added

**Views**
- `NitroView` - Base view with HTMX detection, toast helpers
- `NitroListView` - List with search, filter, sort, pagination
- `NitroModelView` - Single object detail
- `NitroFormView` - Form handling with HTMX support
- `NitroCreateView` - Create with auto company/user assignment
- `NitroUpdateView` - Edit existing
- `NitroDeleteView` - Delete with soft-delete support

**Forms & Wizards**
- `NitroModelForm` - Enhanced ModelForm with Tailwind styling
- `NitroForm` - Non-model forms
- `NitroWizard` - Multi-step form wizard
- `PhoneField`, `CurrencyField`, `CedulaField` - Custom form fields

**Tables & Filters**
- `NitroTable` - Declarative table definition
- `NitroFilterSet` - Faceted filter definitions
- `SearchFilter`, `SelectFilter`, `RangeFilter`, `DateRangeFilter`

**Mixins**
- `OrganizationMixin` - Multi-tenant scoping
- `OwnerRequiredMixin` - Object ownership check
- `StaffRequiredMixin` - Staff only access
- `PermissionRequiredMixin` - Permission checking

**Template Tags**
- HTMX actions: `nitro_search`, `nitro_filter`, `nitro_pagination`, `nitro_sort`, `nitro_delete`
- Forms: `nitro_field`, `nitro_select`, `nitro_form_footer`
- Components: `nitro_modal`, `nitro_slideover`, `nitro_tabs`, `nitro_empty_state`, `nitro_stats_card`, `nitro_avatar`, `nitro_file_upload`, `nitro_toast`
- Filters: `currency`, `status_badge`, `priority_badge`, `phone_format`, `relative_date`, `whatsapp_link`
- Helpers: `nitro_transition`, `nitro_key`, `nitro_scripts`

**HTML Components**
- `toast.html` - Toast notifications
- `modal.html` - Modal dialogs
- `slideover.html` - Slide-out panels
- `tabs.html` - Tab navigation
- `empty_state.html` - Empty state placeholder
- `stats_card.html` - Statistics cards
- `avatar.html` - User avatars
- `pagination.html` - Pagination controls
- `search_bar.html` - Search input
- `filter_select.html` - Filter dropdown
- `file_upload.html` - File upload zone
- `table.html` - Data table
- `form_field.html` - Form field wrapper
- `confirm.html` - Confirmation dialog
- And more...

**Alpine Components**
- `toastManager()` - Toast queue management
- `fileUpload()` - Drag-and-drop uploads
- `clipboard()` - Copy to clipboard
- `searchableSelect()` - Select with search
- `confirmAction()` - Confirmation modal
- `charCounter()` - Character counter
- `currencyInput()` - Currency formatting
- `phoneInput()` - Phone formatting
- `dirtyForm()` - Unsaved changes warning
- `infiniteScroll()` - Load more on scroll

**Utilities**
- `format_currency()`, `parse_currency()` - Currency handling
- `relative_date()`, `month_name()`, `is_overdue()`, `add_months()` - Date utilities
- `ExportMixin`, `export_csv()`, `export_excel()` - Data export

### Removed

- `NitroComponent` class
- `@register_component` decorator
- Pydantic state management
- Django Ninja JSON API
- `nitro-model` directive
- `nitro-action` directive
- Client-side state synchronization
- All v0.7 component classes

### Changed

- **No Pydantic** - Use Django ModelForms instead
- **No JSON APIs** - Server renders complete HTML
- **Alpine for UI only** - No data fetching, just local state
- **HTMX for everything** - Search, filter, pagination, forms

---

## [0.7.0] - 2025-12-15

### Added
- `BaseListComponent` with auto-inferred state class
- DX improvements for component development

### Changed
- Simplified component state inference

---

## [0.6.0] - 2025-11-01

### Added
- Initial component-based architecture
- Pydantic state management
- Django Ninja API integration
- Real-time state synchronization

---

## License

MIT License
