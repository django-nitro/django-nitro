/**
 * Django Nitro v0.5.0
 *
 * Client-side integration for Django Nitro components using Alpine.js.
 *
 * DOM Events:
 * - nitro:message        → { level, text } - Each message/toast
 * - nitro:action-complete → { component, action } - Action succeeded
 * - nitro:error          → { component, action, error, status } - Error occurred
 * - nitro:* (custom)     → Custom events emitted from Python with emit()
 *
 * Toast System:
 * - Nitro includes native toasts that work without dependencies
 * - To use your favorite toast library, define window.NitroToastAdapter:
 *
 *   window.NitroToastAdapter = {
 *       show: function(message, level, config) {
 *           // message: string - Toast message
 *           // level: 'success' | 'error' | 'info' | 'warning'
 *           // config: { enabled, position, duration, style }
 *           Swal.fire({ icon: level, title: message, toast: true });
 *       }
 *   };
 *
 * Debug Mode:
 * - Set window.NITRO_DEBUG = true to enable detailed console logging
 */

// Debug mode: Set window.NITRO_DEBUG = true to enable debug logging
const NITRO_DEBUG = typeof window !== 'undefined' && window.NITRO_DEBUG === true;

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Show a toast notification
 * Checks for custom adapter or uses native implementation
 */
function showToast(message, level, config) {
    // Check if custom adapter is available
    if (window.NitroToastAdapter && typeof window.NitroToastAdapter.show === 'function') {
        window.NitroToastAdapter.show(message, level, config);
        return;
    }

    // Fall back to native toasts
    showNativeToast(message, level, config);
}

/**
 * Native toast implementation
 * Professional toasts without external dependencies
 */
function showNativeToast(message, level = 'info', config = {}) {
    const {
        position = 'top-right',
        duration = 3000,
        style = 'default'
    } = config;

    // Get or create toast container
    const containerClass = `nitro-toast-container nitro-toast-${position}`;
    let container = document.querySelector(`.${containerClass.replace(/ /g, '.')}`);
    if (!container) {
        container = document.createElement('div');
        container.className = containerClass;
        document.body.appendChild(container);
    }

    // Icon mapping
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    // Create toast element (safe from XSS)
    const toast = document.createElement('div');
    toast.className = `nitro-toast nitro-toast-${level} nitro-toast-${style}`;

    // Icon
    const iconSpan = document.createElement('span');
    iconSpan.className = 'nitro-toast-icon';
    iconSpan.textContent = icons[level] || icons.info;

    // Message (textContent prevents XSS)
    const textSpan = document.createElement('span');
    textSpan.className = 'nitro-toast-text';
    textSpan.textContent = message;

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'nitro-toast-close';
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.innerHTML = '&times;';

    toast.appendChild(iconSpan);
    toast.appendChild(textSpan);
    toast.appendChild(closeBtn);

    // Add to container
    container.appendChild(toast);

    // Close button handler
    const removeToast = () => {
        toast.classList.remove('nitro-toast-show');
        toast.classList.add('nitro-toast-hide');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            // Remove container if empty
            if (container.children.length === 0) {
                container.remove();
            }
        }, 300);
    };

    closeBtn.addEventListener('click', removeToast);

    // Trigger show animation
    requestAnimationFrame(() => {
        toast.classList.add('nitro-toast-show');
    });

    // Auto-remove after duration
    if (duration > 0) {
        setTimeout(removeToast, duration);
    }
}

/**
 * Apply list diff for smart updates
 * Updates array in-place based on diff operations
 */
function applyListDiff(currentArray, diff) {
    if (!diff) return;

    // Remove items
    if (diff.removed && diff.removed.length > 0) {
        diff.removed.forEach(id => {
            const index = currentArray.findIndex(item => item.id === id);
            if (index !== -1) {
                currentArray.splice(index, 1);
            }
        });
    }

    // Update items
    if (diff.updated && diff.updated.length > 0) {
        diff.updated.forEach(updatedItem => {
            const index = currentArray.findIndex(item => item.id === updatedItem.id);
            if (index !== -1) {
                Object.assign(currentArray[index], updatedItem);
            }
        });
    }

    // Add items (to the end by default)
    if (diff.added && diff.added.length > 0) {
        diff.added.forEach(item => {
            currentArray.push(item);
        });
    }
}

/**
 * Alpine.js component initialization
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('nitro', (componentName, element) => {
        // Parse state from data attribute
        const initialPayload = JSON.parse(element.dataset.nitroState || '{}');

        // Validate we got data
        if (!initialPayload.state) {
            console.error('[Nitro] No state found in data attribute for', componentName);
            initialPayload.state = {};
        }

        if (NITRO_DEBUG) {
            console.log('[Nitro] Initializing', componentName, 'with state:', initialPayload.state);
        }

        return {
            // Spread state into component root
            ...initialPayload.state,

            // Internal variables
            _errors: initialPayload.errors || {},
            _integrity: initialPayload.integrity || null,
            _messages: initialPayload.messages || [],
            _toast_config: initialPayload.toast_config || {},
            _events: [],
            isLoading: false,

            get errors() { return this._errors; },
            get messages() { return this._messages; },
            get events() { return this._events; },

            async call(actionName, payload = {}, file = null) {
                this.isLoading = true;
                this._errors = {};
                element.setAttribute('data-loading', 'true');

                try {
                    const cleanState = this._getCleanState();

                    if (NITRO_DEBUG) {
                        console.log('[Nitro] Calling action:', actionName);
                        console.log('[Nitro] State being sent:', cleanState);
                        console.log('[Nitro] Payload:', payload);
                        console.log('[Nitro] File:', file);
                    }

                    let requestBody;
                    let headers = {
                        'X-CSRFToken': getCookie('csrftoken')
                    };

                    if (file) {
                        // Use FormData for file uploads
                        const formData = new FormData();
                        formData.append('component_name', componentName);
                        formData.append('action', actionName);
                        formData.append('state', JSON.stringify(cleanState));
                        formData.append('payload', JSON.stringify(payload));
                        formData.append('integrity', this._integrity || '');
                        formData.append('file', file);

                        requestBody = formData;
                        // Don't set Content-Type - FormData sets it with boundary
                    } else {
                        // Use JSON for normal requests
                        headers['Content-Type'] = 'application/json';
                        requestBody = JSON.stringify({
                            component_name: componentName,
                            action: actionName,
                            state: cleanState,
                            payload: payload,
                            integrity: this._integrity
                        });
                    }

                    const response = await fetch('/api/nitro/dispatch', {
                        method: 'POST',
                        headers: headers,
                        body: requestBody
                    });

                    if (response.status === 403) {
                        this._dispatchEvent('nitro:error', {
                            action: actionName,
                            error: 'Security verification failed',
                            status: 403
                        });
                        alert("⚠️ Security: Data has been tampered with.");
                        return;
                    }

                    if (!response.ok) {
                        const txt = await response.text();
                        console.error("[Nitro] Server Error:", txt);
                        this._dispatchEvent('nitro:error', {
                            action: actionName,
                            error: txt,
                            status: response.status
                        });
                        throw new Error(`Server error: ${response.status}`);
                    }

                    const data = await response.json();

                    // Handle smart updates (partial state with diffs)
                    if (data.partial && data.state) {
                        // Apply diffs for arrays
                        Object.keys(data.state).forEach(key => {
                            const value = data.state[key];
                            if (value && typeof value === 'object' && 'diff' in value) {
                                // Apply list diff
                                if (Array.isArray(this[key])) {
                                    applyListDiff(this[key], value.diff);
                                }
                            } else {
                                // Regular update
                                this[key] = value;
                            }
                        });
                    } else {
                        // Full state update (backward compatible)
                        Object.assign(this, data.state);
                    }

                    this._errors = data.errors || {};
                    this._integrity = data.integrity;
                    this._messages = data.messages || [];

                    // Update toast config if provided
                    if (data.toast_config) {
                        this._toast_config = data.toast_config;
                    }

                    // Show toast messages
                    if (this._toast_config.enabled && data.messages && data.messages.length > 0) {
                        data.messages.forEach(msg => {
                            showToast(msg.text, msg.level, this._toast_config);
                        });
                    }

                    // Emit message events (for custom handling)
                    if (data.messages && data.messages.length > 0) {
                        data.messages.forEach(msg => {
                            this._dispatchEvent('nitro:message', {
                                level: msg.level,
                                text: msg.text
                            });
                        });
                    }

                    // Process and emit custom events from server
                    if (data.events && data.events.length > 0) {
                        data.events.forEach(event => {
                            this._dispatchEvent(event.name, event.data || {});
                        });
                    }

                    // Emit action complete event
                    this._dispatchEvent('nitro:action-complete', {
                        action: actionName,
                        state: data.state
                    });

                    // Log messages to console in debug mode
                    if (NITRO_DEBUG && data.messages && data.messages.length > 0) {
                        data.messages.forEach(msg => {
                            const icon = msg.level === 'success' ? '✅' : msg.level === 'error' ? '❌' : '🔔';
                            console.log(`${icon} [${msg.level}]: ${msg.text}`);
                        });
                    }

                } catch (err) {
                    console.error('Nitro Error:', err);
                    this._dispatchEvent('nitro:error', {
                        action: actionName,
                        error: err.message
                    });
                } finally {
                    this.isLoading = false;
                    element.removeAttribute('data-loading');
                }
            },

            _getCleanState() {
                // Use JSON serialization to get all enumerable properties
                const serialized = JSON.parse(JSON.stringify(this));

                // Remove forbidden internal fields and Alpine internals
                const forbidden = ['_errors', '_integrity', '_messages', '_toast_config', '_events', 'isLoading', 'errors', 'messages', 'events'];
                forbidden.forEach(key => delete serialized[key]);

                // Remove Alpine internal properties (start with $)
                Object.keys(serialized).forEach(key => {
                    if (key.startsWith('$')) {
                        delete serialized[key];
                    }
                });

                return serialized;
            },

            _dispatchEvent(eventName, detail = {}) {
                const event = new CustomEvent(eventName, {
                    detail: {
                        component: componentName,
                        ...detail
                    },
                    bubbles: true,
                    cancelable: true
                });
                window.dispatchEvent(event);

                if (NITRO_DEBUG) {
                    console.log(`[Nitro] Event: ${eventName}`, detail);
                }
            },

            /**
             * Handle file upload with progress tracking and preview
             * Used by {% nitro_file %} template tag
             */
            async handleFileUpload(event, fieldName, options = {}) {
                const file = event.target.files?.[0];
                if (!file) {
                    if (NITRO_DEBUG) {
                        console.log('[Nitro] No file selected');
                    }
                    return;
                }

                if (NITRO_DEBUG) {
                    console.log('[Nitro] File selected:', file.name, file.size, 'bytes');
                }

                // Validate file size if maxSize specified
                if (options.maxSize) {
                    const maxBytes = this._parseFileSize(options.maxSize);
                    if (file.size > maxBytes) {
                        const maxSizeFormatted = this._formatFileSize(maxBytes);
                        const fileSizeFormatted = this._formatFileSize(file.size);
                        this._errors[fieldName] = `File is too large (${fileSizeFormatted}). Maximum allowed: ${maxSizeFormatted}`;

                        // Dispatch error event
                        this._dispatchEvent('nitro:file-error', {
                            field: fieldName,
                            error: 'File too large',
                            size: file.size,
                            maxSize: maxBytes
                        });

                        if (NITRO_DEBUG) {
                            console.error('[Nitro] File too large:', fileSizeFormatted, '>', maxSizeFormatted);
                        }
                        return;
                    }
                }

                // Generate preview for images if requested
                if (options.preview && file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        // Store preview URL in state
                        this[`${fieldName}Preview`] = e.target.result;

                        // Dispatch preview ready event
                        this._dispatchEvent('nitro:file-preview', {
                            field: fieldName,
                            preview: e.target.result,
                            file: { name: file.name, size: file.size, type: file.type }
                        });
                    };
                    reader.readAsDataURL(file);
                }

                // Initialize upload progress
                this[`${fieldName}UploadProgress`] = 0;
                this[`${fieldName}Uploading`] = true;

                try {
                    // Dispatch upload start event
                    this._dispatchEvent('nitro:file-upload-start', {
                        field: fieldName,
                        file: { name: file.name, size: file.size, type: file.type }
                    });

                    // Upload file using XMLHttpRequest for progress tracking
                    const uploadedFile = await this._uploadFileWithProgress(file, fieldName);

                    // Store file info in state
                    this[fieldName] = {
                        name: file.name,
                        size: file.size,
                        type: file.type,
                        url: uploadedFile.url || null
                    };

                    // Dispatch upload complete event
                    this._dispatchEvent('nitro:file-upload-complete', {
                        field: fieldName,
                        file: this[fieldName]
                    });

                    if (NITRO_DEBUG) {
                        console.log('[Nitro] File upload complete:', this[fieldName]);
                    }

                } catch (error) {
                    this._errors[fieldName] = error.message || 'Upload failed';

                    // Dispatch error event
                    this._dispatchEvent('nitro:file-error', {
                        field: fieldName,
                        error: error.message
                    });

                    if (NITRO_DEBUG) {
                        console.error('[Nitro] File upload error:', error);
                    }
                } finally {
                    this[`${fieldName}Uploading`] = false;
                }
            },

            /**
             * Upload file with progress tracking using the call() method
             */
            async _uploadFileWithProgress(file, fieldName) {
                // Call the upload action with the file
                // The server should handle the file upload
                await this.call('_handle_file_upload', { field: fieldName }, file);

                // Update progress to 100%
                this[`${fieldName}UploadProgress`] = 100;

                return { url: null }; // Server will handle storing the file
            },

            /**
             * Parse file size string (e.g., "5MB", "1GB") to bytes
             */
            _parseFileSize(sizeStr) {
                const units = {
                    'B': 1,
                    'KB': 1024,
                    'MB': 1024 * 1024,
                    'GB': 1024 * 1024 * 1024,
                    'TB': 1024 * 1024 * 1024 * 1024
                };

                const match = sizeStr.match(/^(\d+(?:\.\d+)?)\s*([A-Z]+)$/i);
                if (!match) {
                    console.error('[Nitro] Invalid file size format:', sizeStr);
                    return 0;
                }

                const value = parseFloat(match[1]);
                const unit = match[2].toUpperCase();
                return value * (units[unit] || 1);
            },

            /**
             * Format bytes to human-readable size
             */
            _formatFileSize(bytes) {
                if (bytes === 0) return '0 B';

                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));

                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
        };
    })
});
