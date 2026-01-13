# Django Nitro Examples

This directory contains example applications demonstrating Django Nitro features.

## Available Examples

### 1. Counter (Basic)
**Directory**: `counter/`

A simple counter component demonstrating:
- Basic component structure
- State management
- Action methods
- Template integration

**Run**: Navigate to the directory and follow the README instructions.

---

### 2. Contact Form (v0.6.0) ⭐ NEW
**Directory**: `contact-form/`

Demonstrates the new **Form Field Template Tags** introduced in v0.6.0:
- `{% nitro_input %}` - Text, email, tel inputs
- `{% nitro_select %}` - Dropdown with choices
- `{% nitro_textarea %}` - Multi-line text input
- `{% nitro_checkbox %}` - Boolean fields
- Automatic validation and error handling
- Bootstrap integration

**Run**:
```bash
cd contact-form
python app.py
```

Then visit: http://127.0.0.1:8000

---

### 3. File Upload
**Directory**: `file-upload/`

Demonstrates file upload functionality with:
- `{% nitro_file %}` template tag
- File handling in components
- Progress indicators
- File validation

**Run**: Navigate to the directory and follow the README instructions.

---

### 4. Property Manager (Advanced)
**Directory**: `property-manager/`

A complete property management application demonstrating:
- CRUD operations with `BaseListComponent`
- Pagination, search, and filtering
- Multi-tenant data isolation
- Security mixins (OwnershipMixin, TenantScopedMixin)
- Complex forms and validation
- File uploads
- Responsive design with Tailwind CSS

**Run**: Navigate to the directory and follow the README instructions.

---

## Quick Start

Each example is self-contained and can be run independently. Most examples include:

1. **README.md** - Setup instructions and feature descriptions
2. **app.py** or **manage.py** - Django application entry point
3. **component.py** - Nitro component definitions
4. **templates/** - Django templates

## Requirements

All examples require:
- Python 3.12+
- Django 5.2+ or 6.0+
- django-nitro 0.6.0+

For Django 5.2 compatibility, install:
```bash
pip install django-nitro[django52]
```

## Learning Path

Recommended order for learning Django Nitro:

1. **counter** - Learn basic concepts
2. **contact-form** - Learn form field template tags (v0.6.0)
3. **file-upload** - Learn file handling
4. **property-manager** - See everything in action

## Documentation

For complete documentation, see:
- Main README: `/README.md`
- Official docs: https://github.com/django-nitro/django-nitro

## Contributing

Found a bug or have an improvement? Please open an issue or submit a PR!
