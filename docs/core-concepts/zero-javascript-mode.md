# Zero JavaScript Mode

Django Nitro's **Zero JavaScript Mode** is a set of template tags that completely hide Alpine.js syntax, allowing Django developers to build reactive UIs without writing any JavaScript.

## The Problem

**Traditional Nitro (Alpine Mode):**
```html
<input
    x-model="email"
    @input.debounce.300ms="call('validate_email')"
    :class="{'border-red-500': errors.email}"
>

<button @click="call('submit')" :disabled="isLoading">
    <span x-show="!isLoading">Send</span>
    <span x-show="isLoading">Sending...</span>
</button>
```

**Issues:**
- ❌ Requires learning Alpine.js syntax
- ❌ Not truly "Zero JavaScript"
- ❌ Intimidating for Django-only developers

## The Solution: Template Tags

**Zero JavaScript Mode:**
```html
{% load nitro_tags %}

<input {% nitro_model 'email' debounce='300ms' on_change='validate_email' %}>

<button {% nitro_action 'submit' %}>
    <span {% nitro_show '!isLoading' %}>Send</span>
    <span {% nitro_show 'isLoading' %}>Sending...</span>
</button>
```

**Benefits:**
- ✅ Pure Django template syntax
- ✅ No Alpine knowledge required
- ✅ Truly "Zero JavaScript"
- ✅ Familiar to Django developers

---

## Available Template Tags

### {% nitro_model %}

Auto-sync bidirectional binding (equivalent to Livewire's `wire:model`).

**Basic Usage:**
```html
<input {% nitro_model 'email' %}>
```

**With Debounce:**
```html
<input {% nitro_model 'search' debounce='300ms' %}>
```

**Lazy (sync on blur):**
```html
<input {% nitro_model 'password' lazy=True %}>
```

**With Callback:**
```html
<input {% nitro_model 'email' on_change='validate_email' %}>
```

**What it generates:**
```html
<input
    x-model="email"
    @input="call('_sync_field', {field: 'email', value: email})"
    :class="{'border-red-500': errors.email}"
>
```

**Features:**
- ✅ Auto-syncs field to state
- ✅ Automatic error styling
- ✅ Optional debouncing
- ✅ Optional callback after sync

---

### {% nitro_action %}

Action button (equivalent to Livewire's `wire:click`).

**Basic Usage:**
```html
<button {% nitro_action 'submit' %}>Send</button>
```

**With Parameters:**
```html
<button {% nitro_action 'delete' id='item.id' %}>Delete</button>
<button {% nitro_action 'update' id='task.id' status='completed' %}>
    Mark Complete
</button>
```

**What it generates:**
```html
<button
    @click="call('delete', {id: item.id})"
    :disabled="isLoading"
>Delete</button>
```

**Features:**
- ✅ Calls component action
- ✅ Auto-disabled during loading
- ✅ Supports multiple parameters

---

### {% nitro_show %}

Conditional visibility (wrapper for `x-show`).

**Usage:**
```html
<div {% nitro_show 'isLoading' %}>Loading...</div>
<div {% nitro_show '!isLoading' %}>Content</div>
<div {% nitro_show 'count > 0' %}>Has items</div>
<div {% nitro_show 'errors.email' %}>
    <span class="error">Invalid email</span>
</div>
```

**What it generates:**
```html
<div x-show="isLoading">Loading...</div>
```

**Use for:**
- Loading indicators
- Conditional messages
- Error displays

---

### {% nitro_class %}

Conditional CSS classes (wrapper for `:class`).

**Usage:**
```html
<div {% nitro_class active='isActive' disabled='isLoading' %}>
    Tab content
</div>

<div {% nitro_class 'bg-red-500'='hasError' 'bg-green-500'='isSuccess' %}>
    Status indicator
</div>
```

**What it generates:**
```html
<div :class="{'active': isActive, 'disabled': isLoading}">
```

**Use for:**
- Active/inactive states
- Error/success styling
- Dynamic theming

---

### {% nitro_attr %}

Dynamic HTML attributes (wrapper for Alpine `:attr` binding).

**Usage:**
```html
<!-- Dynamic href -->
<a {% nitro_attr href='selectedUrl' %}>Go to link</a>

<!-- Dynamic src -->
<img {% nitro_attr src='imageUrl' alt='imageAlt' %}>

<!-- Dynamic data attributes -->
<div {% nitro_attr 'data-id'='itemId' 'data-status'='currentStatus' %}>
    Content
</div>

<!-- Multiple attributes -->
<input {% nitro_attr placeholder='placeholderText' maxlength='maxLen' %}>
```

**What it generates:**
```html
<a :href="selectedUrl">Go to link</a>
<img :src="imageUrl" :alt="imageAlt">
```

**Use for:**
- Dynamic links and URLs
- Dynamic image sources
- Data attributes that change with state
- Any attribute that needs to be reactive

---

### {% nitro_if %}

Conditional rendering (wrapper for `x-if` with `<template>`).

**Usage:**
```html
{% nitro_if 'isAdmin' %}
    <button {% nitro_action 'delete_all' %}>Delete All</button>
{% end_nitro_if %}

{% nitro_if 'items.length > 0' %}
    <ul>
        <!-- List items -->
    </ul>
{% end_nitro_if %}

{% nitro_if 'user.isVerified' %}
    <span class="badge">Verified</span>
{% end_nitro_if %}
```

**What it generates:**
```html
<template x-if="isAdmin">
    <button @click="call('delete_all')" :disabled="isLoading">Delete All</button>
</template>
```

**Difference from `nitro_show`:**
- `nitro_show` hides the element with CSS (`display: none`) but keeps it in the DOM
- `nitro_if` completely removes the element from the DOM when condition is false

**Use for:**
- Elements that should not exist in DOM when hidden
- Conditional form sections
- Admin-only features
- Performance optimization (removes elements instead of hiding)

---

### {% nitro_disabled %}

Dynamic disabled state for form elements.

**Usage:**
```html
<!-- Disable during loading -->
<button {% nitro_disabled 'isLoading' %}>Submit</button>

<!-- Disable based on validation -->
<button {% nitro_disabled '!isValid' %}>Continue</button>

<!-- Complex conditions -->
<input {% nitro_disabled 'isLocked || !canEdit' %}>

<!-- Disable submit until form is complete -->
<button
    {% nitro_action 'submit' %}
    {% nitro_disabled '!name || !email || !message' %}
>
    Send Message
</button>
```

**What it generates:**
```html
<button :disabled="isLoading">Submit</button>
<button :disabled="!isValid">Continue</button>
```

**Use for:**
- Preventing double-clicks during loading
- Form validation (disable submit until valid)
- Read-only mode based on permissions
- Conditional form element states

---

### {% nitro_file %}

File upload handling with automatic state management.

**Usage:**
```html
<!-- Basic file upload -->
<input type="file" {% nitro_file 'document' %}>

<!-- Multiple files -->
<input type="file" {% nitro_file 'images' multiple=True %}>

<!-- With accepted types -->
<input type="file" {% nitro_file 'avatar' accept='image/*' %}>

<!-- With callback after upload -->
<input type="file" {% nitro_file 'attachment' on_change='process_file' %}>
```

**What it generates:**
```html
<input
    type="file"
    @change="handleFileUpload('document', $event)"
>
```

**Python Component:**
```python
from nitro import NitroComponent, register_component
from pydantic import BaseModel
from typing import Optional


class FileUploadState(BaseModel):
    document: Optional[dict] = None  # Contains file info after upload
    document_name: str = ""
    document_size: int = 0


@register_component
class FileUpload(NitroComponent[FileUploadState]):
    template_name = "components/file_upload.html"
    state_class = FileUploadState

    def get_initial_state(self, **kwargs):
        return FileUploadState()

    def process_file(self):
        """Called after file is uploaded."""
        if self.state.document:
            # File is available as base64 or can be saved
            self.success(f"Uploaded: {self.state.document_name}")
```

**Complete Example:**
```html
{% load nitro_tags %}

<div class="file-upload">
    <label for="document">Upload Document</label>
    <input
        id="document"
        type="file"
        {% nitro_file 'document' accept='.pdf,.doc,.docx' on_change='validate_document' %}
    >

    <!-- Show file info after upload -->
    <div {% nitro_show 'document_name' %}>
        <p>File: <span x-text="document_name"></span></p>
        <p>Size: <span x-text="document_size"></span> bytes</p>
        <button {% nitro_action 'clear_file' %}>Remove</button>
    </div>

    <!-- Upload button -->
    <button
        {% nitro_action 'submit_document' %}
        {% nitro_disabled '!document' %}
    >
        Submit Document
    </button>
</div>
```

**Use for:**
- Document uploads
- Image uploads with preview
- Multi-file uploads
- File validation before submission

---

## Nested Fields (Dot Notation)

Django Nitro supports nested fields using dot notation, allowing you to work with complex state structures.

### Basic Nested Fields

```python
# myapp/components/user_profile.py
from pydantic import BaseModel
from nitro import NitroComponent, register_component


class Address(BaseModel):
    street: str = ""
    city: str = ""
    country: str = ""


class UserSettings(BaseModel):
    theme: str = "light"
    notifications: bool = True
    language: str = "en"


class UserProfileState(BaseModel):
    name: str = ""
    email: str = ""
    address: Address = Address()
    settings: UserSettings = UserSettings()


@register_component
class UserProfile(NitroComponent[UserProfileState]):
    template_name = "components/user_profile.html"
    state_class = UserProfileState

    def get_initial_state(self, **kwargs):
        return UserProfileState()

    def save_profile(self):
        # Access nested fields directly
        city = self.state.address.city
        theme = self.state.settings.theme
        # Save logic...
        self.success("Profile saved!")
```

### Template with Nested Fields

```html
{% load nitro_tags %}

<div class="user-profile">
    <h2>User Profile</h2>

    <!-- Basic fields -->
    <div class="form-group">
        <label>Name</label>
        <input {% nitro_model 'name' %}>
    </div>

    <div class="form-group">
        <label>Email</label>
        <input {% nitro_model 'email' %}>
    </div>

    <!-- Nested address fields using dot notation -->
    <fieldset>
        <legend>Address</legend>

        <div class="form-group">
            <label>Street</label>
            <input {% nitro_model 'address.street' %}>
        </div>

        <div class="form-group">
            <label>City</label>
            <input {% nitro_model 'address.city' %}>
        </div>

        <div class="form-group">
            <label>Country</label>
            <input {% nitro_model 'address.country' %}>
        </div>
    </fieldset>

    <!-- Nested settings fields -->
    <fieldset>
        <legend>Settings</legend>

        <div class="form-group">
            <label>Theme</label>
            <select {% nitro_model 'settings.theme' %}>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto</option>
            </select>
        </div>

        <div class="form-group">
            <label>
                <input type="checkbox" {% nitro_model 'settings.notifications' %}>
                Enable Notifications
            </label>
        </div>

        <div class="form-group">
            <label>Language</label>
            <select {% nitro_model 'settings.language' %}>
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
            </select>
        </div>
    </fieldset>

    <button {% nitro_action 'save_profile' %}>Save Profile</button>
</div>
```

### Nested Fields in Conditions

You can also use dot notation in `nitro_show`, `nitro_if`, and `nitro_class`:

```html
<!-- Show based on nested field -->
<div {% nitro_show 'settings.notifications' %}>
    Notifications are enabled
</div>

<!-- Conditional rendering -->
{% nitro_if 'address.country' %}
    <p>Country: <span x-text="address.country"></span></p>
{% end_nitro_if %}

<!-- Conditional classes -->
<div {% nitro_class 'dark-mode'='settings.theme === "dark"' %}>
    Content
</div>

<!-- Error display for nested fields -->
<span {% nitro_show 'errors["address.city"]' %} class="error">
    <span x-text='errors["address.city"]'></span>
</span>
```

### Deeply Nested Structures

```python
class CompanySettings(BaseModel):
    billing_email: str = ""
    tax_id: str = ""


class Company(BaseModel):
    name: str = ""
    settings: CompanySettings = CompanySettings()


class ProfileState(BaseModel):
    company: Company = Company()
```

```html
<!-- Three levels deep -->
<input {% nitro_model 'company.settings.billing_email' %}>
<input {% nitro_model 'company.settings.tax_id' %}>
```

---

## Complete Example: Contact Form

### Python Component

```python
# myapp/components/contact_form.py
from pydantic import BaseModel, EmailStr
from nitro import NitroComponent, register_component


class ContactFormState(BaseModel):
    name: str = ""
    email: str = ""
    message: str = ""
    submitted: bool = False


@register_component
class ContactForm(NitroComponent[ContactFormState]):
    template_name = "components/contact_form.html"
    state_class = ContactFormState

    def get_initial_state(self, **kwargs):
        return ContactFormState()

    def validate_email(self):
        """Called automatically by nitro_model on_change."""
        if self.state.email and '@' not in self.state.email:
            self.add_error('email', 'Invalid email format')

    def submit(self):
        """Submit the form."""
        # Validation
        if not self.state.name:
            self.add_error('name', 'Name is required')
            return

        if not self.state.email:
            self.add_error('email', 'Email is required')
            return

        if not self.state.message:
            self.add_error('message', 'Message is required')
            return

        # Send email
        send_contact_email(
            name=self.state.name,
            email=self.state.email,
            message=self.state.message
        )

        # Mark as submitted
        self.state.submitted = True
        self.success("Message sent! We'll get back to you soon.")
```

### Template (Zero JS Mode)

```html
{% load nitro_tags %}

<div class="contact-form">
    <!-- Show form until submitted -->
    <div {% nitro_show '!submitted' %}>
        <h2>Contact Us</h2>

        <!-- Name field -->
        <div class="form-group">
            <label for="name">Name</label>
            <input
                id="name"
                type="text"
                {% nitro_model 'name' %}
                placeholder="Your name"
            >
            <span
                {% nitro_show 'errors.name' %}
                class="error"
                x-text="errors.name"
            ></span>
        </div>

        <!-- Email field with validation -->
        <div class="form-group">
            <label for="email">Email</label>
            <input
                id="email"
                type="email"
                {% nitro_model 'email' debounce='500ms' on_change='validate_email' %}
                placeholder="your@email.com"
            >
            <span
                {% nitro_show 'errors.email' %}
                class="error"
                x-text="errors.email"
            ></span>
        </div>

        <!-- Message field -->
        <div class="form-group">
            <label for="message">Message</label>
            <textarea
                id="message"
                {% nitro_model 'message' %}
                rows="5"
                placeholder="Your message..."
            ></textarea>
            <span
                {% nitro_show 'errors.message' %}
                class="error"
                x-text="errors.message"
            ></span>
        </div>

        <!-- Submit button -->
        <button
            {% nitro_action 'submit' %}
            class="btn btn-primary"
        >
            <span {% nitro_show '!isLoading' %}>Send Message</span>
            <span {% nitro_show 'isLoading' %}>Sending...</span>
        </button>
    </div>

    <!-- Success message -->
    <div {% nitro_show 'submitted' %} class="success-message">
        <h3>Thank You!</h3>
        <p>We've received your message and will respond soon.</p>
    </div>
</div>
```

**Result:** A fully functional contact form with validation, zero JavaScript written!

---

## Mode Comparison

### Zero JS Mode (Beginner-Friendly)

```html
{% load nitro_tags %}

<input {% nitro_model 'email' debounce='300ms' %}>
<button {% nitro_action 'submit' %}>Send</button>
<div {% nitro_show 'isLoading' %}>Loading...</div>
```

**Pros:**
- ✅ No Alpine knowledge required
- ✅ Familiar Django syntax
- ✅ Less verbose
- ✅ Automatic error styling

**Cons:**
- ⚠️ Less flexible (limited to provided tags)
- ⚠️ Can't do complex Alpine logic
- ⚠️ One more layer of abstraction

**Best for:**
- Django developers new to reactive UIs
- Simple forms and CRUD interfaces
- Teams that want to avoid JavaScript

---

### Alpine Mode (Advanced)

```html
<input
    x-model="email"
    @input.debounce.300ms="call('sync_field', {field: 'email', value: email})"
>
<button @click="call('submit')" :disabled="isLoading">Send</button>
<div x-show="isLoading">Loading...</div>
```

**Pros:**
- ✅ Full Alpine flexibility
- ✅ Can use all Alpine features
- ✅ More control

**Cons:**
- ❌ Requires Alpine knowledge
- ❌ More verbose
- ❌ Manual error handling

**Best for:**
- Developers familiar with Alpine
- Complex UI interactions
- Custom animations/transitions

---

## When to Use Each Mode

### Use Zero JS Mode When:
- ✅ Building simple forms
- ✅ Standard CRUD interfaces
- ✅ Team doesn't know Alpine
- ✅ Want to minimize JavaScript

**Example:** Contact form, user profile editor, task list

### Use Alpine Mode When:
- ✅ Need complex client-side logic
- ✅ Custom animations/transitions
- ✅ Advanced Alpine features (x-transition, x-ref, etc.)
- ✅ Already familiar with Alpine

**Example:** Drag-and-drop interface, complex wizard, real-time chat

### Mix Both Modes

You can combine both modes in the same component:

```html
{% load nitro_tags %}

<!-- Zero JS for simple fields -->
<input {% nitro_model 'email' %}>
<button {% nitro_action 'submit' %}>Send</button>

<!-- Alpine for complex UI -->
<div x-data="{expanded: false}">
    <button @click="expanded = !expanded">
        <span x-text="expanded ? 'Hide' : 'Show'"></span> Details
    </button>

    <div x-show="expanded" x-transition>
        <!-- Complex content with Alpine features -->
    </div>
</div>
```

---

## Migration Guide

### From Alpine Mode to Zero JS Mode

**Before:**
```html
<input x-model="email" @input.debounce.300ms="call('validate')">
<button @click="call('submit')" :disabled="isLoading">Send</button>
<div x-show="isLoading">Loading...</div>
```

**After:**
```html
{% load nitro_tags %}

<input {% nitro_model 'email' debounce='300ms' on_change='validate' %}>
<button {% nitro_action 'submit' %}>Send</button>
<div {% nitro_show 'isLoading' %}>Loading...</div>
```

**Steps:**
1. Add `{% load nitro_tags %}` at top
2. Replace `x-model` → `{% nitro_model %}`
3. Replace `@click="call(...)"` → `{% nitro_action %}`
4. Replace `x-show` → `{% nitro_show %}`
5. Replace `:class` → `{% nitro_class %}`

---

## Best Practices

### 1. Load Tags Once at Top

```html
<!-- ✅ Good -->
{% load nitro_tags %}

<div>
    <input {% nitro_model 'email' %}>
    <button {% nitro_action 'submit' %}>Send</button>
</div>

<!-- ❌ Bad -->
<div>
    {% load nitro_tags %}
    <input {% nitro_model 'email' %}>
    {% load nitro_tags %}  <!-- Don't reload -->
    <button {% nitro_action 'submit' %}>Send</button>
</div>
```

### 2. Use Descriptive Action Names

```python
# ✅ Good
def validate_email(self):
    pass

def submit_form(self):
    pass

# ❌ Bad
def validate(self):  # Validate what?
    pass

def do_it(self):  # Do what?
    pass
```

### 3. Add Error Displays

```html
<!-- ✅ Good - Show validation errors -->
<input {% nitro_model 'email' %}>
<span {% nitro_show 'errors.email' %} class="error">
    <span x-text="errors.email"></span>
</span>

<!-- ❌ Bad - Errors silently ignored -->
<input {% nitro_model 'email' %}>
```

### 4. Use Debounce for Search

```html
<!-- ✅ Good - Reduces API calls -->
<input {% nitro_model 'search' debounce='300ms' %}>

<!-- ❌ Bad - Calls on every keystroke -->
<input {% nitro_model 'search' %}>
```

### 5. Use Lazy for Passwords

```html
<!-- ✅ Good - Only sync on blur -->
<input type="password" {% nitro_model 'password' lazy=True %}>

<!-- ❌ Bad - Syncs on every character (security/performance) -->
<input type="password" {% nitro_model 'password' %}>
```

---

## Limitations

### 1. No Array Indexing

```html
<!-- ❌ Not supported -->
<input {% nitro_model 'items.0.name' %}>

<!-- ✅ Use x-for with separate component -->
```

### 2. Limited to Basic Use Cases

For complex logic, use Alpine directly:

```html
<!-- ❌ Can't do this with template tags -->
<div x-data="{count: 0, doubled: $watch('count', val => val * 2)}">
    Count: <span x-text="count"></span>
    Doubled: <span x-text="doubled"></span>
</div>

<!-- ✅ Use Alpine for complex reactivity -->
```

---

## True Zero-JS Template Tags (v0.7.0)

Version 0.7.0 introduces **truly Zero-JavaScript** template tags. While previous tags like `nitro_show` still required understanding Alpine expressions (`'item.status === "active"'`), these new tags define ALL logic in Python kwargs.

### The Philosophy

**Before v0.7.0 (required JS knowledge):**
```django
{# Developer had to know JS ternary syntax #}
<span {% nitro_bind "item.status === 'active' ? 'Active' : 'Inactive'" %}></span>
<div {% nitro_class_map "{'bg-green-100': item.status === 'active'}" %}></div>
```

**After v0.7.0 (Pure Python):**
```django
{# All logic in kwargs - no JS knowledge needed #}
{% nitro_switch 'item.status' active='Active' expired='Expired' default='Draft' %}
<div {% nitro_css 'item.status' active='bg-green-100' expired='bg-red-100' %}></div>
```

---

### {% nitro_switch %} - Conditional Text

Display different text based on a field's value:

```django
{% load nitro_tags %}

{# Basic usage #}
{% nitro_switch 'item.status' active='Active' expired='Expired' default='Draft' %}

{# Multiple values #}
{% nitro_switch 'priority' high='🔴 High' medium='🟡 Medium' low='🟢 Low' %}

{# In a table #}
<td>{% nitro_switch 'user.role' admin='Administrator' staff='Staff' default='User' %}</td>
```

---

### {% nitro_css %} - Conditional CSS Classes

Apply different CSS classes based on a field's value:

```django
{# Badge styling #}
<span {% nitro_css 'item.status' active='bg-green-100 text-green-700' expired='bg-red-100 text-red-700' %}>
    {% nitro_switch 'item.status' active='Active' expired='Expired' %}
</span>

{# Row highlighting #}
<tr {% nitro_css 'item.priority' high='bg-red-50' medium='bg-yellow-50' low='bg-blue-50' %}>
```

---

### {% nitro_badge %} - Combined Text + Styling

Render complete badges with text AND classes in one tag:

```django
{% nitro_badge 'item.status'
   active='Active:bg-green-100 text-green-700'
   expired='Expired:bg-red-100 text-red-700'
   pending='Pending:bg-yellow-100 text-yellow-700'
   default='Draft:bg-gray-100'
   base_class='px-2 py-1 rounded-full text-sm font-medium' %}
```

**Format:** `'display_text:css_classes'`

---

### {% nitro_visible %} / {% nitro_hidden %} - Boolean Visibility

Show/hide elements based on boolean fields (no JS expressions needed):

```django
{# Show when active #}
<div {% nitro_visible 'item.is_active' %}>Visible when active</div>

{# Show when NOT deleted (negate) #}
<div {% nitro_visible 'item.is_deleted' negate=True %}>Hidden when deleted</div>

{# Hide when loading #}
<div {% nitro_hidden 'isLoading' %}>Content hidden during load</div>
```

---

### {% nitro_plural %} / {% nitro_count %} - Pluralization

Handle singular/plural automatically:

```django
{# Basic plural #}
{% nitro_plural 'count' singular='item' plural='items' zero='No items' %}

{# Count with label: "5 properties", "1 property", "No properties" #}
{% nitro_count 'items.length' singular='property' plural='properties' zero='No properties' %}

{# With number formatting #}
{% nitro_count 'total' singular='result' plural='results' %}
```

---

### {% nitro_format %} / {% nitro_date %} - Value Formatting

Format values with proper display:

```django
{# Currency formatting #}
{% nitro_format 'item.price' format_type='currency' prefix='$' %}

{# With empty state #}
{% nitro_format 'item.value' empty='N/A' %}

{# Date formatting #}
{% nitro_date 'item.created_at' empty='No date' %}
```

---

### Complete Example: Property List with Zero-JS

```django
{% load nitro_tags %}

<table class="w-full">
    <thead>
        <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Price</th>
            <th>Tenants</th>
        </tr>
    </thead>
    <tbody>
        {% nitro_for 'items' as 'item' %}
            <tr {% nitro_css 'item.status' active='bg-green-50' expired='bg-red-50' %}>
                <td>{% nitro_text 'item.name' %}</td>
                <td>
                    {% nitro_badge 'item.status'
                       active='Active:bg-green-100 text-green-700'
                       expired='Expired:bg-red-100 text-red-700'
                       base_class='px-2 py-1 rounded text-xs' %}
                </td>
                <td>{% nitro_format 'item.price' format_type='currency' prefix='$' %}</td>
                <td>{% nitro_count 'item.tenant_count' singular='tenant' plural='tenants' %}</td>
            </tr>
        {% end_nitro_for %}
    </tbody>
</table>

{# Footer with total #}
<div class="mt-4 text-sm text-gray-500">
    {% nitro_count 'total_count' singular='property' plural='properties' zero='No properties' %}
</div>
```

**Notice:** No JavaScript expressions anywhere! All conditional logic is defined in Python kwargs.

---

## Troubleshooting

### "Field does not exist" Error

```
ValueError: Field 'emial' does not exist in ContactFormState.
Available fields: email, name, message
```

**Solution:** Fix the typo in the template:
```html
<!-- ❌ Wrong -->
<input {% nitro_model 'emial' %}>

<!-- ✅ Correct -->
<input {% nitro_model 'email' %}>
```

### Template Tag Not Found

```
TemplateSyntaxError: Invalid block tag: 'nitro_model'
```

**Solution:** Load the template tags:
```html
{% load nitro_tags %}  <!-- Add this at top -->

<input {% nitro_model 'email' %}>
```

### Auto-Sync Not Working

**Check:**
1. ✅ Field exists in state schema
2. ✅ Template tags loaded (`{% load nitro_tags %}`)
3. ✅ nitro.js is included in base template
4. ✅ Alpine.js is included

---

## See Also

- [Template Tags Reference](template-tags.md) - SEO tags (nitro_for, nitro_text)
- [API Reference](../api-reference.md) - Complete API documentation
- [Counter Example](../examples/counter.md) - Simple example
- [Property Manager Example](../examples/property-manager.md) - Advanced example
- [Getting Started](../getting-started/quick-start.md) - Quickstart guide

---

**Added in:** v0.4.0
**Status:** Stable
