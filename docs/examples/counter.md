# Counter Example

The Counter example is a simple, beginner-friendly demonstration of Django Nitro's core concepts. It shows how to build a reactive component without any database interaction.

## Location

```
examples/counter/
├── config/              # Django project settings
├── counter_app/
│   ├── components/     # Nitro components
│   │   └── counter.py
│   └── templates/
│       └── components/
│           └── counter.html
├── manage.py
└── README.md
```

## What It Demonstrates

- Basic `NitroComponent` usage
- State management with Pydantic
- Action methods
- Success messages
- AlpineJS template integration
- No database required

## The Component

### State Definition

```python
from pydantic import BaseModel

class CounterState(BaseModel):
    """State schema for the counter component."""
    count: int = 0
    step: int = 1
```

**Fields:**
- `count` - Current counter value
- `step` - Increment/decrement amount

### Component Class

```python
from nitro.base import NitroComponent
from nitro.registry import register_component

@register_component
class Counter(NitroComponent[CounterState]):
    template_name = "components/counter.html"
    state_class = CounterState

    def get_initial_state(self, **kwargs):
        """Initialize with custom values if provided."""
        return CounterState(
            count=kwargs.get('initial', 0),
            step=kwargs.get('step', 1)
        )

    def increment(self):
        """Increase counter by step amount."""
        self.state.count += self.state.step
        self.success(f"Count increased to {self.state.count}")

    def decrement(self):
        """Decrease counter by step amount."""
        self.state.count -= self.state.step
        self.success(f"Count decreased to {self.state.count}")

    def reset(self):
        """Reset counter to zero."""
        self.state.count = 0
        self.success("Counter reset to 0")
```

**Actions:**
- `increment()` - Adds `step` to `count`
- `decrement()` - Subtracts `step` from `count`
- `reset()` - Sets `count` back to 0

### Template

```html
<div class="counter-widget">
    <h2>Counter: <span x-text="count"></span></h2>

    <div class="controls">
        <!-- Decrement button -->
        <button
            @click="call('decrement')"
            :disabled="isLoading"
            class="btn btn-secondary"
        >
            -
        </button>

        <!-- Reset button -->
        <button
            @click="call('reset')"
            :disabled="isLoading"
            class="btn btn-outline"
        >
            Reset
        </button>

        <!-- Increment button -->
        <button
            @click="call('increment')"
            :disabled="isLoading"
            class="btn btn-primary"
        >
            +
        </button>
    </div>

    <!-- Step control -->
    <div class="step-control">
        <label>
            Step:
            <input
                type="number"
                x-model.number="step"
                min="1"
                max="100"
            >
        </label>
    </div>

    <!-- Loading indicator -->
    <div x-show="isLoading" class="loading">
        <span>Processing...</span>
    </div>

    <!-- Messages -->
    <div class="messages">
        <template x-for="msg in messages" :key="msg.text">
            <div
                :class="'alert alert-' + msg.level"
                x-text="msg.text"
            ></div>
        </template>
    </div>
</div>
```

**Alpine Features Used:**
- `x-text` - Display reactive state
- `@click` - Handle button clicks
- `:disabled` - Disable during loading
- `x-model.number` - Two-way binding for step
- `x-show` - Conditional display
- `x-for` - Loop through messages

## Usage in Views

```python
from django.shortcuts import render
from counter_app.components.counter import Counter

def index(request):
    """Home page with counter component."""
    # Initialize with custom values
    counter = Counter(
        request=request,
        initial=10,  # Start at 10
        step=5       # Increment by 5
    )

    return render(request, 'index.html', {
        'counter': counter
    })
```

## Running the Example

### Setup

```bash
cd examples/counter

# Create virtual environment
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# Install dependencies
pip install django django-ninja pydantic django-nitro

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

### Access

Visit: `http://localhost:8000/`

## Key Concepts

### 1. State is Reactive

When you click increment, the state changes and the UI updates automatically:

```
User clicks "+" button
→ call('increment') sent to server
→ increment() method executes
→ self.state.count += self.state.step
→ Updated state sent back to client
→ Alpine updates display
```

### 2. Actions are Server-Side

All logic runs on the server:

```python
def increment(self):
    self.state.count += self.state.step  # Server-side Python
    self.success("Count increased")     # Server generates message
```

No JavaScript needed for business logic!

### 3. Two-Way Binding

The step input uses `x-model`:

```html
<input x-model.number="step" type="number">
```

Changes are local until an action is called. The server gets the updated `step` value with every action.

### 4. Loading States

AlpineJS provides `isLoading` automatically:

```html
<button :disabled="isLoading">
    Click Me
</button>

<div x-show="isLoading">
    Processing...
</div>
```

### 5. Messages

Server-side messages appear in the template:

```python
# Server
self.success("Counter reset!")
```

```html
<!-- Client -->
<template x-for="msg in messages">
    <div x-text="msg.text"></div>
</template>
```

## Customization Ideas

### Add a Maximum

```python
class CounterState(BaseModel):
    count: int = 0
    step: int = 1
    max_count: int = 100

class Counter(NitroComponent[CounterState]):
    def increment(self):
        if self.state.count + self.state.step > self.state.max_count:
            self.error(f"Cannot exceed {self.state.max_count}")
            return

        self.state.count += self.state.step
        self.success(f"Count: {self.state.count}")
```

### Add History

```python
class CounterState(BaseModel):
    count: int = 0
    step: int = 1
    history: list[int] = Field(default_factory=list)

class Counter(NitroComponent[CounterState]):
    def increment(self):
        self.state.history.append(self.state.count)
        self.state.count += self.state.step

    def undo(self):
        if self.state.history:
            self.state.count = self.state.history.pop()
            self.success("Undone")
        else:
            self.error("Nothing to undo")
```

### Persist to Session

```python
class Counter(NitroComponent[CounterState]):
    def get_initial_state(self, **kwargs):
        # Load from session
        count = self.request.session.get('counter_value', 0)
        return CounterState(count=count)

    def increment(self):
        self.state.count += self.state.step

        # Save to session
        self.request.session['counter_value'] = self.state.count
        self.success(f"Count: {self.state.count}")
```

## What's Next?

After understanding the Counter example, explore:

1. **[Property Manager Example](property-manager.md)** - See CRUD operations with Django models
2. **[BaseListComponent](../components/base-list-component.md)** - Learn about pagination and search
3. **[Security Mixins](../security/overview.md)** - Add authentication and permissions

## Troubleshooting

### Counter Not Updating

Check:
1. Is `nitro.js` loaded after Alpine?
2. Is the component registered with `@register_component`?
3. Check browser console for errors

### State Resets on Refresh

This is normal! Component state is not persistent by default. To persist:
- Use Django sessions (see customization above)
- Use database models (see Property Manager example)
- Use browser localStorage (requires custom JavaScript)

## Complete Code

The full working example is available in:

```
examples/counter/
```

Clone the repository and run it to see it in action!

## Learn More

- [NitroComponent Reference](../components/nitro-component.md)
- [State Management Guide](../core-concepts/state-management.md)
- [Actions Guide](../core-concepts/actions.md)
