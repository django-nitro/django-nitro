# Django Nitro - Context & Architecture

## 📋 Project Overview

**Django Nitro** is a modern reactive component framework for Django, combining the best of Alpine.js and Python for building interactive UIs without writing JavaScript.

**Philosophy:** "Write Python, not JavaScript" - Business logic in Python, reactivity handled automatically.

**Version:** 0.5.0
**Status:** Beta (approaching v1.0)
**License:** MIT

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Client)                     │
├─────────────────────────────────────────────────────────┤
│  Alpine.js (15KB)                                        │
│  - Reactive DOM updates                                 │
│  - Event handling                                        │
│  - State management (client-side)                       │
├─────────────────────────────────────────────────────────┤
│  nitro.js                                               │
│  - Component initialization                             │
│  - API communication                                     │
│  - State diffing (client-side)                          │
│  - Toast notifications                                   │
│  - Event dispatching                                     │
└─────────────────────────────────────────────────────────┘
                            ▲
                            │ HTTP POST /api/nitro/dispatch
                            │ { component_name, action, state, payload }
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Django (Server)                       │
├─────────────────────────────────────────────────────────┤
│  Django Ninja API (/api/nitro/)                         │
│  - Action dispatching                                    │
│  - CSRF validation                                       │
│  - JSON serialization                                    │
├─────────────────────────────────────────────────────────┤
│  NitroComponent (Python)                                │
│  - Pydantic state validation                            │
│  - Business logic                                        │
│  - HMAC integrity verification                          │
│  - State diffing (server-side)                          │
│  - Event emission                                        │
├─────────────────────────────────────────────────────────┤
│  Django ORM                                             │
│  - Database operations                                   │
│  - Model integration                                     │
└─────────────────────────────────────────────────────────┘
```

### Component Lifecycle

```
1. Initial Render (Server-Side)
   ┌──────────────────────────────────────┐
   │ View calls component.render()        │
   │   ↓                                  │
   │ get_initial_state(**kwargs)          │
   │   ↓                                  │
   │ State serialized to JSON             │
   │   ↓                                  │
   │ Template rendered with state         │
   │   ↓                                  │
   │ HTML + <script> with state sent      │
   └──────────────────────────────────────┘

2. Client-Side Hydration
   ┌──────────────────────────────────────┐
   │ Alpine.js initializes                │
   │   ↓                                  │
   │ nitro.js parses data-nitro-state     │
   │   ↓                                  │
   │ Alpine.data('nitro') created         │
   │   ↓                                  │
   │ State becomes reactive               │
   └──────────────────────────────────────┘

3. User Interaction
   ┌──────────────────────────────────────┐
   │ User clicks button                   │
   │   ↓                                  │
   │ @click="call('action')" triggered    │
   │   ↓                                  │
   │ POST /api/nitro/dispatch             │
   │   ↓                                  │
   │ NitroComponent.process_action()      │
   │   ↓                                  │
   │ Action method executed               │
   │   ↓                                  │
   │ State updated                        │
   │   ↓                                  │
   │ Response: { state, messages, ... }   │
   │   ↓                                  │
   │ Client updates Alpine state          │
   │   ↓                                  │
   │ DOM updates reactively               │
   └──────────────────────────────────────┘
```

---

## 🔑 Key Design Decisions

### 1. **Alpine.js over Morphdom**

**Decision:** Use Alpine.js for client-side reactivity.

**Why:**
- **Lighter:** 15KB vs 50KB (Morphdom)
- **Declarative:** Easier to understand
- **Popular:** Large community, good docs
- **Flexible:** Can be used beyond Nitro

**Trade-off:** Requires learning Alpine syntax (we mitigate with template tags in v0.4.0).

### 2. **Pydantic for State Management**

**Decision:** Use Pydantic BaseModel for state schemas.

**Why:**
- **Type Safety:** Runtime validation
- **IDE Support:** Autocomplete, type checking
- **Serialization:** Easy JSON conversion
- **Validation:** Built-in validators

**Example:**
```python
class UserState(BaseModel):
    email: EmailStr  # Auto-validates email format
    age: int = Field(ge=0, le=120)  # Range validation
```

**Trade-off:** Slightly more boilerplate than plain classes.

### 3. **Django Ninja for API Layer**

**Decision:** Use Django Ninja instead of custom views.

**Why:**
- **Modern:** Fast, async-capable
- **OpenAPI:** Auto-generated docs
- **Type Hints:** Pydantic integration
- **Performance:** FastAPI-like speed

**Trade-off:** Additional dependency.

### 4. **HMAC Integrity Verification**

**Decision:** Sign sensitive fields to prevent client tampering.

**Why:**
- **Security:** Client can't modify IDs, foreign keys
- **Automatic:** ModelNitroComponent auto-secures id fields
- **Transparent:** Developers don't think about it

**How it works:**
```python
# Server generates signature
integrity = hmac.new(SECRET_KEY, state_json, sha256).hexdigest()

# Client sends back: { state, integrity }

# Server validates
if not hmac.compare_digest(expected, received):
    raise SecurityError("Tampering detected")
```

### 5. **State Diffing (v0.4.0)**

**Decision:** Opt-in state diffing for large lists.

**Why:**
- **Performance:** 98% reduction in response size for 500-item lists
- **Opt-in:** No overhead for small lists
- **Smart:** Only diffs lists with `id` field

**When enabled:**
```python
class TaskList(BaseListComponent):
    smart_updates = True  # ← Enable diffing
```

**Response:**
```json
{
    "partial": true,
    "state": {
        "items": {
            "diff": {
                "added": [{"id": 101, ...}],
                "removed": [99],
                "updated": [{"id": 42, ...}]
            }
        }
    }
}
```

### 6. **Template Tags for "Zero JavaScript" (v0.4.0)**

**Decision:** Provide template tags that hide Alpine syntax.

**Why:**
- **Marketing:** "Zero JavaScript" promise
- **DX:** Django developers don't need to learn Alpine
- **Hybrid:** Can still use Alpine for advanced cases

**Example:**
```html
<!-- Zero JS Mode -->
<input {% nitro_model 'email' debounce='300ms' %}>
<button {% nitro_action 'submit' %}>Send</button>

<!-- Alpine Mode (advanced) -->
<input x-model="email" @input.debounce.300ms="call('sync_field', ...)">
```

---

## 📁 Project Structure

```
nitro/
├── __init__.py              # Package exports, version
├── api.py                   # Django Ninja API endpoints
├── base.py                  # Core: NitroComponent, ModelNitroComponent, CrudNitroComponent
├── list.py                  # BaseListComponent with pagination/search
├── security.py              # Security mixins (Ownership, Tenant, Permission)
├── registry.py              # Component registration
├── conf.py                  # Configuration system (NITRO settings)
├── tests.py                 # Unit tests
├── management/
│   └── commands/
│       └── startnitro.py    # CLI scaffolding command
├── templatetags/
│   ├── __init__.py
│   └── nitro_tags.py        # Template tags (nitro_model, nitro_action, etc.)
└── static/nitro/
    ├── nitro.css            # Toast styles
    └── nitro.js             # Alpine integration, client logic

docs/
├── index.md                 # Homepage
├── api-reference.md         # Complete API docs
├── getting-started/
│   ├── installation.md
│   └── quick-start.md
├── core-concepts/
│   ├── events.md            # Event system guide
│   ├── cli-tools.md         # CLI scaffolding guide
│   ├── template-tags.md     # SEO & Zero JS tags
│   ├── smart-updates.md     # State diffing guide
│   ├── TOAST_ADAPTERS.md    # Toast customization
│   └── zero-javascript-mode.md  # Zero JS complete guide
└── security/
    ├── overview.md
    ├── ownership-mixin.md
    ├── tenant-scoped-mixin.md
    └── permission-mixin.md

examples/
├── counter/                 # Simple counter (Zero JS Mode)
│   ├── counter_project/
│   ├── dashboard/
│   │   └── components/
│   │       └── counter.py
│   └── templates/
└── property-manager/        # Real-world CRUD example
    └── ...
```

---

## 🔐 Security Model

### Layers of Security

1. **CSRF Protection** (Django built-in)
   - All POST requests include CSRF token
   - Validated by Django middleware

2. **HMAC Integrity Verification** (Nitro)
   - Sensitive fields signed with SECRET_KEY
   - Prevents client-side tampering
   - Auto-enabled for id fields

3. **Pydantic Validation** (Runtime)
   - All state changes validated
   - Type checking, constraints
   - Prevents invalid data

4. **Developer Responsibilities**
   - Authentication checks (`self.require_auth()`)
   - Authorization checks (PermissionMixin)
   - Input sanitization
   - Rate limiting

### Example: Secure Component

```python
from nitro.security import OwnershipMixin, PermissionMixin

@register_component
class DocumentManager(
    OwnershipMixin,      # Only current user's docs
    PermissionMixin,     # Custom permission logic
    CrudNitroComponent
):
    model = Document
    owner_field = 'user'
    secure_fields = ['id', 'user_id', 'price']  # Can't be modified

    def check_permission(self, action: str) -> bool:
        if action == 'delete':
            return self.current_user.is_staff
        return True

    def delete_item(self, id: int):
        if not self.enforce_permission('delete', "Only staff can delete"):
            return

        super().delete_item(id)
```

---

## 🎯 Design Patterns

### 1. Component Hierarchy

```
NitroComponent (Base)
    ├── State validation
    ├── Action dispatching
    ├── Message system
    └── Event system

ModelNitroComponent (ORM Integration)
    ├── Inherits: NitroComponent
    ├── Model loading (pk/id)
    ├── Auto-secure fields
    └── refresh() from DB

CrudNitroComponent (CRUD Operations)
    ├── Inherits: ModelNitroComponent
    ├── create_item()
    ├── delete_item()
    ├── start_edit(), save_edit()
    └── Buffers (create_buffer, edit_buffer)

BaseListComponent (Pagination + CRUD)
    ├── Inherits: CrudNitroComponent
    ├── Pagination
    ├── Search
    ├── Filters
    └── Smart updates (diffing)
```

### 2. Mixins Pattern

```python
# Security mixins can be combined
@register_component
class MyComponent(
    OwnershipMixin,      # Filter by owner
    TenantScopedMixin,   # Filter by tenant
    PermissionMixin,     # Custom permissions
    BaseListComponent    # Base functionality
):
    pass
```

**MRO (Method Resolution Order):**
Mixins are applied **left to right**, both filters combine with AND logic.

### 3. Generic Types

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class NitroComponent(Generic[T]):
    state_class: Type[T]
    state: T  # ← IDE knows the exact type
```

**Benefits:**
- IDE autocomplete
- Type checking
- Self-documenting code

---

## 🚀 Performance Optimizations

### 1. State Diffing (v0.4.0)

**When:** Lists with 100+ items
**Savings:** 90-98% reduction in response size
**How:** Server calculates added/removed/updated items

### 2. Lazy Loading

**When:** Large querysets
**How:** Use `.only()`, `.defer()`, `select_related()`, `prefetch_related()`

```python
def get_base_queryset(self):
    return Product.objects.select_related('category').only(
        'id', 'name', 'price', 'category__name'
    )
```

### 3. Pagination

**Default:** 20 items per page
**Configurable:** `per_page = 50`

### 4. Debouncing

**Template tags support:**
```html
<input {% nitro_model 'search' debounce='300ms' %}>
```

Reduces API calls from 10/second to 1/300ms.

---

## 🐛 Common Pitfalls

### 1. Forgetting `from_attributes=True`

```python
# ❌ Wrong
class ProductSchema(BaseModel):
    id: int
    name: str

# ✅ Correct
class ProductSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
```

### 2. Not Specifying Buffer Types

```python
# ❌ Wrong (type inference fails)
class MyListState(BaseListState):
    items: list[ItemSchema] = []

# ✅ Correct
class MyListState(BaseListState):
    items: list[ItemSchema] = []
    create_buffer: ItemFormSchema = Field(default_factory=ItemFormSchema)
    edit_buffer: ItemFormSchema | None = None
```

### 3. Mixing Alpine and Template Tags

```html
<!-- ❌ Wrong - duplicate bindings -->
<input
    {% nitro_model 'email' %}
    x-model="email"
>

<!-- ✅ Correct - use one or the other -->
<input {% nitro_model 'email' %}>
```

### 4. Not Validating Permissions

```python
# ❌ Wrong - no permission check
def delete_item(self, id: int):
    obj = self.model.objects.get(id=id)
    obj.delete()

# ✅ Correct
def delete_item(self, id: int):
    if not self.require_auth("Login required"):
        return

    obj = self.model.objects.get(id=id)

    if obj.owner != self.current_user:
        self.error("Permission denied")
        return

    obj.delete()
```

---

## 📊 Comparison to Alternatives

| Feature | Nitro | Unicorn | Livewire | HTMX |
|---------|-------|---------|----------|------|
| **Language** | Python | Python | PHP | Any |
| **Frontend** | Alpine.js | Morphdom | Alpine.js | Vanilla JS |
| **Bundle Size** | 15KB | 50KB | 15KB | 14KB |
| **Type Safety** | ★★★★★ | ★★☆☆☆ | ★★★☆☆ | ★☆☆☆☆ |
| **Auto-sync** | ✅ (v0.4.0) | ❌ | ✅ | ❌ |
| **State Diffing** | ✅ | ❌ | ❌ | ❌ |
| **SEO Tags** | ✅ | ❌ | ❌ | ✅ |
| **Events** | ✅ | ❌ | ✅ | ✅ |
| **Zero JS** | ✅ (v0.4.0) | ✅ | ✅ | ✅ |

**Nitro's Unique Selling Points:**
1. Type safety with Pydantic
2. State diffing for performance
3. Hybrid mode (Zero JS + Alpine)
4. SEO-friendly template tags
5. Modern async-ready API

---

## 🎓 Learning Path

### Beginner (Day 1)
1. Read: Getting Started guide
2. Try: Counter example
3. Understand: State, Actions, Templates

### Intermediate (Week 1)
1. Build: Simple CRUD component
2. Learn: Pagination, Search, Filters
3. Use: BaseListComponent

### Advanced (Month 1)
1. Master: Security mixins
2. Optimize: State diffing
3. Customize: Toast adapters
4. Integrate: Events system

### Expert (Month 3)
1. Contribute: Open source PRs
2. Build: Complex multi-component apps
3. Teach: Write tutorials
4. Extend: Custom mixins

---

## 🔮 Vision & Roadmap

### Short-term (3 months)
- v0.5.0: Advanced template tags
- v0.6.0: Developer experience improvements
- Community building

### Mid-term (6 months)
- v0.7.0: Real-time features (polling, WebSockets)
- v0.8.0: File upload improvements
- v0.9.0: Beta testing, bug fixes

### Long-term (12 months)
- v1.0.0: Production-ready release
- Ecosystem: UI component library
- Enterprise: Paid support/consulting

### Dream Features
- Visual component builder
- AI-powered component generation
- Mobile/desktop app support
- Edge computing deployment

---

## 📞 Contact & Contributing

**GitHub:** https://github.com/django-nitro/django-nitro
**Issues:** https://github.com/django-nitro/django-nitro/issues
**Discussions:** https://github.com/django-nitro/django-nitro/discussions

**Core Maintainer:** Jearel (jeasoft)
**Philosophy:** "Write Python, not JavaScript"
**Status:** Active development, approaching v1.0

---

**Last Updated:** 2025-12-29
**Version:** v0.5.0
**Next Release:** v0.6.0 (Developer Experience)
