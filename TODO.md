# Django Nitro - TODO List

## ✅ v0.4.0 - COMPLETED (Current Release)

### Core Features
- [x] Toast notification system (native + custom adapters)
- [x] Configuration system (nitro/conf.py)
- [x] Event system (emit, refresh_component)
- [x] DOM events (nitro:message, nitro:action-complete, nitro:error)
- [x] State diffing (smart_updates for large lists)
- [x] CLI scaffolding (python manage.py startnitro)
- [x] SEO template tags (nitro_for, nitro_text, nitro_scripts)
- [x] warning() and info() methods
- [x] Documentation complete

### Zero JavaScript Mode (MVP)
- [x] Template tag: nitro_model (wire:model equivalent)
- [x] Template tag: nitro_action (wire:click equivalent)
- [x] Template tag: nitro_show (x-show wrapper)
- [x] Template tag: nitro_class (conditional CSS)
- [x] Backend: _sync_field() method for auto-sync
- [x] Tests for new template tags
- [x] Example: Counter migrated to Zero JS Mode
- [x] Docs: Zero JavaScript Mode guide

---

## ✅ v0.5.0 - Zero JS Advanced - COMPLETED

**Released:** 2025-12-29

### Advanced Template Tags
- [x] nitro_attr - Dynamic attributes
  ```html
  <img {% nitro_attr 'src' 'product.image_url' %}>
  <a {% nitro_attr 'href' 'item.link' %}>
  ```

- [x] nitro_if - Conditional rendering wrapper
  ```html
  {% nitro_if 'user.is_authenticated' %}
      <div>Welcome back!</div>
  {% end_nitro_if %}
  ```

- [x] nitro_disabled - Dynamic disabled state
  ```html
  <button {% nitro_disabled 'isProcessing or !isValid' %}>
  ```

- [x] nitro_file - File upload with progress
  ```html
  <input type="file" {% nitro_file 'document' accept='.pdf,.docx' %}>
  ```

### Nested Field Support
- [x] Support dot notation in nitro_model
  ```html
  <input {% nitro_model 'user.profile.email' %}>
  <input {% nitro_model 'settings.theme' %}>
  ```
- [x] Nested field validation and error handling
- [x] Tests for nested field support

### File Upload System
- [x] Client-side file upload handler with progress tracking
- [x] File size validation (maxSize parameter)
- [x] Image preview support (preview parameter)
- [x] Server-side _handle_file_upload() method
- [x] Custom file upload events

### Debugging Tools
- [x] NITRO_DEBUG mode with HTML debug attributes
- [x] Django Debug Toolbar panel
- [x] Component state tracking
- [x] Action call tracking
- [x] Event emission tracking
- [x] Complete debugging documentation

### Testing & Documentation
- [x] Tests for all new template tags
- [x] Tests for nested field support
- [x] Tests for file upload handler
- [x] Updated CHANGELOG.md with v0.5.0 features
- [x] Version bump to 0.5.0
- [x] Debugging guide documentation

### Deferred to Future Versions
- [ ] Array indexing support (e.g., `items.0.name`)
- [ ] Lazy loading for nitro_model (only sync on blur by default)
- [ ] Batch sync multiple fields in one request
- [ ] Migrate Property Manager example to Zero JS Mode
- [ ] Create new example: Contact Form (Zero JS)
- [ ] Create new example: Todo List (Zero JS)
- [ ] Complete Zero JavaScript Mode guide
- [ ] Add "Mode Comparison" page (Zero JS vs Alpine)
- [ ] Add "When to Use Alpine" guide
- [ ] Video tutorial for Zero JS Mode

---

## ✅ v0.6.0 - Developer Experience - COMPLETED

**Released:** 2026-01-13

### Form Field Template Tags
- [x] `{% nitro_input %}` - Text, email, number, date, tel inputs
- [x] `{% nitro_select %}` - Dropdown with choices support
- [x] `{% nitro_checkbox %}` - Checkbox with label
- [x] `{% nitro_textarea %}` - Multi-line text input
- [x] Automatic error display and Bootstrap styling
- [x] Edit buffer support for CRUD operations

### Performance Improvements
- [x] Default 200ms debounce on `nitro_model`
- [x] TypeAdapter caching in BaseListComponent
- [x] Code deduplication in nitro/utils.py

### Django 5.2 Compatibility
- [x] Added `django-template-partials` support
- [x] Optional dependency: `pip install django-nitro[django52]`

### Testing & Quality
- [x] 24 new tests (46% → 59% coverage)
- [x] CI/CD pipeline fixes
- [x] Ruff linting compliance

---

## ✅ v0.7.0 - True Zero-JS & DX - COMPLETED

**Released:** 2026-01-19

### DX Improvements
- [x] **Auto-infer `state_class`** from Generic type parameter
  ```python
  # No more redundant state_class = MyState
  class Counter(NitroComponent[CounterState]):
      pass  # state_class auto-inferred!
  ```

- [x] **CacheMixin** - Component state and HTML caching
  ```python
  class MyComponent(CacheMixin, NitroComponent[MyState]):
      cache_enabled = True
      cache_ttl = 300
      cache_html = True
  ```

- [x] **@cache_action decorator** - Cache expensive action results
- [x] **nitro_phone / n_phone** - Phone input with XXX-XXX-XXXX mask
- [x] **Unaccent search** - Accent-insensitive search (PostgreSQL)
- [x] **nitro_text as attribute** - Works with other HTML attributes

### True Zero-JS Template Tags
- [x] `{% nitro_switch %}` - Conditional text (no JS ternaries!)
- [x] `{% nitro_css %}` - Conditional CSS classes
- [x] `{% nitro_badge %}` - Combined text + styling
- [x] `{% nitro_visible %}` / `{% nitro_hidden %}` - Boolean visibility
- [x] `{% nitro_plural %}` / `{% nitro_count %}` - Pluralization
- [x] `{% nitro_format %}` / `{% nitro_date %}` - Value formatting
- [x] `{% nitro_each %}` - Zero-JS iteration

### Bug Fixes
- [x] Fixed `_get_state_class()` for BaseListComponent Generic inference
- [x] Fixed loading indicator flash during field sync (silent mode)
- [x] Fixed x-model binding in form field templates
- [x] Fixed state flicker on field sync

---

## 🔮 v0.8.0 - Real-Time & Advanced Features

**Target:** Q2 2026

### Real-Time Features
- [ ] Polling support (wire:poll equivalent)
  ```python
  @register_component
  class LiveDashboard(NitroComponent[DashboardState]):
      polling_interval = 5000  # 5 seconds
  ```

- [ ] WebSocket support for live updates
- [ ] Server-sent events (SSE) for notifications

### File Upload Improvements
- [ ] Multiple file uploads
- [ ] Drag & drop support
- [ ] Chunked uploads for large files

### Advanced State Management
- [ ] Offline state support (localStorage persistence)
- [ ] Undo/Redo support
- [ ] Optimistic updates

### Security Enhancements
- [ ] Rate limiting per component/action
- [ ] CAPTCHA integration for sensitive actions
- [ ] IP-based throttling

---

## 🌟 v1.0.0 - Production Ready

**Target:** 6-12 months

### Stability
- [ ] 100% test coverage
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Load testing (1000+ concurrent users)

### Documentation
- [ ] Complete API documentation
- [ ] Video tutorials
- [ ] Case studies from real projects
- [ ] Best practices guide
- [ ] Performance optimization guide

### Ecosystem
- [ ] Integration with popular Django packages:
  - django-allauth
  - django-crispy-forms
  - django-tables2
  - django-filter

- [ ] Official UI component library
  - Button, Input, Select components
  - Modal, Dropdown, Toast components
  - Form validation components

- [ ] Tailwind CSS plugin for Nitro

### Enterprise Features
- [ ] Server-side rendering (SSR) for better SEO
- [ ] Multi-language support (i18n)
- [ ] Accessibility (WCAG 2.1 AA compliance)
- [ ] Analytics integration

---

## 🐛 Known Issues / Technical Debt

### High Priority
- [ ] Fix: Static files location in deployment (already fixed in v0.4.0)
- [ ] Fix: XSS vulnerabilities in toasts (already fixed in v0.4.0)
- [ ] Improve: Error handling in API layer

### Medium Priority
- [ ] Refactor: Consolidate message types (success, error, warning, info)
- [ ] Optimize: Reduce JavaScript bundle size
- [ ] Improve: Type hints in base.py (more specific generics)

### Low Priority
- [ ] Refactor: Template tag tests (more edge cases)
- [ ] Docs: More examples in API reference
- [ ] CI/CD: Add automated testing

---

## 📝 Documentation Needed

### Guides
- [ ] Migration guide from Django Unicorn
- [ ] Migration guide from Livewire
- [ ] Deployment guide (production checklist)
- [ ] Scaling guide (performance optimization)
- [ ] Testing guide (how to test Nitro components)

### Tutorials
- [ ] Build a blog with Nitro
- [ ] Build a todo app with Nitro
- [ ] Build a chat app with Nitro
- [ ] Build an e-commerce product catalog

### Recipes
- [ ] Infinite scroll
- [ ] Auto-save drafts
- [ ] Multi-step forms
- [ ] Bulk operations
- [ ] CSV import/export
- [ ] PDF generation

---

## 🎯 Community / Marketing

### Pre-launch (Before v1.0)
- [ ] Create Twitter/X account
- [ ] Create Discord server
- [ ] Write blog posts about architecture
- [ ] Submit to Django Packages
- [ ] Submit to Awesome Django

### Post-launch (After v1.0)
- [ ] Conference talks (DjangoCon, PyCon)
- [ ] YouTube channel with tutorials
- [ ] Weekly blog posts
- [ ] Case studies from users
- [ ] Comparison articles (vs Unicorn, vs HTMX)

### Growth
- [ ] Sponsor Django events
- [ ] Create starter templates
- [ ] SaaS boilerplate with Nitro
- [ ] Paid support/consulting
- [ ] Enterprise license (optional)

---

## 💭 Ideas / Future Exploration

- [ ] Mobile app support (React Native bridge?)
- [ ] Desktop app support (Electron/Tauri?)
- [ ] Visual component builder (drag & drop?)
- [ ] AI-powered component generation
- [ ] GraphQL integration
- [ ] Serverless deployment support
- [ ] Edge computing support (Cloudflare Workers?)

---

## 📊 Metrics to Track

- [ ] GitHub stars
- [ ] PyPI downloads
- [ ] Documentation page views
- [ ] Discord/community members
- [ ] Number of production deployments
- [ ] Performance benchmarks over time
- [ ] Bug report resolution time

---

**Last Updated:** 2026-01-19
**Current Version:** v0.7.0
**Next Release:** v0.8.0 (Real-Time & Advanced Features)
