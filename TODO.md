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

## 🎨 v0.6.0 - Developer Experience (Next Release)

**Target:** 1-2 months after v0.5.0

### IDE Support
- [ ] VSCode snippets for template tags
  - `nitro-model` → `{% nitro_model 'field' %}`
  - `nitro-action` → `{% nitro_action 'method' %}`
  - `nitro-attr` → `{% nitro_attr 'attribute' 'value' %}`
  - `nitro-if` → `{% nitro_if 'condition' %} ... {% end_nitro_if %}`

- [ ] PyCharm live templates
- [ ] Syntax highlighting for {% nitro_* %} tags

### Advanced Debugging (Future)
- [ ] Browser DevTools extension for Nitro
  - Inspect component tree
  - Live state editing
  - Time-travel debugging

### Developer Tools
- [ ] manage.py command: `inspectcomponent ComponentName`
  - Show state schema
  - List all actions
  - Show template location

- [ ] manage.py command: `validatecomponents`
  - Check all registered components
  - Validate state schemas
  - Check template existence

### Error Messages
- [ ] Better error messages for common mistakes
  ```python
  # Before
  AttributeError: 'CounterState' object has no attribute 'cnt'

  # After
  NitroError: Field 'cnt' does not exist in CounterState.
  Did you mean 'count'? Available fields: count, step
  ```

- [ ] Validation error display in templates
  ```html
  <input {% nitro_model 'email' %}>
  <!-- Auto-generated error display -->
  <span class="nitro-error" x-show="errors.email" x-text="errors.email"></span>
  ```

---

## 🔮 v0.7.0 - Advanced Features

**Target:** 3-4 months after v0.6.0

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
- [ ] Upload progress tracking
  ```html
  <input {% nitro_file 'avatar' %}>
  <div x-show="uploadProgress > 0">
      Uploading: <span x-text="uploadProgress"></span>%
  </div>
  ```

- [ ] Multiple file uploads
- [ ] Drag & drop support
- [ ] Image preview before upload

### Advanced State Management
- [ ] Offline state support (localStorage persistence)
  ```python
  class FormState(BaseModel):
      persist_offline = True  # Auto-save to localStorage
  ```

- [ ] Undo/Redo support
  ```python
  self.state.history_enabled = True
  self.undo()
  self.redo()
  ```

- [ ] Optimistic updates (update UI before server confirms)

### Security Enhancements
- [ ] Rate limiting per component/action
  ```python
  @rate_limit(max_calls=10, window=60)  # 10 calls per minute
  def send_email(self):
      pass
  ```

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

**Last Updated:** 2025-12-29
**Current Version:** v0.5.0
**Next Release:** v0.6.0 (Developer Experience)
