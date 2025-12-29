# Smart State Updates (Diffing)

For components with large lists, Nitro provides an opt-in performance optimization that sends only the changes (diffs) instead of the full state.

## The Problem

Traditional state updates send the entire state on every action:

```python
@register_component
class TaskList(BaseListComponent[TaskListState]):
    def toggle_task(self, id: int):
        task = Task.objects.get(id=id)
        task.completed = not task.completed
        task.save()

        # Reload ALL 500 tasks
        self.refresh()

# Response sent to client: ~50KB (all 500 tasks)
{
    "state": {
        "items": [
            {"id": 1, "title": "Task 1", "completed": false},
            {"id": 2, "title": "Task 2", "completed": true},
            # ... 498 more tasks ...
        ]
    }
}
```

**Performance issues:**
- 50KB response for changing one field
- Client must re-render entire list
- Slow on mobile connections
- Poor UX for real-time updates

## The Solution: State Diffing

Enable `smart_updates` to send only the changes:

```python
@register_component
class TaskList(BaseListComponent[TaskListState]):
    smart_updates = True  # ← Enable diffing

    def toggle_task(self, id: int):
        task = Task.objects.get(id=id)
        task.completed = not task.completed
        task.save()

        # Reload state
        self.refresh()

# Response sent to client: ~1KB (only the changed task)
{
    "partial": true,
    "state": {
        "items": {
            "diff": {
                "added": [],
                "removed": [],
                "updated": [
                    {"id": 42, "title": "Task 42", "completed": true}
                ]
            }
        }
    }
}
```

**Benefits:**
- 98% reduction in response size (50KB → 1KB)
- Faster network transfer
- Client updates only changed items
- Better UX for real-time apps

---

## How It Works

### 1. Server-Side Diffing

When `smart_updates = True`, Nitro compares old state vs new state:

```python
# Before action
old_state = {"items": [
    {"id": 1, "title": "Task 1", "completed": false},
    {"id": 2, "title": "Task 2", "completed": true},
    {"id": 3, "title": "Task 3", "completed": false},
]}

# After action
new_state = {"items": [
    {"id": 1, "title": "Task 1", "completed": false},
    # id=2 removed
    {"id": 3, "title": "Task 3 (edited)", "completed": true},  # Updated
    {"id": 4, "title": "Task 4", "completed": false},  # Added
]}

# Diff calculation
diff = {
    "removed": [2],  # IDs of deleted items
    "updated": [{"id": 3, "title": "Task 3 (edited)", "completed": true}],
    "added": [{"id": 4, "title": "Task 4", "completed": false}]
}
```

### 2. Client-Side Application

The JavaScript layer applies changes in-place:

```javascript
// Receive diff response
{
    "partial": true,
    "state": {
        "items": {
            "diff": {
                "removed": [2],
                "updated": [{"id": 3, "title": "Task 3 (edited)", "completed": true}],
                "added": [{"id": 4, "title": "Task 4", "completed": false}]
            }
        }
    }
}

// Apply changes to existing array
function applyListDiff(currentArray, diff) {
    // Remove items
    diff.removed.forEach(id => {
        const index = currentArray.findIndex(item => item.id === id);
        if (index !== -1) {
            currentArray.splice(index, 1);
        }
    });

    // Update items
    diff.updated.forEach(updatedItem => {
        const index = currentArray.findIndex(item => item.id === updatedItem.id);
        if (index !== -1) {
            Object.assign(currentArray[index], updatedItem);
        }
    });

    // Add items
    diff.added.forEach(item => {
        currentArray.push(item);
    });
}
```

**Result:** No full re-render, only changed items update.

---

## Requirements

For state diffing to work, items must have an `id` field:

```python
class TaskSchema(BaseModel):
    id: int  # ← Required for diffing
    title: str
    completed: bool

class TaskListState(BaseListState):
    items: list[TaskSchema] = []  # ← Must be a list

@register_component
class TaskList(BaseListComponent[TaskListState]):
    smart_updates = True  # ✅ Will work
```

**Without `id` field:**

```python
class TaskSchema(BaseModel):
    # No id field!
    title: str
    completed: bool

@register_component
class TaskList(BaseListComponent[TaskListState]):
    smart_updates = True  # ⚠️ Will fall back to full state update
```

---

## When to Use

### ✅ Use Smart Updates For:

**1. Large Lists (100+ items)**
```python
@register_component
class ProductCatalog(BaseListComponent[ProductCatalogState]):
    smart_updates = True
    per_page = 100

    # 100 products = ~10KB response
    # Diff update = ~1KB (90% reduction)
```

**2. Real-Time Collaborative Editing**
```python
@register_component
class CollaborativeBoard(BaseListComponent[BoardState]):
    smart_updates = True

    def update_card(self, card_id: int, title: str):
        # Only send the changed card
        card = Card.objects.get(id=card_id)
        card.title = title
        card.save()
        self.refresh()
        # Sends ~100 bytes instead of 50KB
```

**3. Live Dashboards**
```python
@register_component
class LiveMetrics(BaseListComponent[MetricsState]):
    smart_updates = True

    def refresh_metrics(self):
        # Only updated metrics sent to client
        self.refresh()
```

**4. Frequent Updates**
```python
@register_component
class ChatMessages(BaseListComponent[ChatState]):
    smart_updates = True

    def send_message(self, text: str):
        # Only new message sent
        Message.objects.create(text=text, user=self.current_user)
        self.refresh()
```

### ❌ Don't Use For:

**1. Small Lists (< 50 items)**
```python
# ❌ Overhead not worth it
@register_component
class RecentNotifications(BaseListComponent[NotificationState]):
    smart_updates = True  # Not needed for 10-20 items
    per_page = 20
```

**2. Components Without Lists**
```python
# ❌ No list state to diff
@register_component
class UserProfile(ModelNitroComponent[ProfileSchema]):
    smart_updates = True  # Doesn't help
```

**3. Lists Without IDs**
```python
# ❌ Can't calculate diffs without IDs
class LogEntry(BaseModel):
    timestamp: str
    message: str
    # No id field!

@register_component
class LogViewer(BaseListComponent[LogState]):
    smart_updates = True  # Will fall back to full state
```

---

## Performance Comparison

### Scenario: 500-Item Task List

**Without smart_updates:**
```python
@register_component
class TaskList(BaseListComponent[TaskListState]):
    smart_updates = False  # Default

    def toggle_task(self, id: int):
        # ... toggle logic ...
        self.refresh()

# Response: 50KB (all 500 tasks)
# Network time: 500ms (on 3G)
# Render time: 200ms
# Total: 700ms
```

**With smart_updates:**
```python
@register_component
class TaskList(BaseListComponent[TaskListState]):
    smart_updates = True  # ← Enable

    def toggle_task(self, id: int):
        # ... toggle logic ...
        self.refresh()

# Response: 1KB (only changed task)
# Network time: 10ms (on 3G)
# Render time: 5ms (update one item)
# Total: 15ms ← 47x faster!
```

### Benchmark Results

| List Size | Full State | Diff State | Reduction |
|-----------|-----------|-----------|-----------|
| 50 items | 5KB | 4KB | 20% |
| 100 items | 10KB | 1KB | 90% |
| 500 items | 50KB | 1KB | 98% |
| 1000 items | 100KB | 1KB | 99% |

**Conclusion:** Bigger lists = bigger savings.

---

## Examples

### Example 1: Task Manager

```python
from pydantic import BaseModel, Field
from nitro import BaseListComponent, BaseListState, register_component
from tasks.models import Task


class TaskSchema(BaseModel):
    id: int  # Required for diffing
    title: str
    completed: bool
    priority: str

    class Config:
        from_attributes = True


class TaskListState(BaseListState):
    items: list[TaskSchema] = []


@register_component
class TaskList(BaseListComponent[TaskListState]):
    template_name = "components/task_list.html"
    state_class = TaskListState
    model = Task

    # Enable smart updates
    smart_updates = True

    search_fields = ['title']
    per_page = 100  # Large list → good candidate for diffing
    order_by = '-created_at'

    def toggle_completed(self, id: int):
        """Toggle task completion status."""
        task = self.model.objects.get(id=id)
        task.completed = not task.completed
        task.save()

        # Only the changed task is sent to client
        self.refresh()
        # Response: ~100 bytes instead of ~10KB

    def update_priority(self, id: int, priority: str):
        """Update task priority."""
        task = self.model.objects.get(id=id)
        task.priority = priority
        task.save()

        # Only the changed task is sent to client
        self.refresh()
```

**Result:**
- Toggling a task: 100 bytes instead of 10KB
- 100x faster on slow connections
- Smooth real-time experience

### Example 2: Real-Time Inventory

```python
@register_component
class InventoryDashboard(BaseListComponent[InventoryState]):
    smart_updates = True  # Essential for real-time updates

    def update_stock(self, product_id: int, quantity: int):
        """Update stock quantity."""
        product = Product.objects.get(id=product_id)
        product.stock = quantity
        product.save()

        # Only changed product sent
        self.refresh()

    def bulk_import(self, file):
        """Import multiple products."""
        # ... import 100 products ...

        # Diff will show:
        # - added: [100 new products]
        # - updated: []
        # - removed: []
        self.refresh()
```

### Example 3: Collaborative Kanban Board

```python
@register_component
class KanbanBoard(BaseListComponent[KanbanState]):
    smart_updates = True

    def move_card(self, card_id: int, column: str):
        """Move card to different column."""
        card = Card.objects.get(id=card_id)
        card.column = column
        card.order = self.get_next_order(column)
        card.save()

        # Only moved card sent to all clients
        self.refresh()
        self.emit('card-moved', {
            'card_id': card_id,
            'column': column
        })

    def edit_card_title(self, card_id: int, title: str):
        """Edit card title."""
        card = Card.objects.get(id=card_id)
        card.title = title
        card.save()

        # Minimal update
        self.refresh()
```

**Template:**
```html
<div class="kanban-board">
    <template x-for="card in items" :key="card.id">
        <div
            class="card"
            :class="card.column"
            draggable="true"
            @dragend="call('move_card', {card_id: card.id, column: $event.target.dataset.column})"
        >
            <input
                x-model="card.title"
                @blur="call('edit_card_title', {card_id: card.id, title: $event.target.value})"
            >
        </div>
    </template>
</div>
```

---

## Advanced: Controlling What Gets Diffed

Only lists with `id` fields are diffed. Other fields update normally:

```python
class DashboardState(BaseModel):
    tasks: list[TaskSchema] = []  # ← Has id, will be diffed
    stats: dict = {}  # ← No id, full update
    user_name: str = ""  # ← Simple field, full update

@register_component
class Dashboard(NitroComponent[DashboardState]):
    smart_updates = True

    def refresh_all(self):
        # tasks → diff sent
        # stats → full dict sent
        # user_name → full value sent
        self.refresh()
```

**Response:**
```json
{
    "partial": true,
    "state": {
        "tasks": {
            "diff": {
                "added": [...],
                "removed": [...],
                "updated": [...]
            }
        },
        "stats": {"total": 100, "completed": 50},  // Full update
        "user_name": "John Doe"  // Full update
    }
}
```

---

## Debugging

### Enable Debug Mode

```html
<script>
    window.NITRO_DEBUG = true;
</script>
<script src="{% static 'nitro/nitro.js' %}"></script>
```

**Console output:**
```
[Nitro] Calling action: toggle_task
[Nitro] State being sent: {...}
[Nitro] Response received (partial: true)
[Nitro] Applying diff to 'items':
  - Added: 0 items
  - Updated: 1 items
  - Removed: 0 items
```

### Verify Diffing Is Working

Check the response size in Network tab:

```
# Without smart_updates
Response: 50KB (full state)

# With smart_updates
Response: 1KB (diff only)
```

If you see full state despite `smart_updates = True`, check:
1. ✅ Items have `id` field?
2. ✅ List is in state (not a regular field)?
3. ✅ Items are Pydantic models (not dicts)?

---

## Best Practices

### 1. Use with Pagination

Combine smart updates with pagination for optimal performance:

```python
@register_component
class ProductList(BaseListComponent[ProductListState]):
    smart_updates = True
    per_page = 50  # Limit items per page

    # User sees 50 items
    # Diff updates are even smaller
```

### 2. Optimize Refresh Calls

Only refresh when necessary:

```python
# ✅ Good - Only refresh when data changes
def toggle_task(self, id: int):
    task = Task.objects.get(id=id)
    task.completed = not task.completed
    task.save()
    self.refresh()  # Data changed → refresh needed

# ❌ Bad - Refresh on every action
def validate_input(self):
    if not self.state.email:
        self.error("Email required")
        self.refresh()  # No data changed → unnecessary
```

### 3. Avoid Frequent Full Refreshes

```python
# ❌ Bad - Refreshes entire list on every change
def update_multiple_tasks(self, task_ids: list[int]):
    for task_id in task_ids:
        task = Task.objects.get(id=task_id)
        task.completed = True
        task.save()
        self.refresh()  # ← 10 refreshes for 10 tasks!

# ✅ Good - Single refresh at the end
def update_multiple_tasks(self, task_ids: list[int]):
    Task.objects.filter(id__in=task_ids).update(completed=True)
    self.refresh()  # ← 1 refresh for 10 tasks
```

---

## Limitations

### 1. Requires ID Field

Items without `id` field fall back to full state update.

### 2. Order Not Preserved

Diffs don't preserve list order. Added items appear at the end:

```python
# Before
items = [
    {"id": 1, "title": "A"},
    {"id": 2, "title": "B"},
]

# Add item with id=3 between A and B
items = [
    {"id": 1, "title": "A"},
    {"id": 3, "title": "C"},  # ← Inserted in middle
    {"id": 2, "title": "B"},
]

# Client sees (added items pushed to end)
items = [
    {"id": 1, "title": "A"},
    {"id": 2, "title": "B"},
    {"id": 3, "title": "C"},  # ← Appears at end
]
```

**Solution:** Use `order_by` to maintain consistent ordering.

### 3. Nested Lists Not Supported

Only top-level lists are diffed:

```python
class BoardState(BaseModel):
    columns: list[ColumnSchema] = []  # ← Diffed
    # Each column has:
    # - cards: list[CardSchema]  ← NOT diffed (nested)

# Workaround: Flatten structure
class BoardState(BaseModel):
    cards: list[CardSchema] = []  # ← All cards in one list
    # Use column field to group: card.column = "todo"
```

---

## See Also

- [API Reference: smart_updates](../api-reference.md#class-attributes)
- [BaseListComponent](../components/base-list-component.md)
- [Performance Best Practices](../best-practices.md)
