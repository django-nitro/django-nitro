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
 * Setup event listeners with modifiers support
 * Handles nitro:click.prevent.stop="action_name" attributes
 */
function setupEventModifiers(element) {
    // Find all elements with nitro:click or similar attributes
    const eventTypes = ['click', 'submit', 'change', 'input'];

    eventTypes.forEach(eventType => {
        const selector = `[nitro\\:${eventType}], [nitro\\:${eventType}\\.prevent], [nitro\\:${eventType}\\.stop], [nitro\\:${eventType}\\.self]`;
        const elements = element.querySelectorAll(selector);

        elements.forEach(el => {
            // Get all attributes that start with nitro:{eventType}
            Array.from(el.attributes).forEach(attr => {
                if (attr.name.startsWith(`nitro:${eventType}`)) {
                    const fullAttr = attr.name;
                    const actionName = attr.value;

                    // Parse modifiers from attribute name
                    // e.g., "nitro:click.prevent.stop" -> ['prevent', 'stop']
                    const parts = fullAttr.split('.');
                    const modifiers = parts.slice(1); // Everything after "nitro:click"

                    if (NITRO_DEBUG && modifiers.length > 0) {
                        console.log(`[Nitro] Setting up ${eventType} with modifiers:`, modifiers, 'for action:', actionName);
                    }

                    // Add event listener with modifiers
                    el.addEventListener(eventType, (event) => {
                        // Apply modifiers
                        if (modifiers.includes('prevent')) {
                            event.preventDefault();
                        }
                        if (modifiers.includes('stop')) {
                            event.stopPropagation();
                        }
                        if (modifiers.includes('self')) {
                            // Only trigger if event.target === event.currentTarget
                            if (event.target !== event.currentTarget) {
                                return;
                            }
                        }

                        // Find the Alpine component and call the action
                        // This is handled by Alpine's x-data, so we just need to ensure modifiers work
                        // The actual action call is handled by Alpine's @click directive
                    });
                }
            });
        });
    });
}

/**
 * Alpine.js component initialization
 */
document.addEventListener('alpine:init', () => {
    // Create global store for dirty state tracking and component registry
    Alpine.store('nitro', {
        dirtyComponents: [],
        componentRegistry: {},

        markDirty(componentId) {
            if (!this.dirtyComponents.includes(componentId)) {
                this.dirtyComponents.push(componentId);
                if (NITRO_DEBUG) {
                    console.log('[Nitro] Component marked as dirty:', componentId);
                }
            }
        },

        markClean(componentId) {
            const index = this.dirtyComponents.indexOf(componentId);
            if (index !== -1) {
                this.dirtyComponents.splice(index, 1);
                if (NITRO_DEBUG) {
                    console.log('[Nitro] Component marked as clean:', componentId);
                }
            }
        },

        isDirty(componentId) {
            return this.dirtyComponents.includes(componentId);
        },

        hasAnyDirty() {
            return this.dirtyComponents.length > 0;
        },

        // Register component for parent-child access
        registerComponent(componentId, component, parentId) {
            this.componentRegistry[componentId] = {
                component: component,
                parentId: parentId
            };
            if (NITRO_DEBUG) {
                console.log(`[Nitro] Registered component: ${componentId}`, parentId ? `with parent: ${parentId}` : '(no parent)');
            }
        },

        // Get component by ID
        getComponent(componentId) {
            const entry = this.componentRegistry[componentId];
            return entry ? entry.component : null;
        },

        // Get parent component
        getParent(componentId) {
            const entry = this.componentRegistry[componentId];
            if (entry && entry.parentId) {
                return this.getComponent(entry.parentId);
            }
            return null;
        }
    });

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

        // Setup event modifiers for nitro:click attributes
        setTimeout(() => setupEventModifiers(element), 0);

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
            _pollInterval: null,
            _isDirty: false,
            _originalState: null,

            get errors() { return this._errors; },
            get messages() { return this._messages; },
            get events() { return this._events; },
            get isDirty() { return this._isDirty; },

            // Mark component as dirty
            markDirty() {
                if (!this._isDirty) {
                    this._isDirty = true;
                    Alpine.store('nitro').markDirty(element.id);
                }
            },

            // Mark component as clean
            markClean() {
                if (this._isDirty) {
                    this._isDirty = false;
                    Alpine.store('nitro').markClean(element.id);
                }
            },

            // Track field changes for dirty state
            trackChange(field) {
                // Mark as dirty when user changes a field
                this.markDirty();

                if (NITRO_DEBUG) {
                    console.log(`[Nitro] Field changed: ${field}, component marked dirty`);
                }
            },

            // $parent accessor for child components
            get $parent() {
                const parent = Alpine.store('nitro').getParent(element.id);
                if (!parent) {
                    console.warn(`[Nitro] No parent component found for ${element.id}`);
                    return null;
                }
                return parent;
            },

            // Initialize polling if configured
            init() {
                // Register this component in the global registry
                const parentId = element.dataset.nitroParent || null;
                Alpine.store('nitro').registerComponent(element.id, this, parentId);

                // Store original state for dirty checking
                this._originalState = JSON.stringify(this._getCleanState());
                const pollInterval = element.dataset.nitroPoll;
                if (pollInterval && parseInt(pollInterval) > 0) {
                    const interval = parseInt(pollInterval);
                    if (NITRO_DEBUG) {
                        console.log(`[Nitro] Setting up polling for ${componentName} every ${interval}ms`);
                    }

                    // Start polling
                    this._pollInterval = setInterval(() => {
                        if (!this.isLoading) {
                            if (NITRO_DEBUG) {
                                console.log(`[Nitro] Polling refresh for ${componentName}`);
                            }
                            // Call refresh action if it exists, otherwise just re-fetch state
                            if (typeof this.refresh === 'function') {
                                this.refresh();
                            } else {
                                // Default: call a _poll action that components can implement
                                this.call('_poll').catch(() => {
                                    // Ignore errors for polling - component might not have _poll action
                                });
                            }
                        }
                    }, interval);
                }
            },

            // Cleanup polling on component destroy
            destroy() {
                if (this._pollInterval) {
                    clearInterval(this._pollInterval);
                    if (NITRO_DEBUG) {
                        console.log(`[Nitro] Cleared polling interval for ${componentName}`);
                    }
                }

                // Unregister component
                delete Alpine.store('nitro').componentRegistry[element.id];
                if (NITRO_DEBUG) {
                    console.log(`[Nitro] Unregistered component: ${element.id}`);
                }
            },

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

                    // Check for error response from server
                    if (data.error) {
                        // Show error toast
                        const errorConfig = {
                            position: this._toast_config.position || 'top-right',
                            duration: 5000,  // 5 seconds for errors
                            style: this._toast_config.style || 'default'
                        };
                        showToast(data.message || 'An error occurred', 'error', errorConfig);

                        // Dispatch error event
                        this._dispatchEvent('nitro:error', {
                            action: actionName,
                            error: data.message,
                            status: response.status
                        });

                        if (NITRO_DEBUG) {
                            console.error('[Nitro] Action error:', data.message);
                        }
                        return;
                    }

                    // Handle smart updates (partial state with diffs)
                    // FIX: Always use merge strategy for partial updates (including _sync_field)
                    // This prevents data loss when syncing individual fields
                    if (data.partial && data.state) {
                        // Partial update - merge only changed fields
                        Object.keys(data.state).forEach(key => {
                            const value = data.state[key];
                            if (value && typeof value === 'object' && 'diff' in value) {
                                // Apply list diff
                                if (Array.isArray(this[key])) {
                                    applyListDiff(this[key], value.diff);
                                }
                            } else {
                                // Regular update - only update keys that are present in response
                                this[key] = value;
                            }
                        });
                    } else if (data.merge && data.state) {
                        // Explicit merge request (for _sync_field backward compat)
                        Object.keys(data.state).forEach(key => {
                            this[key] = data.state[key];
                        });
                    } else {
                        // Full state replacement (backward compatible)
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

                    // Mark component as clean after successful save/update actions
                    // Common save action names
                    const saveActions = ['save', 'update', 'create', 'save_edit', 'create_item', 'submit'];
                    if (saveActions.includes(actionName)) {
                        this.markClean();
                        if (NITRO_DEBUG) {
                            console.log(`[Nitro] Component marked clean after ${actionName}`);
                        }
                    }

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

/**
 * Warn user before leaving page with unsaved changes
 */
window.addEventListener('beforeunload', (e) => {
    // Check if any components have unsaved changes
    if (Alpine.store('nitro') && Alpine.store('nitro').hasAnyDirty()) {
        const message = 'You have unsaved changes. Are you sure you want to leave?';
        e.preventDefault();
        e.returnValue = message; // For Chrome
        return message; // For other browsers
    }
});
