# Quick Start

Let's build a simple counter component to understand Django Nitro basics.

## 1. Define the Component

```python
# myapp/components/counter.py
from pydantic import BaseModel
from nitro.base import NitroComponent
from nitro.registry import register_component


class CounterState(BaseModel):
    """State schema for the counter component."""
    count: int = 0
    step: int = 1


@register_component
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    # state_class auto-inferred from Generic (v0.7.0)

    def get_initial_state(self, **kwargs):
        """Initialize the component state."""
        return CounterState(
            count=kwargs.get('initial', 0),
            step=kwargs.get('step', 1)
        )

    def increment(self):
        """Action: increment the counter."""
        self.state.count += self.state.step
        self.success(f"Count increased to {self.state.count}")

    def decrement(self):
        """Action: decrement the counter."""
        self.state.count -= self.state.step

    def reset(self):
        """Action: reset to zero."""
        self.state.count = 0
```

## 2. Create the Template

```html
<!-- templates/components/counter.html -->
{% load nitro_tags %}

<div class="counter-widget">
    <h2>Counter: {% nitro_text 'count' %}</h2>

    <div class="controls">
        <button @click="call('decrement')" :disabled="isLoading">-</button>
        <button @click="call('reset')" :disabled="isLoading">Reset</button>
        <button @click="call('increment')" :disabled="isLoading">+</button>
    </div>

    <!-- Show loading state -->
    <div x-show="isLoading" class="loading">Updating...</div>

    <!-- Show messages -->
    <template x-for="msg in messages" :key="msg.text">
        <div class="alert" x-text="msg.text"></div>
    </template>
</div>
```

## 3. Use in Your View

```python
# myapp/views.py
from django.shortcuts import render
from myapp.components.counter import Counter

def counter_page(request):
    # Initialize the component with custom values
    component = Counter(request=request, initial=10, step=5)
    return render(request, 'counter_page.html', {'counter': component})
```

```html
<!-- templates/counter_page.html -->
{% extends "base.html" %}

{% block content %}
    <h1>Counter Demo</h1>
    {{ counter.render }}
{% endblock %}
```

## That's it! 🎉

You now have a fully reactive counter component without writing any JavaScript.

## What's Happening?

1. **State** is defined as a Pydantic model (`CounterState`)
2. **Actions** are Python methods (`increment`, `decrement`, `reset`)
3. **Template** uses Alpine.js directives (`x-text`, `@click`, `x-show`)
4. **Reactivity** is handled automatically by Nitro + Alpine

## Next Steps

- [Learn about Components](../core-concepts/components.md)
- [Explore CRUD operations](../components/crud-nitro-component.md)
- [Try more examples](../examples/counter.md)
