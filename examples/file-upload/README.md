# File Upload Example - Django Nitro v0.5.0

This example demonstrates Django Nitro's file upload capabilities using the `{% nitro_file %}` template tag.

## Features Demonstrated

### 1. Avatar Upload Component
- **`{% nitro_file %}`** template tag with image preview
- Image-only uploads (`accept='image/*'`)
- File size validation (max 5MB)
- Automatic preview generation
- Upload progress tracking
- Clear/delete functionality

### 2. Document Upload Component
- PDF and DOCX file uploads
- File size validation (max 10MB)
- Multiple file upload support
- Download links
- Delete functionality
- Document list management

## New v0.5.0 Features Used

### `{% nitro_file %}` Template Tag
```html
<input
    type="file"
    {% nitro_file 'avatar' accept='image/*' preview=True max_size='5MB' %}
/>
```

**Parameters:**
- `field` - Field name (required)
- `accept` - File type filter (optional)
- `max_size` - Maximum file size (optional)
- `preview` - Enable image preview (optional, default: False)

### `_handle_file_upload()` Method
```python
def _handle_file_upload(self, field: str, uploaded_file=None):
    """Handle file upload automatically called by {% nitro_file %}."""
    if not uploaded_file:
        self.error("No file was uploaded")
        return

    # Save file
    filename = default_storage.save(f"avatars/{uploaded_file.name}", uploaded_file)

    # Update state
    self.state.avatar_url = default_storage.url(filename)
    self.success("File uploaded!")
```

### Other v0.5.0 Features
- **`{% nitro_if %}`** - Conditional rendering
- **`{% nitro_show %}`** - Visibility toggling
- **`{% nitro_attr %}`** - Dynamic attributes
- **`{% nitro_action %}`** - Action buttons

## Installation

1. **Add to your Django project:**
   ```bash
   # Install Django Nitro
   pip install django-nitro
   ```

2. **Configure Django settings:**
   ```python
   # settings.py
   INSTALLED_APPS = [
       'django.contrib.staticfiles',
       'nitro',
       'upload_app',
   ]

   # Media files configuration (required for file uploads)
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   ```

3. **Update URLs:**
   ```python
   # urls.py
   from django.conf import settings
   from django.conf.urls.static import static

   urlpatterns = [
       # ... your urls
   ]

   # Serve media files in development
   if settings.DEBUG:
       urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

4. **Register components:**
   ```python
   # upload_app/apps.py
   from django.apps import AppConfig

   class UploadAppConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'upload_app'

       def ready(self):
           from . import components  # Register Nitro components
   ```

5. **Use in templates:**
   ```html
   {% load nitro_tags %}

   <!DOCTYPE html>
   <html>
   <head>
       <title>File Upload Example</title>
       {% nitro_scripts %}
   </head>
   <body>
       {% nitro_component 'AvatarUpload' %}
       {% nitro_component 'DocumentUpload' %}
   </body>
   </html>
   ```

## Project Structure

```
examples/file-upload/
├── README.md                       # This file
├── upload_app/
│   ├── components.py              # Nitro components
│   └── templates/
│       └── components/
│           ├── avatar_upload.html # Avatar upload template
│           └── document_upload.html # Document upload template
```

## How It Works

### 1. Client-Side (nitro.js)
When a file is selected:
1. `handleFileUpload()` is automatically called
2. File size is validated client-side
3. Image preview is generated (if `preview=True`)
4. File is sent to server via FormData

### 2. Server-Side (Python)
1. `_handle_file_upload()` method receives the uploaded file
2. File is validated (type, size)
3. File is saved using Django's storage system
4. Component state is updated
5. Success/error message is sent to client

### 3. State Updates
The client automatically updates:
- `{field}Uploading` - Upload in progress flag
- `{field}UploadProgress` - Upload progress (0-100)
- `{field}Preview` - Base64 image preview (if `preview=True`)

## Error Handling

### Client-Side Validation
- File size validation before upload
- File type validation (accept attribute)
- Automatic error display

### Server-Side Validation
```python
def _handle_file_upload(self, field: str, uploaded_file=None):
    # Validate file exists
    if not uploaded_file:
        self.error("No file was uploaded")
        return

    # Validate file type
    if not uploaded_file.content_type.startswith("image/"):
        self.error("Only images are allowed")
        return

    # Validate file size (already done client-side)
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    if uploaded_file.size > MAX_SIZE:
        self.error("File too large")
        return

    # Save file...
```

## Events

The file upload system emits custom events:

- **`nitro:file-upload-start`** - Upload started
- **`nitro:file-upload-complete`** - Upload completed
- **`nitro:file-error`** - Upload error
- **`nitro:file-preview`** - Preview generated

Listen to events:
```html
<div @nitro:file-upload-complete.window="console.log('Upload done!', $event.detail)">
```

## Production Considerations

1. **Storage Backend**: Use cloud storage (S3, GCS) in production
   ```python
   # settings.py
   DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
   ```

2. **File Validation**: Always validate on server-side
3. **Virus Scanning**: Scan uploaded files for malware
4. **Rate Limiting**: Limit upload frequency per user
5. **Cleanup**: Delete old/unused files periodically

## Learn More

- **[Debugging Guide](../../docs/core-concepts/debugging.md)** - Debug file uploads
- **[Zero JS Mode](../../docs/core-concepts/zero-javascript-mode.md)** - Template tags reference
- **[API Reference](../../docs/api-reference.md)** - Complete API docs

## Support

For issues or questions, visit:
- **GitHub Issues**: https://github.com/django-nitro/django-nitro/issues
- **Documentation**: https://github.com/django-nitro/django-nitro#readme
