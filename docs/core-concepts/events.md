# Events & Inter-Component Communication

Django Nitro provides a powerful event system for communication between components and custom integrations.

## Overview

The event system allows components to:
- Emit custom events to JavaScript listeners
- Trigger refreshes in other components
- Listen to built-in Nitro events
- Build complex multi-component workflows

## Emitting Custom Events

Use the `emit()` method to send custom events from your component:

```python
from nitro import NitroComponent, register_component

@register_component
class ShoppingCart(NitroComponent[CartState]):
    def add_to_cart(self, product_id: int):
        # Add product to cart
        product = Product.objects.get(id=product_id)
        self.state.items.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price)
        })

        # Emit event that other components can listen to
        self.emit('cart-updated', {
            'item_count': len(self.state.items),
            'product_id': product_id,
            'product_name': product.name
        })

        self.success(f"Added {product.name} to cart")
```

### Event Name Conventions

- Events are automatically prefixed with `nitro:` if not already present
- `emit('cart-updated')` → dispatches `nitro:cart-updated`
- `emit('nitro:custom')` → dispatches `nitro:custom` (no double prefix)

## Refreshing Other Components

The `refresh_component()` helper triggers a refresh in another component:

```python
@register_component
class ProductEditor(ModelNitroComponent[ProductSchema]):
    def save_product(self):
        obj = self.get_object(self.state.id)
        obj.name = self.state.name
        obj.price = self.state.price
        obj.save()

        # Tell the ProductList component to refresh
        self.refresh_component('ProductList')

        self.success("Product saved!")
```

This emits a `nitro:refresh-productlist` event that your components can listen to and respond by refreshing their data.

## Listening to Events in JavaScript

Listen to Nitro events in your templates or custom JavaScript:

```html
<script>
// Listen for cart updates
window.addEventListener('nitro:cart-updated', (event) => {
    console.log('Cart updated:', event.detail);
    // event.detail contains: { component: 'ShoppingCart', item_count: 3, product_id: 42 }

    // Update cart badge
    const badge = document.getElementById('cart-badge');
    if (badge) {
        badge.textContent = event.detail.item_count;
        badge.classList.add('pulse');
    }
});

// Listen for product list refresh requests
window.addEventListener('nitro:refresh-productlist', (event) => {
    console.log('ProductList should refresh');
    // Your ProductList component can listen and trigger a reload
});
</script>
```

## Built-in DOM Events

Nitro automatically dispatches these events for all components:

### nitro:message

Dispatched for each message/toast notification:

```javascript
window.addEventListener('nitro:message', (event) => {
    console.log('Message:', event.detail);
    // {
    //   component: 'MyComponent',
    //   level: 'success',  // 'success', 'error', 'warning', 'info'
    //   text: 'Operation completed!'
    // }

    // Example: Send to analytics
    analytics.track('nitro_message', {
        component: event.detail.component,
        level: event.detail.level
    });
});
```

### nitro:action-complete

Dispatched when an action completes successfully:

```javascript
window.addEventListener('nitro:action-complete', (event) => {
    console.log('Action completed:', event.detail);
    // {
    //   component: 'MyComponent',
    //   action: 'save',
    //   state: { ... }  // New state after action
    // }

    // Example: Track successful actions
    if (event.detail.action === 'purchase') {
        gtag('event', 'purchase', {
            component: event.detail.component
        });
    }
});
```

### nitro:error

Dispatched when an error occurs:

```javascript
window.addEventListener('nitro:error', (event) => {
    console.error('Nitro error:', event.detail);
    // {
    //   component: 'MyComponent',
    //   action: 'save',
    //   error: 'Server error message',
    //   status: 500
    // }

    // Example: Send to error tracking
    Sentry.captureException(new Error(event.detail.error), {
        tags: {
            component: event.detail.component,
            action: event.detail.action
        }
    });
});
```

## Multi-Component Workflow Example

Here's a complete example of components communicating via events:

### Product Editor Component

```python
@register_component
class ProductEditor(ModelNitroComponent[ProductSchema]):
    model = Product
    template_name = "components/product_editor.html"
    # state_class auto-inferred from Generic (v0.7.0)

    def delete_product(self):
        obj = self.get_object(self.state.id)
        product_name = obj.name
        product_category = obj.category
        obj.delete()

        # Notify analytics component
        self.emit('product-deleted', {
            'product_name': product_name,
            'category': product_category
        })

        # Refresh the product list
        self.refresh_component('ProductList')

        # Refresh the category stats
        self.refresh_component('CategoryStats')

        self.success(f"Deleted {product_name}")
```

### JavaScript Listener

```html
<!-- In your base template or specific page -->
<script>
window.addEventListener('nitro:product-deleted', (event) => {
    const { product_name, category } = event.detail;

    // Track deletion in analytics
    fetch('/api/analytics/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            event: 'product_deleted',
            product_name: product_name,
            category: category,
            timestamp: new Date().toISOString()
        })
    });

    // Show custom notification
    console.log(`Product ${product_name} was deleted`);
});

// Listen for refresh requests
window.addEventListener('nitro:refresh-productlist', () => {
    // Trigger reload in your ProductList component
    // This could trigger a search_items call or reload the component
    console.log('ProductList should reload');
});
</script>
```

## Use Cases

### 1. Shopping Cart Updates

Update cart badge when items are added:

```python
# In product component
def add_to_cart(self, product_id: int):
    self.state.cart_items.append(product_id)
    self.emit('cart-updated', {'count': len(self.state.cart_items)})
```

```javascript
// Update badge everywhere
window.addEventListener('nitro:cart-updated', (e) => {
    document.querySelectorAll('.cart-badge').forEach(badge => {
        badge.textContent = e.detail.count;
    });
});
```

### 2. Real-time Notifications

Notify users when background tasks complete:

```python
# In background task component
def process_export(self):
    # ... processing ...
    self.emit('export-ready', {
        'download_url': '/exports/file.csv',
        'file_size': '2.5MB'
    })
```

```javascript
window.addEventListener('nitro:export-ready', (e) => {
    new Notification('Export Ready', {
        body: `Download ready (${e.detail.file_size})`
    });
});
```

### 3. Analytics Tracking

Track user actions for analytics:

```python
# In any component
def important_action(self):
    # ... action logic ...
    self.emit('user-action', {
        'action_type': 'purchase',
        'value': 99.99
    })
```

```javascript
window.addEventListener('nitro:user-action', (e) => {
    gtag('event', e.detail.action_type, {
        value: e.detail.value
    });
});
```

### 4. Component Coordination

Coordinate multiple related components:

```python
@register_component
class OrderCreator(NitroComponent[OrderState]):
    def create_order(self):
        # Create order
        order = Order.objects.create(...)

        # Refresh related components
        self.refresh_component('OrderList')
        self.refresh_component('InventoryStatus')
        self.refresh_component('RevenueChart')

        # Notify analytics
        self.emit('order-created', {
            'order_id': order.id,
            'total': float(order.total)
        })
```

## Best Practices

### 1. Use Descriptive Event Names

```python
# ✅ Good - Clear and specific
self.emit('product-deleted', {'product_id': 123})
self.emit('payment-completed', {'order_id': 456})

# ❌ Bad - Too generic
self.emit('update', {'data': ...})
self.emit('done', {})
```

### 2. Include Useful Context

```python
# ✅ Good - Includes relevant data
self.emit('inventory-low', {
    'product_id': product.id,
    'product_name': product.name,
    'current_stock': product.stock,
    'threshold': 10
})

# ❌ Bad - Missing context
self.emit('inventory-low', {})
```

### 3. Avoid Event Loops

```python
# ❌ Bad - Can cause infinite loops
class ComponentA(NitroComponent[StateA]):
    def action(self):
        self.refresh_component('ComponentB')  # Triggers ComponentB

class ComponentB(NitroComponent[StateB]):
    def action(self):
        self.refresh_component('ComponentA')  # Triggers ComponentA → Loop!
```

### 4. Document Your Events

```python
@register_component
class ProductManager(CrudNitroComponent[ProductState]):
    """
    Product management component.

    Emitted Events:
    - nitro:product-created: {product_id, product_name, category}
    - nitro:product-updated: {product_id, changes: [...]}
    - nitro:product-deleted: {product_id, product_name}

    Listens to:
    - nitro:refresh-productmanager: Reloads product list
    """
    pass
```

## Advanced: Chaining Events

Build complex workflows by chaining events:

```python
# Step 1: User creates order
@register_component
class OrderForm(NitroComponent[OrderFormState]):
    def submit_order(self):
        order = Order.objects.create(...)
        self.emit('order-created', {'order_id': order.id})
```

```javascript
// Step 2: JavaScript handles payment
window.addEventListener('nitro:order-created', async (e) => {
    const orderId = e.detail.order_id;

    // Process payment
    const payment = await stripe.processPayment(orderId);

    // Trigger next step via Nitro component action
    // (You'd need to call a component action here to continue the workflow)
});
```

```python
# Step 3: Payment confirmation
@register_component
class PaymentProcessor(NitroComponent[PaymentState]):
    def confirm_payment(self, order_id: int, payment_id: str):
        # Confirm payment
        order = Order.objects.get(id=order_id)
        order.status = 'paid'
        order.save()

        # Notify fulfillment
        self.emit('order-paid', {
            'order_id': order_id,
            'payment_id': payment_id
        })

        # Refresh order list
        self.refresh_component('OrderList')
```

## See Also

- [API Reference: Event Methods](../api-reference.md#event-methods-v040)
- [API Reference: DOM Events](../api-reference.md#dom-events-v040)
- [Toast Adapters](TOAST_ADAPTERS.md) - Using events with toast notifications
