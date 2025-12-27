/* nitro_core/static/nitro.js */

// Debug mode: Set window.NITRO_DEBUG = true to enable debug logging
const NITRO_DEBUG = typeof window !== 'undefined' && window.NITRO_DEBUG === true;

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
            isLoading: false,

            get errors() { return this._errors; },
            get messages() { return this._messages; },

            async call(actionName, payload = {}, file = null) {
            this.isLoading = true;
            this._errors = {};

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
                    alert("⚠️ Security: Data has been tampered with.");
                    return;
                }

                if (!response.ok) {
                    const txt = await response.text();
                    console.error("[Nitro] Server Error:", txt);
                    throw new Error(`Server error: ${response.status}`);
                }

                const data = await response.json();

                // Update component state
                Object.assign(this, data.state);
                this._errors = data.errors || {};
                this._integrity = data.integrity;
                this._messages = data.messages || [];

                // Log messages to console in debug mode
                if (NITRO_DEBUG && data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        const icon = msg.level === 'success' ? '✅' : msg.level === 'error' ? '❌' : '🔔';
                        console.log(`${icon} [${msg.level}]: ${msg.text}`);
                    });
                }

            } catch (err) {
                console.error('Nitro Error:', err);
            } finally {
                this.isLoading = false;
            }
        },

        _getCleanState() {
            // Use JSON serialization to get all enumerable properties
            const serialized = JSON.parse(JSON.stringify(this));

            // Remove forbidden internal fields and Alpine internals
            const forbidden = ['_errors', '_integrity', '_messages', 'isLoading', 'errors', 'messages'];
            forbidden.forEach(key => delete serialized[key]);

            // Remove Alpine internal properties (start with $)
            Object.keys(serialized).forEach(key => {
                if (key.startsWith('$')) {
                    delete serialized[key];
                }
            });

            return serialized;
        }
        };
    })
});