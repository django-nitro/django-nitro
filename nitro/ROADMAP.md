# Django Nitro - Roadmap Actualizado

**Última actualización:** 2026-01-18
**Versión actual:** v0.6.1

---

## Estado Actual - Lo que YA existe

### v0.4.0 - Core (Completado)
- [x] Toast notifications (nativo + custom adapters)
- [x] Sistema de configuración (nitro/conf.py)
- [x] Sistema de eventos (emit, refresh_component)
- [x] DOM events (nitro:message, nitro:action-complete, nitro:error)
- [x] State diffing (smart_updates para listas grandes)
- [x] CLI scaffolding (python manage.py startnitro)
- [x] SEO template tags (nitro_for, nitro_text)
- [x] Zero JS Mode básico (nitro_model, nitro_action, nitro_show, nitro_class)

### v0.5.0 - Zero JS Avanzado (Completado)
- [x] nitro_attr - Atributos dinámicos
- [x] nitro_if - Renderizado condicional
- [x] nitro_disabled - Estado disabled
- [x] nitro_file - Upload con progreso
- [x] Soporte campos anidados (user.profile.email)
- [x] Debug Toolbar panel
- [x] NITRO_DEBUG mode

### v0.6.0 - Form Fields (Completado)
- [x] nitro_input - Campo input completo
- [x] nitro_select - Campo select estático
- [x] nitro_dynamic_select - Select con opciones de Alpine state
- [x] nitro_checkbox - Campo checkbox
- [x] nitro_textarea - Campo textarea
- [x] Manejo automático de edit_buffer vs create_buffer

### v0.6.1 - ZeroJS Completo (Actual)
- [x] refresh() method en NitroComponent base
- [x] Dirty state auto-tracking (isDirty, trackChange, beforeunload)
- [x] nitro_key - Eventos de teclado (enter, escape, ctrl+s, etc.)
- [x] nitro_toggle - Toggle client-side sin round-trip
- [x] nitro_set - Set valor client-side sin round-trip

---

## Tags Nitro Disponibles (ZeroJS Completo)

| Tag | Propósito | Server? |
|-----|-----------|---------|
| `{% nitro_component %}` | Renderizar componente | ✅ |
| `{% nitro_model %}` | Two-way binding | ✅ |
| `{% nitro_action %}` | Ejecutar método servidor | ✅ |
| `{% nitro_key %}` | Evento teclado → acción | ✅ |
| `{% nitro_toggle %}` | Toggle boolean | ❌ |
| `{% nitro_set %}` | Set valor | ❌ |
| `{% nitro_show %}` | Visibilidad condicional | ❌ |
| `{% nitro_if %}` | Render condicional (DOM) | ❌ |
| `{% nitro_for %}` | Loop reactivo + SEO | ❌ |
| `{% nitro_text %}` | Texto dinámico | ❌ |
| `{% nitro_class %}` | Clases condicionales | ❌ |
| `{% nitro_attr %}` | Atributos dinámicos | ❌ |
| `{% nitro_disabled %}` | Estado disabled | ❌ |
| `{% nitro_input %}` | Campo input completo | ✅ |
| `{% nitro_select %}` | Campo select estático | ✅ |
| `{% nitro_dynamic_select %}` | Select dinámico | ✅ |
| `{% nitro_checkbox %}` | Campo checkbox | ✅ |
| `{% nitro_textarea %}` | Campo textarea | ✅ |
| `{% nitro_file %}` | Upload de archivos | ✅ |

---

## Roadmap Futuro

### v0.7.0 - Testing & DX (Próximo)

**Testing Helpers** - El único gap real pendiente
```python
from nitro.testing import NitroTestCase

class PropertyListTests(NitroTestCase):
    def test_create_property(self):
        component = self.mount('PropertyList')

        # Assert initial state
        component.assertState('items', [])
        component.assertState('showCreate', False)

        # Call action
        component.call('create_item', name='Test Property')

        # Assert results
        component.assertState('items', has_length(1))
        component.assertHasMessage('success', 'Property created')
        component.assertEmitted('property-created')
```

**Mejor manejo de errores**
```python
# Antes
AttributeError: 'CounterState' object has no attribute 'cnt'

# Después
NitroError: Field 'cnt' does not exist in CounterState.
Did you mean 'count'? Available fields: count, step
```

**nitro_error tag** - Mostrar errores de campo
```html
{% nitro_input field='email' %}
{% nitro_error 'email' %}  <!-- Auto-muestra error si existe -->
```

### v0.8.0 - Performance (Futuro)

**Lazy Loading de componentes**
```html
{% nitro_component 'HeavyChart' lazy=True placeholder='loading.html' %}
```

**Batch sync** - Sincronizar múltiples campos en una request
```python
# Actualmente: 1 request por campo
# Con batch: 1 request para N campos modificados
```

**Throttle para nitro_model**
```html
{% nitro_model 'search' throttle='500ms' %}
```

### v0.9.0 - Ecosystem (Futuro)

**Integraciones**
- [ ] django-allauth (auth flows)
- [ ] django-filter (filtros avanzados)
- [ ] django-tables2 (tablas reactivas)

**UI Component Library** (opcional)
- [ ] Componentes pre-construidos (Modal, Dropdown, Tabs)
- [ ] Tailwind CSS plugin

### v1.0.0 - Production Ready

**Estabilidad**
- [ ] 100% test coverage
- [ ] Performance benchmarks
- [ ] Security audit
- [ ] Load testing (1000+ concurrent)

**Documentación**
- [ ] API documentation completa
- [ ] Video tutorials
- [ ] Migration guides (desde Unicorn, HTMX)
- [ ] Best practices guide

---

## Lo que NO vamos a implementar

Después de analizar Livewire, Unicorn, y otros frameworks, decidimos que estos features son **redundantes** porque Nitro ya tiene Alpine.js:

| Feature | Por qué NO |
|---------|------------|
| `$set` server-side | `{% nitro_set %}` es client-side (más rápido) |
| `$toggle` server-side | `{% nitro_toggle %}` es client-side (más rápido) |
| Loading targets | `{% nitro_show 'isLoading' %}` + variables locales suficiente |
| Form class Django | Pydantic `state_class` ya hace validación tipada |
| Computed properties | Python `@property` y `@cached_property` ya existen |
| `@on` decorator | `@nitro:event.window` en template es más flexible |
| SPA Navigation | Fuera de scope - usar HTMX boost o Turbo si se necesita |
| WebSockets | Fuera de scope - polling con `poll=N` es suficiente para 99% casos |

---

## Filosofía de Nitro

> **"Nitro abstrae el server round-trip. Alpine maneja el client-side."**

1. **ZeroJS para el desarrollador** - No escribes JavaScript, solo template tags
2. **Server-side cuando necesario** - `nitro_model`, `nitro_action`, `nitro_key`
3. **Client-side cuando posible** - `nitro_toggle`, `nitro_set`, `nitro_show`
4. **Pydantic para validación** - Tipado fuerte, no Django Forms
5. **Alpine.js bajo el capó** - Potencia sin complejidad

---

## Comparación con Alternativas

| Feature | Livewire | Unicorn | HTMX | Nitro |
|---------|----------|---------|------|-------|
| Zero JS | ❌ | ❌ | ✅ | ✅ |
| Typed State | ❌ | ❌ | ❌ | ✅ (Pydantic) |
| Client-side state | ❌ | ❌ | ❌ | ✅ (Alpine) |
| Two-way binding | ✅ | ✅ | ❌ | ✅ |
| Dirty tracking | ✅ | ✅ | ❌ | ✅ |
| Events system | ✅ | ✅ | ✅ | ✅ |
| File uploads | ✅ | ✅ | ❌ | ✅ |
| SEO friendly | ❌ | ❌ | ✅ | ✅ |
| Polling | ✅ | ✅ | ✅ | ✅ |
| Debug tools | ✅ | ❌ | ❌ | ✅ |

**Ventajas únicas de Nitro:**
- `on_success` callback en acciones
- `beforeunload` warning automático para dirty state
- `refresh_component()` para refrescar otros componentes
- State diffing para listas grandes (smart_updates)
- Pydantic para validación con tipos

---

## Prioridades Inmediatas

| Prioridad | Feature | Esfuerzo | Status |
|-----------|---------|----------|--------|
| P0 | Testing Helpers | 3-4h | Pendiente |
| P0 | nitro_error tag | 30min | Pendiente |
| P1 | Mejor error messages | 2h | Pendiente |
| P1 | VSCode snippets | 1h | Pendiente |
| P2 | Lazy loading | 2h | Futuro |
| P2 | Batch sync | 3h | Futuro |
| P3 | UI Component Library | 10h+ | Futuro |

---

## Changelog Reciente

### v0.6.1 (2026-01-18)
- Added `refresh()` method to base NitroComponent
- Added automatic dirty tracking (`isDirty`, `trackChange()`)
- Added `beforeunload` warning for unsaved changes
- Added `{% nitro_key %}` for keyboard event handlers
- Added `{% nitro_toggle %}` for client-side boolean toggles
- Added `{% nitro_set %}` for client-side value assignment
- Updated all form field templates with dirty tracking
