# Debugging Tools

Django Nitro v0.5.0 includes powerful debugging tools to help you understand what's happening in your components.

## Table of Contents
- [NITRO_DEBUG Mode](#nitro_debug-mode)
- [Django Debug Toolbar Panel](#django-debug-toolbar-panel)
- [Browser DevTools](#browser-devtools)
- [Common Debug Scenarios](#common-debug-scenarios)

---

## NITRO_DEBUG Mode

Enable debug mode to see detailed information about template tags in your HTML.

### Configuration

Add to your Django `settings.py`:

```python
# settings.py
DEBUG = True  # Django's DEBUG must be True

NITRO = {
    'DEBUG': True,  # Enable Nitro debug mode
    'TOASTS': {
        'enabled': True,
        # ... other settings
    }
}
```

### What It Does

When `NITRO_DEBUG` is enabled, all template tags add a `data-nitro-debug` attribute to their HTML output with information about the tag's configuration.

**Example:**

Template:
```html
<input type="text" {% nitro_model 'email' debounce='300ms' %}>
```

Output (with NITRO_DEBUG enabled):
```html
<input type="text"
       data-nitro-debug="nitro_model: field='email', debounce=300ms"
       x-model="email"
       @input.debounce.300ms="call('_sync_field', {field: 'email', value: email})"
       :class="{'border-red-500': errors.email}">
```

### Debug Info by Template Tag

#### `{% nitro_model %}`
```html
data-nitro-debug="nitro_model: field='email', debounce=300ms, lazy=True"
```

#### `{% nitro_action %}`
```html
data-nitro-debug="nitro_action: action='submit', params=(id=item.id, confirm=true)"
```

#### `{% nitro_attr %}`
```html
data-nitro-debug="nitro_attr: src=product.image_url"
```

#### `{% nitro_disabled %}`
```html
data-nitro-debug="nitro_disabled: isProcessing || !isValid"
```

#### `{% nitro_file %}`
```html
data-nitro-debug="nitro_file: field='avatar', accept='image/*', max_size=5MB, preview=True"
```

### Inspecting Debug Info

Use your browser's DevTools to inspect elements and see the `data-nitro-debug` attributes:

1. Right-click on an element
2. Choose "Inspect Element"
3. Look for the `data-nitro-debug` attribute

---

## Django Debug Toolbar Panel

The Nitro Debug Toolbar panel shows component state, actions, and events during a request.

### Installation

1. **Install Django Debug Toolbar** (if not already installed):
   ```bash
   pip install django-debug-toolbar
   ```

2. **Add to INSTALLED_APPS** in `settings.py`:
   ```python
   INSTALLED_APPS = [
       # ...
       'debug_toolbar',
       'nitro',
   ]
   ```

3. **Add Nitro Panel to DEBUG_TOOLBAR_PANELS**:
   ```python
   DEBUG_TOOLBAR_PANELS = [
       'debug_toolbar.panels.history.HistoryPanel',
       'debug_toolbar.panels.versions.VersionsPanel',
       'debug_toolbar.panels.timer.TimerPanel',
       'debug_toolbar.panels.settings.SettingsPanel',
       'debug_toolbar.panels.headers.HeadersPanel',
       'debug_toolbar.panels.request.RequestPanel',
       'debug_toolbar.panels.sql.SQLPanel',
       'debug_toolbar.panels.staticfiles.StaticFilesPanel',
       'debug_toolbar.panels.templates.TemplatesPanel',
       'debug_toolbar.panels.cache.CachePanel',
       'debug_toolbar.panels.signals.SignalsPanel',
       'debug_toolbar.panels.redirects.RedirectsPanel',
       'debug_toolbar.panels.profiling.ProfilingPanel',
       'nitro.debug_toolbar_panel.NitroDebugPanel',  # <-- Add this
   ]
   ```

4. **Add Debug Toolbar middleware**:
   ```python
   MIDDLEWARE = [
       # ...
       'debug_toolbar.middleware.DebugToolbarMiddleware',
       # ...
   ]
   ```

5. **Configure INTERNAL_IPS**:
   ```python
   INTERNAL_IPS = [
       '127.0.0.1',
   ]
   ```

6. **Add to URLs**:
   ```python
   # urls.py
   from django.conf import settings

   if settings.DEBUG:
       import debug_toolbar
       urlpatterns += [
           path('__debug__/', include(debug_toolbar.urls)),
       ]
   ```

### What It Shows

The Nitro panel displays:

#### 1. Components Rendered
- Component name
- Template path
- Secure fields
- Smart updates status (enabled/disabled)
- Full component state (formatted JSON)

#### 2. Action Calls
- Component and action name (e.g., `Counter.increment()`)
- Payload parameters
- File upload indicator (if action includes file upload)

#### 3. Events Emitted
- Event name
- Source component
- Event data/payload

#### 4. Summary
- Total components rendered
- Total actions called
- Total events emitted

### Example Screenshot

```
┌─────────────────────────────────────────────────┐
│ Nitro                                      [3]  │
├─────────────────────────────────────────────────┤
│ Components Rendered                        [3]  │
│                                                 │
│ ┌─ Counter ────────────────────────────────┐  │
│ │ Template: components/counter.html         │  │
│ │ Secure Fields: None                       │  │
│ │ Smart Updates: Disabled                   │  │
│ │ State: {                                  │  │
│ │   "count": 5,                             │  │
│ │   "step": 1                               │  │
│ │ }                                         │  │
│ └───────────────────────────────────────────┘  │
│                                                 │
│ Action Calls                               [2]  │
│                                                 │
│ ⚡ Counter.increment()                         │
│ ⚡ Counter.increment()                         │
│                                                 │
│ Events Emitted                             [0]  │
│                                                 │
│ No events emitted                              │
└─────────────────────────────────────────────────┘
```

---

## Browser DevTools

### Client-Side Debug Mode

Enable JavaScript debug logging by setting `window.NITRO_DEBUG = true`:

```html
<script>
    window.NITRO_DEBUG = true;
</script>
{% nitro_scripts %}
```

This will log detailed information to the browser console:

```
[Nitro] Initializing Counter with state: {count: 0, step: 1}
[Nitro] Calling action: increment
[Nitro] State being sent: {count: 5, step: 1}
[Nitro] Event: nitro:action-complete {action: "increment", state: {...}}
✅ [success]: Counter incremented
```

### Console Events

You can listen to Nitro events in the console:

```javascript
// Listen to all action completions
window.addEventListener('nitro:action-complete', (e) => {
    console.log('Action completed:', e.detail);
});

// Listen to errors
window.addEventListener('nitro:error', (e) => {
    console.error('Nitro error:', e.detail);
});

// Listen to custom events
window.addEventListener('nitro:user-updated', (e) => {
    console.log('User updated:', e.detail.data);
});
```

---

## Common Debug Scenarios

### Scenario 1: Field Not Syncing

**Problem:** Changes to an input field aren't updating the component state.

**Debug Steps:**

1. **Check HTML debug attribute**:
   ```html
   <input data-nitro-debug="nitro_model: field='email'">
   ```
   Verify the field name is correct.

2. **Check browser console** (with `NITRO_DEBUG = true`):
   ```
   [Nitro] Calling action: _sync_field
   [Nitro] Payload: {field: 'email', value: 'test@example.com'}
   ```

3. **Check Debug Toolbar panel**:
   - Look at "Action Calls" section
   - Verify `_sync_field` action was called
   - Check component state in "Components Rendered"

**Common Causes:**
- Typo in field name
- Field doesn't exist in state schema
- JavaScript error preventing sync

---

### Scenario 2: Action Not Working

**Problem:** Button click doesn't trigger an action.

**Debug Steps:**

1. **Check HTML debug attribute**:
   ```html
   <button data-nitro-debug="nitro_action: action='submit'">
   ```

2. **Check browser console**:
   ```
   [Nitro] Calling action: submit
   ❌ [error]: Server error: 500
   ```

3. **Check Debug Toolbar**:
   - Verify action appears in "Action Calls"
   - Check for errors in SQL panel
   - Review request/response in Network tab

**Common Causes:**
- Action method doesn't exist
- Permission error
- Validation error
- Server exception

---

### Scenario 3: Events Not Firing

**Problem:** Custom events aren't being received.

**Debug Steps:**

1. **Check if event is emitted** (Debug Toolbar):
   - Look in "Events Emitted" section
   - Verify event name and data

2. **Check browser console**:
   ```
   [Nitro] Event: nitro:user-updated {userId: 123}
   ```

3. **Verify event listener**:
   ```html
   <div @nitro:user-updated.window="call('refresh')">
   ```

**Common Causes:**
- Event name mismatch (case-sensitive)
- Missing `.window` modifier for cross-component events
- Event listener on wrong element

---

### Scenario 4: File Upload Failing

**Problem:** File upload isn't working.

**Debug Steps:**

1. **Check HTML debug attribute**:
   ```html
   <input data-nitro-debug="nitro_file: field='avatar', accept='image/*', max_size=5MB">
   ```

2. **Check browser console**:
   ```
   [Nitro] File selected: avatar.jpg 2048576 bytes
   [Nitro] File too large: 2.00 MB > 5.00 MB
   ```

3. **Check network tab**:
   - Look for `/api/nitro/dispatch` request
   - Verify `Content-Type: multipart/form-data`
   - Check file is included in FormData

**Common Causes:**
- File too large
- Invalid file type
- `_handle_file_upload` not implemented
- Server upload size limit

---

## Best Practices

1. **Always enable NITRO_DEBUG during development**
   ```python
   NITRO = {'DEBUG': settings.DEBUG}
   ```

2. **Use Django Debug Toolbar for server-side debugging**
   - Check component state
   - Verify actions are being called
   - Monitor events

3. **Use browser console for client-side debugging**
   ```javascript
   window.NITRO_DEBUG = true;
   ```

4. **Inspect HTML attributes**
   - Use browser DevTools to verify `data-nitro-debug` attributes
   - Confirm Alpine.js directives are correct

5. **Monitor network requests**
   - Check `/api/nitro/dispatch` calls
   - Verify request/response payloads
   - Look for errors

6. **Disable debug mode in production**
   ```python
   NITRO = {
       'DEBUG': False,  # Disable in production
   }
   ```

---

## Troubleshooting Guide

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| No debug attributes in HTML | `NITRO.DEBUG` not enabled | Set `NITRO = {'DEBUG': True}` |
| Panel not showing in toolbar | Not added to `DEBUG_TOOLBAR_PANELS` | Add `nitro.debug_toolbar_panel.NitroDebugPanel` |
| No console logs | `window.NITRO_DEBUG` not set | Add `<script>window.NITRO_DEBUG=true</script>` |
| Events not tracked | Debug Toolbar not instrumented | Ensure panel is loaded before page render |
| State shows `<object>` | State not serializable | Implement `model_dump()` in state class |

---

## Next Steps

- **[Events System](events.md)** - Learn about inter-component communication
- **[Smart Updates](smart-updates.md)** - Optimize performance with state diffing
- **[API Reference](../api-reference.md)** - Complete API documentation
