# Alpine Components

Client-side components for local UI interactions. No data fetching - Alpine is for UI state only.

## Loading in Templates

Components are auto-registered when you include `{% nitro_scripts %}`:

```html
<head>
    {% nitro_scripts %}
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
```

---

## toastManager

Manages toast notification queue.

```html
<div x-data="toastManager()">
    <!-- Toasts render here -->
</div>
```

Usually included via `{% nitro_toast %}`.

**Events:**
```javascript
// Show toast from anywhere
$dispatch('show-toast', { message: 'Guardado', type: 'success' })
```

---

## fileUpload

Drag-and-drop file upload with preview.

```html
<div x-data="fileUpload({
    uploadUrl: '/api/upload/',
    maxFiles: 5,
    maxSize: 10,
    accept: 'image/*,.pdf'
})">
    <div
        @drop.prevent="handleDrop($event)"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        :class="{ 'border-blue-500': isDragging }"
        class="border-2 border-dashed p-8 text-center"
    >
        <p>Arrastra archivos aquí o</p>
        <input type="file" @change="handleFiles($event)" multiple class="hidden" x-ref="input">
        <button @click="$refs.input.click()" type="button">Seleccionar</button>
    </div>

    <!-- Preview -->
    <template x-for="file in files" :key="file.id">
        <div class="flex items-center gap-2 mt-2">
            <span x-text="file.name"></span>
            <span x-text="formatSize(file.size)"></span>
            <button @click="removeFile(file.id)">×</button>
        </div>
    </template>
</div>
```

**Options:**
| Option | Default | Description |
|--------|---------|-------------|
| `uploadUrl` | required | Upload endpoint |
| `maxFiles` | 10 | Maximum files |
| `maxSize` | 5 | Max size in MB |
| `accept` | '*' | Accepted types |
| `autoUpload` | true | Upload immediately |

---

## clipboard

Copy text to clipboard.

```html
<div x-data="clipboard()">
    <input type="text" value="texto a copiar" x-ref="source">
    <button @click="copy($refs.source.value)">
        <span x-show="!copied">Copiar</span>
        <span x-show="copied">¡Copiado!</span>
    </button>
</div>
```

---

## searchableSelect

Select dropdown with search.

```html
<div x-data="searchableSelect({
    options: {{ options|safe }},
    selected: '{{ selected }}',
    placeholder: 'Seleccionar...',
    searchPlaceholder: 'Buscar...'
})">
    <button @click="open = !open" class="w-full text-left border p-2">
        <span x-text="selectedLabel || placeholder"></span>
    </button>

    <div x-show="open" @click.away="open = false" class="absolute bg-white border mt-1 w-full">
        <input x-model="search" :placeholder="searchPlaceholder" class="w-full p-2 border-b">
        <template x-for="opt in filteredOptions" :key="opt.value">
            <div @click="select(opt)" class="p-2 hover:bg-gray-100 cursor-pointer">
                <span x-text="opt.label"></span>
            </div>
        </template>
    </div>

    <input type="hidden" :name="name" :value="selected">
</div>
```

---

## confirmAction

Confirmation before action.

```html
<button
    x-data="confirmAction({
        title: '¿Eliminar?',
        message: 'Esta acción no se puede deshacer',
        confirmText: 'Eliminar',
        onConfirm: () => $el.closest('form').submit()
    })"
    @click="showConfirm()"
>
    Eliminar
</button>
```

---

## charCounter

Character counter for textareas.

```html
<div x-data="charCounter({ max: 500 })">
    <textarea x-model="text" maxlength="500"></textarea>
    <span x-text="`${count}/${max}`" :class="{ 'text-red-500': remaining < 50 }"></span>
</div>
```

---

## currencyInput

Auto-format currency as user types.

```html
<input
    x-data="currencyInput({ currency: 'DOP', locale: 'es-DO' })"
    x-model="formatted"
    @input="format()"
    type="text"
>
<input type="hidden" name="amount" :value="raw">
```

---

## phoneInput

Auto-format phone numbers.

```html
<input
    x-data="phoneInput({ format: '(###) ###-####' })"
    x-model="formatted"
    @input="format()"
    type="tel"
>
```

---

## dirtyForm

Warn user about unsaved changes.

```html
<form x-data="dirtyForm()" @submit="isDirty = false">
    <input x-model="fields.name" name="name">
    <input x-model="fields.email" name="email">

    <button type="submit" :disabled="!isDirty">Guardar</button>
</form>
```

Shows browser confirmation dialog if user tries to navigate away with unsaved changes.

---

## infiniteScroll

Load more content on scroll.

```html
<div x-data="infiniteScroll({
    url: '/api/items/',
    target: '#items-list',
    threshold: 200
})">
    <div id="items-list">
        {% for item in items %}
            <div>{{ item.name }}</div>
        {% endfor %}
    </div>
    <div x-show="loading">Cargando...</div>
    <div x-show="!hasMore">No hay más items</div>
</div>
```

---

## tabs

Client-side tab switching (no server).

```html
<div x-data="tabs({ active: 'info' })">
    <div class="flex gap-2">
        <button @click="active = 'info'" :class="{ 'active': active === 'info' }">Info</button>
        <button @click="active = 'docs'" :class="{ 'active': active === 'docs' }">Docs</button>
    </div>

    <div x-show="active === 'info'">Info content</div>
    <div x-show="active === 'docs'">Docs content</div>
</div>
```

For server-loaded tabs, use `{% nitro_tabs %}` instead.

---

## toggle

Collapsible sections.

```html
<div x-data="toggle({ open: false })">
    <button @click="toggle()">
        <span x-text="open ? 'Ocultar' : 'Mostrar'"></span>
    </button>
    <div x-show="open" x-collapse>
        Hidden content here
    </div>
</div>
```

---

## darkMode

Theme toggle.

```html
<button x-data="darkMode()" @click="toggle()">
    <span x-show="!isDark">🌙</span>
    <span x-show="isDark">☀️</span>
</button>
```

Persists preference in localStorage.
