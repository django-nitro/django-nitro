/**
 * Django Nitro 0.8 - Core JS for HTMX + Alpine integration.
 *
 * Responsibilities:
 * - CSRF token on all HTMX requests
 * - HTMX error handling → toast notifications
 * - HX-Trigger 'showToast' → toast component
 * - HX-Trigger 'closeModal'/'closeSlideover' → Alpine events
 * - Loading indicator management
 * - NitroToast (vanilla JS fallback)
 * - NitroUtils (clipboard, formatting, debounce)
 * - Alpine components: toastManager, nitroModal, nitroSlideover, nitroSelect
 */

(function () {
  'use strict';

  // ========================================================================
  // CSRF Token for HTMX
  // ========================================================================

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

  // Add CSRF token to all HTMX requests
  document.addEventListener('htmx:configRequest', function (event) {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      event.detail.headers['X-CSRFToken'] = csrfToken;
    }
  });

  // ========================================================================
  // HTMX Loading Indicators
  // ========================================================================

  document.addEventListener('htmx:beforeRequest', function (event) {
    var target = event.detail.target;
    if (target) {
      target.classList.add('htmx-loading');
    }
  });

  document.addEventListener('htmx:afterRequest', function (event) {
    var target = event.detail.target;
    if (target) {
      target.classList.remove('htmx-loading');
    }
  });

  // ========================================================================
  // HTMX + Alpine Integration
  // ========================================================================

  // Ensure Alpine components initialize on HTMX-swapped content
  // This handles cases where morph/innerHTML swaps don't trigger MutationObserver correctly
  document.addEventListener('htmx:afterSwap', function (event) {
    if (window.Alpine && event.detail.target) {
      // Small delay to let DOM settle after swap
      requestAnimationFrame(function () {
        // Find any uninitialized Alpine components and init them
        var uninitializedEls = event.detail.target.querySelectorAll('[x-data]:not([data-alpine-initialized])');
        uninitializedEls.forEach(function (el) {
          Alpine.initTree(el);
        });
      });
    }
  });

  // ========================================================================
  // HTMX Error Handling
  // ========================================================================

  document.addEventListener('htmx:responseError', function (event) {
    var status = event.detail.xhr.status;
    var message = 'Error del servidor. Intente nuevamente.';
    if (status === 403) message = 'No tienes permiso para esta acción.';
    if (status === 404) message = 'Recurso no encontrado.';
    if (status === 422) message = 'Error de validación.';
    if (status === 500) message = 'Error interno del servidor.';

    window.dispatchEvent(new CustomEvent('show-toast', {
      detail: { message: message, type: 'error' }
    }));
  });

  // ========================================================================
  // HX-Trigger: closeModal, closeSlideover
  // Note: showToast is handled by HTMX automatically dispatching the event
  // ========================================================================

  document.addEventListener('htmx:afterRequest', function (event) {
    var xhr = event.detail.xhr;
    if (!xhr) return;
    var trigger = xhr.getResponseHeader('HX-Trigger');
    if (!trigger) return;

    try {
      var data = JSON.parse(trigger);
      // Note: showToast is NOT handled here - HTMX dispatches it automatically
      // and NitroToast listens via document.body.addEventListener('showToast', ...)
      if (data.closeModal) {
        window.dispatchEvent(new CustomEvent('close-modal', {
          detail: data.closeModal
        }));
      }
      if (data.closeSlideover) {
        window.dispatchEvent(new CustomEvent('close-slideover', {
          detail: data.closeSlideover
        }));
      }
    } catch (e) {
      // Not JSON, might be a simple event name
    }
  });

  // ========================================================================
  // NitroToast (Vanilla JS - works without Alpine)
  // ========================================================================

  var NitroToast = {
    container: null,
    counter: 0,

    init: function () {
      if (this.container) return;

      this.container = document.createElement('div');
      this.container.id = 'nitro-toast-container';
      this.container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
      document.body.appendChild(this.container);

      var self = this;
      // Listen for custom show-toast events (from our code)
      window.addEventListener('show-toast', function (e) { self.show(e.detail); });
      // Listen for HTMX HX-Trigger showToast events (bubbles from triggering element)
      // Use capture phase and track shown messages to prevent duplicates
      var shownMessages = new Set();
      document.addEventListener('showToast', function (e) {
        var key = JSON.stringify(e.detail);
        if (!shownMessages.has(key)) {
          shownMessages.add(key);
          self.show(e.detail);
          // Clear after a short delay to allow same message later
          setTimeout(function() { shownMessages.delete(key); }, 100);
        }
      }, true);
    },

    show: function (opts) {
      var message = opts.message || '';
      var type = opts.type || 'info';
      var duration = opts.duration !== undefined ? opts.duration : 5000;
      var id = ++this.counter;

      var colors = {
        success: 'bg-green-50 border-green-200 text-green-800',
        error: 'bg-red-50 border-red-200 text-red-800',
        warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800'
      };
      var icons = { success: '\u2713', error: '\u2717', warning: '\u26A0', info: '\u2139' };

      var toast = document.createElement('div');
      toast.id = 'toast-' + id;
      toast.className = 'flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg max-w-sm transform transition-all duration-300 translate-y-2 opacity-0 ' + (colors[type] || colors.info);
      toast.innerHTML =
        '<span>' + (icons[type] || icons.info) + '</span>' +
        '<span class="flex-1">' + this.escapeHtml(message) + '</span>' +
        '<button onclick="NitroToast.remove(' + id + ')" class="text-gray-400 hover:text-gray-600">\u00D7</button>';

      this.container.appendChild(toast);

      requestAnimationFrame(function () {
        toast.classList.remove('translate-y-2', 'opacity-0');
      });

      if (duration > 0) {
        var self = this;
        setTimeout(function () { self.remove(id); }, duration);
      }

      return id;
    },

    remove: function (id) {
      var toast = document.getElementById('toast-' + id);
      if (toast) {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(function () { toast.remove(); }, 300);
      }
    },

    escapeHtml: function (text) {
      var div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    },

    success: function (message, duration) { return this.show({ message: message, type: 'success', duration: duration }); },
    error: function (message, duration) { return this.show({ message: message, type: 'error', duration: duration }); },
    warning: function (message, duration) { return this.show({ message: message, type: 'warning', duration: duration }); },
    info: function (message, duration) { return this.show({ message: message, type: 'info', duration: duration }); }
  };

  // Auto-init NitroToast on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', function () { NitroToast.init(); });

  // ========================================================================
  // NitroUtils - Common JS utilities
  // ========================================================================

  var NitroUtils = {
    copyToClipboard: function (text) {
      return navigator.clipboard.writeText(text).then(function () {
        NitroToast.success('Copiado al portapapeles');
        return true;
      }).catch(function () {
        NitroToast.error('Error al copiar');
        return false;
      });
    },

    formatCurrency: function (amount, currency) {
      currency = currency || (window.NITRO_DEFAULT_CURRENCY || 'USD');
      var symbols = { DOP: 'RD$', USD: 'US$', EUR: '\u20AC' };
      var symbol = symbols[currency] || currency;
      return symbol + ' ' + parseFloat(amount).toLocaleString('en-US', { minimumFractionDigits: 2 });
    },

    formatPhone: function (phone) {
      var digits = phone.replace(/\D/g, '');
      if (digits.length === 10) {
        return '(' + digits.slice(0, 3) + ') ' + digits.slice(3, 6) + '-' + digits.slice(6);
      }
      return phone;
    },

    formatFileSize: function (bytes) {
      if (bytes === 0) return '0 Bytes';
      var k = 1024;
      var sizes = ['Bytes', 'KB', 'MB', 'GB'];
      var i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    debounce: function (func, wait) {
      var timeout;
      return function () {
        var args = arguments;
        var context = this;
        clearTimeout(timeout);
        timeout = setTimeout(function () { func.apply(context, args); }, wait);
      };
    },

    whatsappLink: function (phone, message) {
      var cleanPhone = phone.replace(/\D/g, '');
      var url = 'https://wa.me/' + cleanPhone;
      if (message) {
        url += '?text=' + encodeURIComponent(message);
      }
      return url;
    }
  };

  // ========================================================================
  // Loading Button Styles
  // ========================================================================

  var style = document.createElement('style');
  style.textContent =
    '.nitro-btn-loading .nitro-spinner { display: inline-block; }' +
    '.nitro-btn-loading .nitro-btn-text { opacity: 0.7; }' +
    '.nitro-btn-loading { pointer-events: none; }' +
    '.nitro-spinner { display: none; }';
  document.head.appendChild(style);

  // Expose globally
  window.NitroToast = NitroToast;
  window.NitroUtils = NitroUtils;

  // ========================================================================
  // Global Event Helpers (for use in templates)
  // ========================================================================

  window.Nitro = {
    openSlideover: function (id) {
      window.dispatchEvent(new CustomEvent('open-slideover', { detail: id }));
    },
    closeSlideover: function (id) {
      window.dispatchEvent(new CustomEvent('close-slideover', { detail: id || '' }));
    },
    openModal: function (id) {
      window.dispatchEvent(new CustomEvent('open-modal', { detail: id }));
    },
    closeModal: function (id) {
      window.dispatchEvent(new CustomEvent('close-modal', { detail: id || '' }));
    }
  };

  // ========================================================================
  // Alpine Components
  // ========================================================================

  document.addEventListener('alpine:init', function () {

    // Toast Manager (Alpine version) - DEPRECATED: Use NitroToast instead
    // This component is kept for backwards compatibility but doesn't listen to events
    // NitroToast (vanilla JS) handles all toast notifications
    Alpine.data('toastManager', function () {
      return {
        toasts: [],
        addToast: function (message, type) {
          var id = Date.now();
          type = type || 'success';
          this.toasts.push({ id: id, message: message, type: type });
          var self = this;
          setTimeout(function () {
            self.toasts = self.toasts.filter(function (t) { return t.id !== id; });
          }, 4000);
        },
        init: function () {
          // NitroToast handles show-toast events - this is kept for manual Alpine usage only
        }
      };
    });

    // Modal Component
    Alpine.data('nitroModal', function (modalId) {
      return {
        open: false,
        modalId: modalId,
        init: function () {
          var self = this;
          window.addEventListener('open-modal', function (e) {
            if (e.detail === self.modalId) self.open = true;
          });
          window.addEventListener('close-modal', function (e) {
            if (e.detail === self.modalId) self.open = false;
          });
        }
      };
    });

    // Slideover Component
    Alpine.data('nitroSlideover', function (slideoverId) {
      return {
        open: false,
        slideoverId: slideoverId,
        init: function () {
          var self = this;
          window.addEventListener('open-slideover', function (e) {
            if (e.detail === self.slideoverId) self.open = true;
          });
          window.addEventListener('close-slideover', function (e) {
            if (!e.detail || e.detail === self.slideoverId) self.open = false;
          });
        }
      };
    });

    // Searchable Select Component (with optional cascade support)
    Alpine.data('nitroSelect', function (config) {
      return {
        open: false,
        search: '',
        selectedValue: config.value || '',
        selectedLabel: config.label || '',
        options: config.options || [],
        filteredOptions: [],
        searchUrl: config.searchUrl || '',
        loading: false,
        highlightIndex: -1,
        parentInput: config.parentInput || '',
        cascadeParam: config.cascadeParam || 'parent',

        init: function () {
          var self = this;
          this.filteredOptions = this.options;
          if (this.selectedValue) {
            var found = this.options.find(function (o) { return o.value === config.value; });
            if (found) this.selectedLabel = found.label;
          }
          // Watch parent for cascade (search within same form, not globally)
          if (this.parentInput) {
            // Use $nextTick to ensure all Alpine components have initialized
            this.$nextTick(function () {
              // Find the form this component belongs to
              var form = self.$el.closest('form');
              var parentEl = form
                ? form.querySelector(self.parentInput)
                : document.querySelector(self.parentInput);
              if (parentEl) {
                // If parent already has a value, load children (preserving current selection)
                if (parentEl.value && self.searchUrl) {
                  var savedValue = self.selectedValue;
                  var savedLabel = self.selectedLabel;
                  self.loading = true;
                  fetch(self._buildUrl())
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                      self.options = data.results || [];
                      self.filteredOptions = self.options;
                      // Restore saved selection if it's in the loaded options
                      if (savedValue) {
                        var found = self.options.find(function (o) { return o.value === savedValue; });
                        if (found) {
                          self.selectedValue = savedValue;
                          self.selectedLabel = found.label;
                        }
                      }
                      self.loading = false;
                      // Notify dependent selects that this one is ready
                      self.$refs.hiddenInput.dispatchEvent(new Event('cascade-ready', { bubbles: true }));
                    })
                    .catch(function () { self.loading = false; });
                }
                // Listen for future changes
                parentEl.addEventListener('change', function () {
                  self.clear();
                  if (self.searchUrl && parentEl.value) {
                    self.loadChildren(parentEl.value);
                  } else {
                    self.options = [];
                    self.filteredOptions = [];
                  }
                });
                // Also listen for cascade-ready from parent (for chained cascades)
                parentEl.addEventListener('cascade-ready', function () {
                  if (self.searchUrl && parentEl.value && !self.selectedValue) {
                    self.loadChildren(parentEl.value);
                  }
                });
              }
            });
          }
        },

        _buildUrl: function (extraParams) {
          var url = this.searchUrl;
          if (this.parentInput) {
            var form = this.$el.closest('form');
            var parentEl = form
              ? form.querySelector(this.parentInput)
              : document.querySelector(this.parentInput);
            if (parentEl && parentEl.value) {
              var sep = url.indexOf('?') !== -1 ? '&' : '?';
              url += sep + this.cascadeParam + '=' + encodeURIComponent(parentEl.value);
            }
          }
          if (extraParams) {
            var sep2 = url.indexOf('?') !== -1 ? '&' : '?';
            url += sep2 + extraParams;
          }
          return url;
        },

        loadChildren: function (parentValue) {
          var self = this;
          if (!parentValue || !self.searchUrl) return;
          self.loading = true;
          fetch(self._buildUrl())
            .then(function (r) { return r.json(); })
            .then(function (data) {
              self.options = data.results || [];
              self.filteredOptions = self.options;
              self.loading = false;
            })
            .catch(function () { self.loading = false; });
        },

        filter: function () {
          var self = this;
          self.highlightIndex = -1;
          if (self.searchUrl) {
            self.loading = true;
            fetch(self._buildUrl('q=' + encodeURIComponent(self.search)))
              .then(function (r) { return r.json(); })
              .then(function (data) {
                self.filteredOptions = data.results || [];
                self.loading = false;
              })
              .catch(function () { self.loading = false; });
          } else {
            var q = self.search.toLowerCase();
            if (!q) {
              self.filteredOptions = self.options;
            } else {
              self.filteredOptions = self.options.filter(function (o) {
                return o.label.toLowerCase().indexOf(q) !== -1;
              });
            }
          }
        },

        select: function (value, label) {
          this.selectedValue = value;
          this.selectedLabel = label;
          this.open = false;
          this.search = '';
          this.filteredOptions = this.options;
          this.$refs.hiddenInput.value = value;
          this.$refs.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
        },

        clear: function () {
          this.selectedValue = '';
          this.selectedLabel = '';
          this.search = '';
          this.filteredOptions = this.options;
          this.$refs.hiddenInput.value = '';
          this.$refs.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
        },

        onKeydown: function (event) {
          if (event.key === 'ArrowDown') {
            event.preventDefault();
            if (this.highlightIndex < this.filteredOptions.length - 1) this.highlightIndex++;
          } else if (event.key === 'ArrowUp') {
            event.preventDefault();
            if (this.highlightIndex > 0) this.highlightIndex--;
          } else if (event.key === 'Enter') {
            event.preventDefault();
            if (this.highlightIndex >= 0 && this.filteredOptions[this.highlightIndex]) {
              var opt = this.filteredOptions[this.highlightIndex];
              this.select(opt.value, opt.label);
            }
          } else if (event.key === 'Escape') {
            this.open = false;
          }
        }
      };
    });
  });

})();
