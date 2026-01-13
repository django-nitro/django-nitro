# Form Field Template Tags (v0.6.0)

Django Nitro includes pre-built template tags for common form fields with automatic error handling, validation styling, and Alpine.js integration.

## Overview

All form field tags provide:
- **Automatic Alpine.js binding** - No manual `x-model` needed
- **Built-in error display** - Shows Pydantic validation errors
- **Bootstrap styling** - Uses Bootstrap 5 classes out of the box
- **Optional chaining support** - Works with nested fields and edit buffers
- **Type safety** - Integrates with Pydantic validation

## Available Tags

### {% nitro_input %}

Renders an input field with automatic error display.

**Basic Usage:**

```html
{% load nitro_tags %}

<!-- Text input -->
{% nitro_input 'name' %}

<!-- Email input -->
{% nitro_input 'email' type='email' placeholder='user@example.com' %}

<!-- Number input with validation -->
{% nitro_input 'age' type='number' min='18' max='100' %}

<!-- Date input -->
{% nitro_input 'birth_date' type='date' %}

<!-- Phone input -->
{% nitro_input 'phone' type='tel' placeholder='555-1234' %}
```

**Parameters:**
- `field` (required) - Field name or path (supports nested fields like `edit_buffer.name`)
- `type` (optional) - Input type (default: `'text'`)
- `placeholder` (optional) - Placeholder text
- `class` (optional) - Additional CSS classes
- `disabled` (optional) - Disable input
- `**attrs` - Any other HTML attributes (e.g., `min`, `max`, `step`, `pattern`)

**Supported Input Types:**
`text`, `email`, `password`, `number`, `tel`, `url`, `date`, `time`, `datetime-local`, `search`

**Generated HTML:**

```html
<div class="mb-3">
  <input
    type="text"
    x-model="name"
    class="form-control"
    :class="{'is-invalid': errors?.name}"
  >
  <div x-show="errors?.name" class="invalid-feedback" x-text="errors?.name"></div>
</div>
```

---

### {% nitro_select %}

Renders a select dropdown with choices and error handling.

**Basic Usage:**

```html
{% load nitro_tags %}

<!-- Basic select -->
{% nitro_select 'status' choices=status_choices %}

<!-- With custom class -->
{% nitro_select 'category' choices=categories class='form-select-lg' %}

<!-- Disabled select -->
{% nitro_select 'country' choices=countries disabled=True %}

<!-- Edit buffer support -->
{% nitro_select 'edit_buffer.priority' choices=priority_choices %}
```

**Component Setup:**

```python
from pydantic import BaseModel, Field
from nitro import NitroComponent, register_component

class FormState(BaseModel):
    status: str = ""
    status_choices: list[dict] = Field(default_factory=lambda: [
        {'value': 'draft', 'label': 'Draft'},
        {'value': 'published', 'label': 'Published'},
        {'value': 'archived', 'label': 'Archived'},
    ])

@register_component
class MyForm(NitroComponent[FormState]):
    template_name = "my_form.html"

    def get_initial_state(self):
        return FormState()
```

**Parameters:**
- `field` (required) - Field name or path
- `choices` (required) - List of dicts with `value` and `label` keys
- `class` (optional) - Additional CSS classes
- `disabled` (optional) - Disable select
- `**attrs` - Any other HTML attributes

**Choices Format:**
```python
choices = [
    {'value': 'option1', 'label': 'Option 1'},
    {'value': 'option2', 'label': 'Option 2'},
]
```

**Generated HTML:**

```html
<div class="mb-3">
  <select x-model="status" class="form-select" :class="{'is-invalid': errors?.status}">
    <option value="">---------</option>
    <option value="draft">Draft</option>
    <option value="published">Published</option>
    <option value="archived">Archived</option>
  </select>
  <div x-show="errors?.status" class="invalid-feedback" x-text="errors?.status"></div>
</div>
```

---

### {% nitro_textarea %}

Renders a textarea with error handling.

**Basic Usage:**

```html
{% load nitro_tags %}

<!-- Basic textarea -->
{% nitro_textarea 'description' %}

<!-- With rows and placeholder -->
{% nitro_textarea 'notes' rows='5' placeholder='Enter notes...' %}

<!-- With custom class -->
{% nitro_textarea 'bio' class='form-control-lg' rows='10' %}

<!-- Disabled textarea -->
{% nitro_textarea 'system_log' disabled=True %}

<!-- Edit buffer support -->
{% nitro_textarea 'edit_buffer.description' rows='8' %}
```

**Parameters:**
- `field` (required) - Field name or path
- `rows` (optional) - Number of visible rows (default: `3`)
- `placeholder` (optional) - Placeholder text
- `class` (optional) - Additional CSS classes
- `disabled` (optional) - Disable textarea
- `**attrs` - Any other HTML attributes

**Generated HTML:**

```html
<div class="mb-3">
  <textarea
    x-model="description"
    class="form-control"
    :class="{'is-invalid': errors?.description}"
    rows="3"
  ></textarea>
  <div x-show="errors?.description" class="invalid-feedback" x-text="errors?.description"></div>
</div>
```

---

### {% nitro_checkbox %}

Renders a checkbox with label and error handling.

**Basic Usage:**

```html
{% load nitro_tags %}

<!-- Basic checkbox -->
{% nitro_checkbox 'is_active' label='Active' %}

<!-- Terms acceptance -->
{% nitro_checkbox 'terms_accepted' label='I agree to the terms and conditions' %}

<!-- With custom class -->
{% nitro_checkbox 'newsletter' label='Subscribe to newsletter' class='form-check-lg' %}

<!-- Disabled checkbox -->
{% nitro_checkbox 'verified' label='Verified' disabled=True %}

<!-- Edit buffer support -->
{% nitro_checkbox 'edit_buffer.is_featured' label='Featured' %}
```

**Parameters:**
- `field` (required) - Field name or path
- `label` (required) - Label text displayed next to checkbox
- `class` (optional) - Additional CSS classes
- `disabled` (optional) - Disable checkbox
- `**attrs` - Any other HTML attributes

**Generated HTML:**

```html
<div class="form-check mb-3">
  <input
    type="checkbox"
    x-model="is_active"
    class="form-check-input"
    :class="{'is-invalid': errors?.is_active}"
    id="id_is_active"
  >
  <label class="form-check-label" for="id_is_active">
    Active
  </label>
  <div x-show="errors?.is_active" class="invalid-feedback" x-text="errors?.is_active"></div>
</div>
```

---

## Complete Example

### Contact Form Component

```python
# components/contact_form.py
from pydantic import BaseModel, EmailStr, Field
from nitro import NitroComponent, register_component

class ContactFormState(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    subject: str = ""
    message: str = ""
    terms_accepted: bool = False

    subject_choices: list[dict] = Field(default_factory=lambda: [
        {'value': 'general', 'label': 'General Inquiry'},
        {'value': 'support', 'label': 'Technical Support'},
        {'value': 'sales', 'label': 'Sales Question'},
    ])

@register_component
class ContactForm(NitroComponent[ContactFormState]):
    template_name = "components/contact_form.html"

    def get_initial_state(self):
        return ContactFormState()

    def submit_form(self):
        # Validation
        if not self.state.full_name or len(self.state.full_name) < 2:
            self.error("Name must be at least 2 characters")
            return

        if not self.state.email or '@' not in self.state.email:
            self.error("Please enter a valid email")
            return

        if not self.state.terms_accepted:
            self.error("You must accept the terms")
            return

        # Process form
        self.success(f"Thank you, {self.state.full_name}!")

        # Reset
        self.state.full_name = ""
        self.state.email = ""
        self.state.phone = ""
        self.state.subject = ""
        self.state.message = ""
        self.state.terms_accepted = False
```

### Template

```html
<!-- templates/components/contact_form.html -->
{% load nitro_tags %}

<div class="card">
  <div class="card-body">
    <h2>Contact Us</h2>

    <!-- Messages -->
    <template x-for="(msg, index) in messages" :key="index">
      <div
        x-show="msg"
        class="alert"
        :class="{
          'alert-success': msg.level === 'success',
          'alert-danger': msg.level === 'error'
        }"
      >
        <span x-text="msg.text"></span>
      </div>
    </template>

    <form @submit.prevent="call('submit_form')">
      <div class="row">
        <div class="col-md-6">
          <label class="form-label">Full Name *</label>
          {% nitro_input 'full_name' placeholder='John Doe' %}
        </div>

        <div class="col-md-6">
          <label class="form-label">Email *</label>
          {% nitro_input 'email' type='email' placeholder='john@example.com' %}
        </div>
      </div>

      <div class="row">
        <div class="col-md-6">
          <label class="form-label">Phone</label>
          {% nitro_input 'phone' type='tel' placeholder='555-1234' %}
        </div>

        <div class="col-md-6">
          <label class="form-label">Subject *</label>
          {% nitro_select 'subject' choices=subject_choices %}
        </div>
      </div>

      <div>
        <label class="form-label">Message *</label>
        {% nitro_textarea 'message' rows='6' placeholder='Enter your message...' %}
      </div>

      <div>
        {% nitro_checkbox 'terms_accepted' label='I agree to the terms and conditions' %}
      </div>

      <button type="submit" class="btn btn-primary" :disabled="isLoading">
        <span x-show="!isLoading">Submit</span>
        <span x-show="isLoading">Submitting...</span>
      </button>
    </form>
  </div>
</div>
```

---

## Edit Buffer Support

All form field tags support edit buffers for CRUD operations:

```html
<!-- In edit mode -->
<template x-if="editing_id === item.id && edit_buffer">
  <div>
    {% nitro_input 'edit_buffer.name' %}
    {% nitro_select 'edit_buffer.status' choices=status_choices %}
    {% nitro_textarea 'edit_buffer.notes' %}
    {% nitro_checkbox 'edit_buffer.is_active' label='Active' %}
  </div>
</template>
```

The tags automatically handle optional chaining for nested fields.

---

## Validation and Errors

Errors from Pydantic validation are automatically displayed:

```python
class UserSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    age: int = Field(ge=18, le=120)

class UserForm(NitroComponent[UserSchema]):
    def save_user(self):
        try:
            # Pydantic validates automatically
            user = User.objects.create(**self.state.dict())
            self.success("User created!")
        except ValidationError as e:
            # Errors displayed under each field automatically
            pass
```

Error messages appear with Bootstrap's `.invalid-feedback` styling.

---

## Customization

### Custom CSS Classes

Add custom classes to any field:

```html
{% nitro_input 'name' class='form-control-lg custom-input' %}
{% nitro_select 'status' choices=choices class='w-50' %}
```

### Custom Attributes

Pass any HTML attribute:

```html
{% nitro_input 'price' type='number' min='0' max='10000' step='0.01' %}
{% nitro_input 'username' pattern='[a-zA-Z0-9_]+' maxlength='20' %}
```

### Disabled State

Disable fields conditionally:

```html
{% nitro_input 'id' disabled=True %}
{% nitro_select 'status' choices=choices disabled=True %}
```

---

## Default Debounce (v0.6.0)

All form field tags use `nitro_model` internally, which now includes a **200ms debounce by default**. This reduces server load by batching rapid user input.

To disable debounce for instant sync:

```html
<!-- In component template, use nitro_model directly -->
<input x-model="field" @input="call('validate_field', {field: $el.value})">
```

---

## See Also

- [API Reference: Template Tags](../api-reference.md#template-tags-v040)
- [SEO Template Tags](template-tags.md)
- [Property Manager Example](../examples/property-manager.md)
- [CRUD Operations](../components/crud-nitro-component.md)
