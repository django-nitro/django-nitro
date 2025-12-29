# Toast Notification Adapters

Django Nitro v0.4.0+ includes a flexible toast system that supports custom notification libraries.

## Native Toasts (Default)

By default, Nitro uses built-in professional toasts without external dependencies.

### Configuration

In `settings.py`:

```python
NITRO = {
    'TOAST_ENABLED': True,
    'TOAST_POSITION': 'top-right',  # top-right, top-left, top-center, bottom-right, bottom-left, bottom-center
    'TOAST_DURATION': 3000,  # milliseconds
    'TOAST_STYLE': 'default',  # default, minimal, bordered
}
```

### Component-Level Override

```python
from nitro import NitroComponent, register_component

@register_component
class MyComponent(NitroComponent[MyState]):
    toast_enabled = True
    toast_position = 'bottom-right'
    toast_duration = 5000
    toast_style = 'minimal'

    def my_action(self):
        self.success("Operation completed!")
```

## Custom Toast Adapters

You can integrate any toast library by defining `window.NitroToastAdapter`.

### Adapter Interface

```javascript
window.NitroToastAdapter = {
    show: function(message, level, config) {
        // message: string - Toast message text
        // level: 'success' | 'error' | 'warning' | 'info'
        // config: { enabled, position, duration, style }

        // Your toast library implementation here
    }
};
```

## Integration Examples

### SweetAlert2

```html
<!-- Include SweetAlert2 -->
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>

<!-- Define adapter -->
<script>
window.NitroToastAdapter = {
    show: function(message, level, config) {
        const iconMap = {
            success: 'success',
            error: 'error',
            warning: 'warning',
            info: 'info'
        };

        const positionMap = {
            'top-right': 'top-end',
            'top-left': 'top-start',
            'top-center': 'top',
            'bottom-right': 'bottom-end',
            'bottom-left': 'bottom-start',
            'bottom-center': 'bottom'
        };

        Swal.fire({
            icon: iconMap[level],
            title: message,
            toast: true,
            position: positionMap[config.position] || 'top-end',
            timer: config.duration,
            timerProgressBar: true,
            showConfirmButton: false
        });
    }
};
</script>
```

### Toastify

```html
<!-- Include Toastify -->
<link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/toastify-js/src/toastify.min.css">
<script type="text/javascript" src="https://cdn.jsdelivr.net/npm/toastify-js"></script>

<!-- Define adapter -->
<script>
window.NitroToastAdapter = {
    show: function(message, level, config) {
        const colorMap = {
            success: 'linear-gradient(to right, #00b09b, #96c93d)',
            error: 'linear-gradient(to right, #ff5f6d, #ffc371)',
            warning: 'linear-gradient(to right, #f2994a, #f2c94c)',
            info: 'linear-gradient(to right, #667eea, #764ba2)'
        };

        const gravityMap = {
            'top-right': 'top',
            'top-left': 'top',
            'top-center': 'top',
            'bottom-right': 'bottom',
            'bottom-left': 'bottom',
            'bottom-center': 'bottom'
        };

        const positionMap = {
            'top-right': 'right',
            'top-left': 'left',
            'top-center': 'center',
            'bottom-right': 'right',
            'bottom-left': 'left',
            'bottom-center': 'center'
        };

        Toastify({
            text: message,
            duration: config.duration,
            gravity: gravityMap[config.position],
            position: positionMap[config.position],
            backgroundColor: colorMap[level],
            stopOnFocus: true
        }).showToast();
    }
};
</script>
```

### Notyf

```html
<!-- Include Notyf -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.css">
<script src="https://cdn.jsdelivr.net/npm/notyf@3/notyf.min.js"></script>

<!-- Define adapter -->
<script>
const notyf = new Notyf({
    duration: 3000,
    position: {
        x: 'right',
        y: 'top'
    }
});

window.NitroToastAdapter = {
    show: function(message, level, config) {
        if (level === 'success') {
            notyf.success(message);
        } else if (level === 'error') {
            notyf.error(message);
        } else {
            notyf.open({
                type: level,
                message: message,
                duration: config.duration
            });
        }
    }
};
</script>
```

## Disabling Toasts

### Globally

```python
# settings.py
NITRO = {
    'TOAST_ENABLED': False,
}
```

### Per Component

```python
@register_component
class MyComponent(NitroComponent[MyState]):
    toast_enabled = False
```

### Custom Event Handling

Listen to `nitro:message` events for manual handling:

```javascript
window.addEventListener('nitro:message', (event) => {
    const { level, text } = event.detail;
    console.log(`[${level}]: ${text}`);

    // Your custom handling here
});
```

## Best Practices

1. **Consistent Positioning**: Use the same position across your app for better UX
2. **Appropriate Duration**:
   - Success: 3000ms (quick confirmation)
   - Info: 4000ms (read time)
   - Warning: 5000ms (important)
   - Error: 6000ms or manual dismiss
3. **Style Consistency**: Choose one style and stick with it throughout your app
4. **Accessibility**: Ensure toasts are accessible (ARIA labels, keyboard dismissal)
5. **Mobile Testing**: Always test toast positioning and sizing on mobile devices

## Troubleshooting

### Toasts Not Showing

1. Check `TOAST_ENABLED` in settings
2. Verify `{% nitro_scripts %}` is included in your template
3. Check browser console for JavaScript errors
4. Ensure Alpine.js is loaded before Nitro

### Custom Adapter Not Working

1. Define `window.NitroToastAdapter` **before** Nitro initializes
2. Check adapter function signature matches the interface
3. Verify external library is loaded correctly
4. Test with `window.NITRO_DEBUG = true` for detailed logging

### Styling Issues

1. Ensure `nitro.css` is loaded
2. Check for CSS conflicts with existing styles
3. Override CSS classes if needed:

```css
.nitro-toast {
    /* Your custom styles */
    font-family: 'Your Font', sans-serif;
    border-radius: 12px;
}
```

## Advanced: Event-Driven Notifications

For complex scenarios, you can bypass toasts entirely and use events:

```python
# Component
def my_action(self):
    self.emit('custom-notification', {
        'type': 'special',
        'message': 'Something important happened',
        'data': {'id': 123}
    })
```

```javascript
// JavaScript
window.addEventListener('nitro:custom-notification', (event) => {
    const { type, message, data } = event.detail;

    // Your custom notification system
    showMyFancyNotification(message, data);
});
```

This gives you complete control over notification handling while still using Nitro's event system.
