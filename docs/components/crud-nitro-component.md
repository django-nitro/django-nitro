# CrudNitroComponent

`CrudNitroComponent` extends `ModelNitroComponent` with pre-built Create, Read, Update, and Delete operations. It's designed for list views with inline editing and provides all the scaffolding for managing collections of model instances.

## When to Use

Use `CrudNitroComponent` when you need:

- **List views** with create/edit/delete functionality
- **Inline editing** of items in a table or list
- **Standard CRUD** operations without custom logic
- **Quick prototyping** of admin-style interfaces

**Examples:**
- Task list with add/edit/delete
- Product catalog management
- User management panel
- Any list-based CRUD interface

## Basic Structure

```python
from pydantic import BaseModel, Field
from nitro.base import CrudNitroComponent
from nitro.registry import register_component
from typing import Optional
from myapp.models import Task

# Schema for a single item (with id)
class TaskSchema(BaseModel):
    id: int
    title: str
    completed: bool = False

    class Config:
        from_attributes = True

# Schema for creating/editing (no id required)
class TaskFormSchema(BaseModel):
    title: str = ""
    completed: bool = False

# State schema for the component
class TaskListState(BaseModel):
    tasks: list[TaskSchema] = []
    create_buffer: TaskFormSchema = Field(default_factory=TaskFormSchema)
    edit_buffer: Optional[TaskFormSchema] = None
    editing_id: Optional[int] = None

# Component
@register_component
class TaskList(CrudNitroComponent[TaskListState]):
    template_name = "components/task_list.html"
    state_class = TaskListState
    model = Task

    def get_initial_state(self, **kwargs):
        return TaskListState(
            tasks=[TaskSchema.model_validate(t) for t in Task.objects.all()]
        )

    def refresh(self):
        self.state.tasks = [
            TaskSchema.model_validate(t)
            for t in Task.objects.all().order_by('-id')
        ]
```

## Pre-built Methods

`CrudNitroComponent` provides these methods out of the box:

### Create

#### `create_item() -> None`

Creates a new item from `state.create_buffer`.

**Behavior:**
1. Validates `create_buffer` data
2. Creates new model instance
3. Calls `refresh()` to reload list
4. Clears `create_buffer`
5. Shows success message

**Example usage in template:**
```html
<input x-model="create_buffer.title" placeholder="New task...">
<button @click="call('create_item')">Add</button>
```

**Override for custom logic:**
```python
def create_item(self):
    # Add owner automatically
    obj = self.model.objects.create(
        **self.state.create_buffer.dict(),
        owner=self.current_user
    )
    self.refresh()
    self.success(f"Created {obj.title}")
```

### Update

#### `start_edit(id: int) -> None`

Initiates editing mode for an item.

**Behavior:**
1. Finds item by ID in state
2. Copies item data to `edit_buffer`
3. Sets `editing_id` to the item's ID

**Example usage:**
```html
<button @click="call('start_edit', {id: task.id})">Edit</button>
```

#### `save_edit() -> None`

Saves changes from `edit_buffer` to database.

**Behavior:**
1. Gets model instance by `editing_id`
2. Updates fields from `edit_buffer`
3. Calls `refresh()` to reload list
4. Clears `editing_id` and `edit_buffer`
5. Shows success message

**Example usage:**
```html
<button @click="call('save_edit')">Save</button>
```

#### `cancel_edit() -> None`

Cancels editing mode without saving.

**Behavior:**
1. Clears `editing_id`
2. Clears `edit_buffer`

**Example usage:**
```html
<button @click="call('cancel_edit')">Cancel</button>
```

### Delete

#### `delete_item(id: int) -> None`

Deletes an item by ID.

**Behavior:**
1. Gets model instance by ID
2. Deletes from database
3. Calls `refresh()` to reload list
4. Shows success message

**Example usage:**
```html
<button @click="confirm('Delete?') && call('delete_item', {id: task.id})">
    Delete
</button>
```

**Override for soft delete:**
```python
def delete_item(self, id: int):
    obj = self.model.objects.get(id=id)
    obj.is_deleted = True  # Soft delete
    obj.save()
    self.refresh()
    self.success("Item archived")
```

## State Structure

Your state class should include these fields:

```python
class MyListState(BaseModel):
    # List of items (required)
    items: list[ItemSchema] = []

    # Create buffer (required)
    create_buffer: ItemFormSchema = Field(default_factory=ItemFormSchema)

    # Edit buffer (required)
    edit_buffer: Optional[ItemFormSchema] = None

    # Currently editing ID (required)
    editing_id: Optional[int] = None

    # Any additional fields you need
    filter_active: bool = True
    sort_by: str = "name"
```

## Complete Example

```python
from django.db import models
from pydantic import BaseModel, Field, validator
from nitro.base import CrudNitroComponent
from nitro.registry import register_component
from typing import Optional

# Django Model
class Todo(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

# Item schema (with id)
class TodoSchema(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    priority: int

    class Config:
        from_attributes = True

# Form schema (no id)
class TodoFormSchema(BaseModel):
    title: str = ""
    description: str = ""
    completed: bool = False
    priority: int = 0

    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title is required')
        return v.strip()

# State schema
class TodoListState(BaseModel):
    todos: list[TodoSchema] = []
    create_buffer: TodoFormSchema = Field(default_factory=TodoFormSchema)
    edit_buffer: Optional[TodoFormSchema] = None
    editing_id: Optional[int] = None

# Component
@register_component
class TodoList(CrudNitroComponent[TodoListState]):
    template_name = "components/todo_list.html"
    state_class = TodoListState
    model = Todo

    def get_initial_state(self, **kwargs):
        # Filter by current user
        todos = self.model.objects.filter(owner=self.request.user)
        return TodoListState(
            todos=[TodoSchema.model_validate(t) for t in todos]
        )

    def refresh(self):
        todos = self.model.objects.filter(owner=self.request.user)
        self.state.todos = [
            TodoSchema.model_validate(t) for t in todos
        ]
        self.state.editing_id = None
        self.state.edit_buffer = None
        self.state.create_buffer = TodoFormSchema()

    # Override create to add owner
    def create_item(self):
        if not self.require_auth():
            return

        try:
            todo = self.model.objects.create(
                **self.state.create_buffer.dict(),
                owner=self.current_user
            )
            self.refresh()
            self.success(f"Created: {todo.title}")
        except Exception as e:
            logger.exception("Create failed")
            self.error("Failed to create todo")

    # Custom action: toggle completion
    def toggle_completed(self, id: int):
        try:
            todo = self.model.objects.get(id=id, owner=self.current_user)
            todo.completed = not todo.completed
            todo.save()
            self.refresh()
        except self.model.DoesNotExist:
            self.error("Todo not found")

    # Custom action: set priority
    def set_priority(self, id: int, priority: int):
        if priority < 0 or priority > 5:
            self.error("Priority must be 0-5")
            return

        try:
            todo = self.model.objects.get(id=id, owner=self.current_user)
            todo.priority = priority
            todo.save()
            self.refresh()
            self.success("Priority updated")
        except self.model.DoesNotExist:
            self.error("Todo not found")
```

**Template:**

```html
<div class="todo-list">
    <!-- Create new todo -->
    <div class="create-form">
        <h3>Add Todo</h3>
        <input
            x-model="create_buffer.title"
            placeholder="What needs to be done?"
            @keyup.enter="call('create_item')"
        >
        <textarea
            x-model="create_buffer.description"
            placeholder="Description (optional)"
            rows="2"
        ></textarea>
        <select x-model.number="create_buffer.priority">
            <option value="0">Low Priority</option>
            <option value="1">Medium Priority</option>
            <option value="2">High Priority</option>
        </select>
        <button @click="call('create_item')" :disabled="isLoading">
            Add Todo
        </button>
    </div>

    <!-- Todo list -->
    <div class="todos">
        <template x-for="todo in todos" :key="todo.id">
            <div class="todo-item" :class="{'completed': todo.completed}">
                <!-- Normal view -->
                <template x-if="editing_id !== todo.id">
                    <div class="todo-view">
                        <!-- Checkbox -->
                        <input
                            type="checkbox"
                            :checked="todo.completed"
                            @click="call('toggle_completed', {id: todo.id})"
                        >

                        <!-- Content -->
                        <div class="todo-content">
                            <h4 x-text="todo.title"></h4>
                            <p x-text="todo.description" x-show="todo.description"></p>
                            <span class="priority" x-text="'Priority: ' + todo.priority"></span>
                        </div>

                        <!-- Actions -->
                        <div class="actions">
                            <button @click="call('start_edit', {id: todo.id})">
                                Edit
                            </button>
                            <button
                                @click="confirm('Delete this todo?') && call('delete_item', {id: todo.id})"
                                class="btn-danger"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </template>

                <!-- Edit view -->
                <template x-if="editing_id === todo.id && edit_buffer">
                    <div class="todo-edit">
                        <input
                            x-model="edit_buffer.title"
                            type="text"
                        >
                        <textarea
                            x-model="edit_buffer.description"
                            rows="2"
                        ></textarea>
                        <select x-model.number="edit_buffer.priority">
                            <option value="0">Low</option>
                            <option value="1">Medium</option>
                            <option value="2">High</option>
                        </select>

                        <div class="edit-actions">
                            <button @click="call('save_edit')">Save</button>
                            <button @click="call('cancel_edit')">Cancel</button>
                        </div>
                    </div>
                </template>
            </div>
        </template>
    </div>

    <!-- Empty state -->
    <div x-show="todos.length === 0" class="empty-state">
        <p>No todos yet. Add one above!</p>
    </div>

    <!-- Messages -->
    <template x-for="msg in messages" :key="msg.text">
        <div :class="'alert alert-' + msg.level" x-text="msg.text"></div>
    </template>
</div>
```

## Customizing CRUD Methods

Override any method for custom behavior:

```python
@register_component
class ProductList(CrudNitroComponent[ProductListState]):
    model = Product

    def create_item(self):
        """Custom create with slug generation."""
        if not self.require_auth():
            return

        # Generate slug from title
        slug = slugify(self.state.create_buffer.name)

        try:
            product = self.model.objects.create(
                **self.state.create_buffer.dict(),
                slug=slug,
                owner=self.current_user
            )
            self.refresh()
            self.success(f"Created {product.name}")
        except IntegrityError:
            self.error("Product with this name already exists")

    def delete_item(self, id: int):
        """Soft delete instead of hard delete."""
        try:
            product = self.model.objects.get(id=id)

            # Check permission
            if product.owner != self.current_user:
                self.error("Permission denied")
                return

            # Soft delete
            product.is_deleted = True
            product.deleted_at = timezone.now()
            product.save()

            self.refresh()
            self.success("Product archived")
        except self.model.DoesNotExist:
            self.error("Product not found")
```

## Security Best Practices

### 1. Filter by Owner

```python
def get_initial_state(self, **kwargs):
    # ✅ Only show user's own items
    items = self.model.objects.filter(owner=self.current_user)
    return MyListState(items=[...])

def delete_item(self, id: int):
    # ✅ Check ownership before delete
    obj = self.model.objects.get(id=id)
    if obj.owner != self.current_user:
        self.error("Permission denied")
        return
    obj.delete()
```

### 2. Validate Input

```python
def create_item(self):
    # ✅ Server-side validation
    if len(self.state.create_buffer.title) > 200:
        self.error("Title too long")
        return

    if not self.state.create_buffer.title.strip():
        self.error("Title required")
        return

    # Create item...
```

### 3. Use Permissions

```python
def delete_item(self, id: int):
    # ✅ Check permission
    if not self.request.user.has_perm('myapp.delete_item'):
        self.error("Permission denied")
        return

    # Delete...
```

## Common Patterns

### Filtering

```python
class ProductListState(BaseModel):
    items: list[ProductSchema] = []
    filter_active: bool = True
    # ... CRUD buffers ...

@register_component
class ProductList(CrudNitroComponent[ProductListState]):
    def refresh(self):
        qs = self.model.objects.all()

        # Apply filter
        if self.state.filter_active:
            qs = qs.filter(is_active=True)

        self.state.items = [
            ProductSchema.model_validate(p) for p in qs
        ]

    def toggle_filter(self):
        self.state.filter_active = not self.state.filter_active
        self.refresh()
```

### Sorting

```python
class ProductListState(BaseModel):
    items: list[ProductSchema] = []
    sort_by: str = "name"
    # ... CRUD buffers ...

@register_component
class ProductList(CrudNitroComponent[ProductListState]):
    def refresh(self):
        items = self.model.objects.all().order_by(self.state.sort_by)
        self.state.items = [
            ProductSchema.model_validate(p) for p in items
        ]

    def set_sort(self, field: str):
        self.state.sort_by = field
        self.refresh()
```

## See Also

- [BaseListComponent](base-list-component.md) - Adds pagination, search, filters
- [ModelNitroComponent](model-nitro-component.md) - Base for model components
- [OwnershipMixin](../security/ownership-mixin.md) - Filter by ownership
- [State Management](../core-concepts/state-management.md) - Managing state
