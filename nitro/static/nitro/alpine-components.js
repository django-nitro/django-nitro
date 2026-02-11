/**
 * Nitro 0.8 - Alpine.js Components
 *
 * Additional reusable Alpine components for common UI patterns.
 * Core components (toastManager, nitroModal, nitroSlideover, nitroSelect)
 * are in nitro.js. This file adds supplementary components.
 *
 * Load after Alpine.js:
 *   <script src="{% static 'nitro/alpine-components.js' %}"></script>
 *   <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
 */

document.addEventListener('alpine:init', function () {

  // =========================================================================
  // Loading Button (spinner on HTMX submit)
  // =========================================================================
  Alpine.data('loadingBtn', function () {
    return {
      loading: false,
      init: function () {
        var self = this;
        var form = this.$el.closest('form');
        if (form) {
          form.addEventListener('htmx:beforeRequest', function () { self.loading = true; });
          form.addEventListener('htmx:afterRequest', function () { self.loading = false; });
        }
      }
    };
  });


  // =========================================================================
  // Clipboard Copy
  // =========================================================================
  Alpine.data('clipboard', function () {
    return {
      copied: false,

      copy: function (text) {
        var self = this;
        navigator.clipboard.writeText(text).then(function () {
          self.copied = true;
          setTimeout(function () { self.copied = false; }, 2000);
        }).catch(function (err) {
          console.error('Copy failed:', err);
        });
      }
    };
  });


  // =========================================================================
  // File Upload with Drag & Drop
  // =========================================================================
  Alpine.data('fileUpload', function () {
    return {
      dragging: false,
      file: null,
      files: [],
      multiple: false,

      handleDrop: function (event) {
        this.dragging = false;
        var droppedFiles = event.dataTransfer.files;
        if (this.multiple) {
          this.files = Array.from(droppedFiles);
        } else {
          this.file = droppedFiles[0];
        }
      },

      handleSelect: function (event) {
        var selectedFiles = event.target.files;
        if (this.multiple) {
          this.files = Array.from(selectedFiles);
        } else {
          this.file = selectedFiles[0];
        }
      },

      removeFile: function (index) {
        if (this.multiple) {
          this.files.splice(index, 1);
        } else {
          this.file = null;
        }
      },

      formatSize: function (bytes) {
        if (bytes === 0) return '0 Bytes';
        var k = 1024;
        var sizes = ['Bytes', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
      }
    };
  });


  // =========================================================================
  // Character Counter
  // =========================================================================
  Alpine.data('charCounter', function (maxLength) {
    return {
      count: 0,
      max: maxLength,

      update: function (event) {
        this.count = event.target.value.length;
      },

      get remaining() {
        return this.max - this.count;
      },

      get isOver() {
        return this.count > this.max;
      }
    };
  });


  // =========================================================================
  // Confirm Action Modal
  // =========================================================================
  Alpine.data('confirmAction', function () {
    return {
      show: false,
      title: '',
      message: '',
      onConfirm: null,
      confirmText: 'Confirmar',
      cancelText: 'Cancelar',
      danger: false,

      ask: function (opts) {
        this.title = opts.title || '';
        this.message = opts.message || '';
        this.onConfirm = opts.onConfirm || null;
        this.confirmText = opts.confirmText || 'Confirmar';
        this.cancelText = opts.cancelText || 'Cancelar';
        this.danger = opts.danger || false;
        this.show = true;
      },

      confirm: function () {
        if (this.onConfirm) {
          this.onConfirm();
        }
        this.close();
      },

      close: function () {
        this.show = false;
        this.onConfirm = null;
      }
    };
  });


  // =========================================================================
  // Toggle (for collapsible sections)
  // =========================================================================
  Alpine.data('toggle', function (initialOpen) {
    return {
      open: initialOpen || false,

      toggle: function () {
        this.open = !this.open;
      }
    };
  });


  // =========================================================================
  // Tabs (client-side, non-HTMX)
  // =========================================================================
  Alpine.data('tabs', function (defaultTab) {
    return {
      activeTab: defaultTab || '',

      isActive: function (tab) {
        return this.activeTab === tab;
      },

      setActive: function (tab) {
        this.activeTab = tab;
      }
    };
  });


  // =========================================================================
  // Currency Input (auto-format)
  // =========================================================================
  Alpine.data('currencyInput', function (initialValue) {
    return {
      raw: initialValue || '',

      get formatted() {
        if (!this.raw) return '';
        var num = parseFloat(this.raw);
        if (isNaN(num)) return this.raw;
        return num.toLocaleString('es-DO', { minimumFractionDigits: 2 });
      },

      handleInput: function (event) {
        var value = event.target.value.replace(/[^0-9.]/g, '');
        var parts = value.split('.');
        if (parts.length > 2) {
          value = parts[0] + '.' + parts.slice(1).join('');
        }
        this.raw = value;
      }
    };
  });


  // =========================================================================
  // Phone Input (auto-format DR numbers)
  // =========================================================================
  Alpine.data('phoneInput', function () {
    return {
      raw: '',

      get formatted() {
        var digits = this.raw.replace(/\D/g, '');
        if (digits.length >= 10) {
          return '(' + digits.slice(0, 3) + ') ' + digits.slice(3, 6) + '-' + digits.slice(6, 10);
        }
        return this.raw;
      },

      handleInput: function (event) {
        this.raw = event.target.value.replace(/\D/g, '').slice(0, 10);
      }
    };
  });


  // =========================================================================
  // MapLibre GL Map (lazy-loaded)
  // =========================================================================
  Alpine.data('nitroMap', function (opts) {
    return {
      map: null,
      loaded: false,

      init: function () {
        var self = this;

        // Skip if already loaded
        if (self.loaded) return;
        self.loaded = true;

        // Lazy-load MapLibre GL JS + CSS
        var cssId = 'maplibre-css';
        if (!document.getElementById(cssId)) {
          var link = document.createElement('link');
          link.id = cssId;
          link.rel = 'stylesheet';
          link.href = 'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css';
          document.head.appendChild(link);
        }

        function loadScript(src, cb) {
          if (window.maplibregl) { cb(); return; }
          var s = document.createElement('script');
          s.src = src;
          s.onload = cb;
          document.head.appendChild(s);
        }

        loadScript('https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js', function () {
          self._initMap();
        });
      },

      _initMap: function () {
        var self = this;

        // Validate center coordinates (Dominican Republic default)
        var defaultCenter = [-69.97, 18.47];
        var center = defaultCenter;
        if (opts.center && Array.isArray(opts.center) && opts.center.length === 2) {
          var lon = parseFloat(opts.center[0]);
          var lat = parseFloat(opts.center[1]);
          if (!isNaN(lon) && !isNaN(lat)) {
            center = [lon, lat];
          }
        }

        self.map = new maplibregl.Map({
          container: self.$refs.mapContainer,
          style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
          center: center,
          zoom: opts.zoom || 10
        });

        self.map.addControl(new maplibregl.NavigationControl(), 'top-right');

        // Fetch GeoJSON markers
        if (opts.endpoint) {
          fetch(opts.endpoint, {
            headers: {
              'X-Requested-With': 'XMLHttpRequest'
            }
          })
          .then(function (r) { return r.json(); })
          .then(function (geojson) {
            self._addMarkers(geojson);
          })
          .catch(function (err) {
            console.error('Map data error:', err);
          });
        }
      },

      _escapeHtml: function (text) {
        // Escape HTML to prevent XSS in map popups
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
      },

      _addMarkers: function (geojson) {
        var self = this;
        var bounds = new maplibregl.LngLatBounds();
        var hasPoints = false;

        if (!geojson.features || geojson.features.length === 0) return;

        geojson.features.forEach(function (feature) {
          var coords = feature.geometry.coordinates;
          var props = feature.properties || {};

          // Escape all user-controlled content to prevent XSS
          var safeName = self._escapeHtml(props.name);
          var safeAddress = self._escapeHtml(props.address);
          var safeStatus = self._escapeHtml(props.status);

          // Validate ID is alphanumeric/UUID only for URL safety
          var safeId = props.id && /^[a-zA-Z0-9-]+$/.test(props.id) ? props.id : '';
          var detailUrl = safeId ? '/leasing/property/' + safeId + '/' : '';

          // Status display mapping (use safe escaped value for unknown statuses)
          var statusDisplay = props.status === 'available' ? 'Disponible' :
                              props.status === 'occupied' ? 'Ocupado' : safeStatus;
          var statusClass = props.status === 'available' ? 'bg-green-100 text-green-700' :
                            props.status === 'occupied' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700';

          var popupHtml = '<div class="text-sm" style="min-width: 180px;">' +
            '<p class="font-semibold text-gray-900">' + safeName + '</p>' +
            (safeAddress ? '<p class="text-gray-500 text-xs mt-1">' + safeAddress + '</p>' : '') +
            (props.status ? '<p class="mt-1"><span class="inline-block px-2 py-0.5 text-xs rounded-full ' + statusClass + '">' + statusDisplay + '</span></p>' : '') +
            (detailUrl ? '<a href="' + detailUrl + '" class="inline-flex items-center mt-2 text-xs font-medium text-primary-600 hover:text-primary-700">' +
              'Ver detalle <svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></a>' : '') +
            '</div>';

          // Create marker
          var marker = new maplibregl.Marker({ color: '#09c6af' })
            .setLngLat(coords)
            .setPopup(new maplibregl.Popup({ offset: 25, maxWidth: '250px' }).setHTML(popupHtml))
            .addTo(self.map);

          bounds.extend(coords);
          hasPoints = true;
        });

        // Fit map to markers if we have any
        if (hasPoints) {
          self.map.fitBounds(bounds, { padding: 50, maxZoom: 15 });
        }
      }
    };
  });


  // =========================================================================
  // Form Dirty Check
  // =========================================================================
  Alpine.data('dirtyForm', function () {
    return {
      isDirty: false,
      initialData: '',

      init: function () {
        var self = this;
        this.$nextTick(function () {
          self.initialData = new FormData(self.$el).toString();
        });

        window.addEventListener('beforeunload', function (e) {
          if (self.isDirty) {
            e.preventDefault();
            e.returnValue = '';
          }
        });
      },

      checkDirty: function () {
        var currentData = new FormData(this.$el).toString();
        this.isDirty = currentData !== this.initialData;
      },

      markClean: function () {
        this.isDirty = false;
        this.initialData = new FormData(this.$el).toString();
      }
    };
  });

  // =========================================================================
  // Image Cropper (with Cropper.js)
  // =========================================================================
  Alpine.data('imageCropper', function (opts) {
    return {
      // Config
      aspectRatio: opts.aspectRatio || null,
      minWidth: opts.minWidth || 100,
      maxSizeMB: opts.maxSizeMB || 5,

      // State
      showCropper: false,
      originalImage: null,
      croppedImage: opts.currentImage || '',
      croppedData: '',
      cropper: null,
      loading: false,
      error: '',

      // Parse aspect ratio string to number
      _parseAspectRatio: function () {
        if (!this.aspectRatio || this.aspectRatio === 'free') return null;
        var parts = String(this.aspectRatio).split(':');
        if (parts.length === 2) {
          var w = parseFloat(parts[0]);
          var h = parseFloat(parts[1]);
          if (!isNaN(w) && !isNaN(h) && h !== 0) return w / h;
        }
        var num = parseFloat(this.aspectRatio);
        return isNaN(num) ? null : num;
      },

      // Handle file selection
      handleFileSelect: function (event) {
        var self = this;
        self.error = '';
        var file = event.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
          self.error = 'Por favor selecciona una imagen valida.';
          event.target.value = '';
          return;
        }

        // Validate file size
        var sizeMB = file.size / (1024 * 1024);
        if (sizeMB > self.maxSizeMB) {
          self.error = 'La imagen es muy grande. Maximo ' + self.maxSizeMB + ' MB.';
          event.target.value = '';
          return;
        }

        // Read file and open cropper
        var reader = new FileReader();
        reader.onload = function (e) {
          self.originalImage = e.target.result;
          self.showCropper = true;
          self.$nextTick(function () {
            self._initCropper();
          });
        };
        reader.readAsDataURL(file);
      },

      // Initialize Cropper.js (lazy load from CDN)
      _initCropper: function () {
        var self = this;
        self.loading = true;

        function initWhenReady() {
          var imgElement = self.$refs.cropImage;
          if (!imgElement || typeof Cropper === 'undefined') {
            setTimeout(initWhenReady, 50);
            return;
          }

          // Destroy existing cropper if any
          if (self.cropper) {
            self.cropper.destroy();
          }

          self.cropper = new Cropper(imgElement, {
            aspectRatio: self._parseAspectRatio(),
            viewMode: 1,
            dragMode: 'move',
            autoCropArea: 0.9,
            responsive: true,
            restore: false,
            guides: true,
            center: true,
            highlight: true,
            cropBoxMovable: true,
            cropBoxResizable: true,
            toggleDragModeOnDblclick: false,
            minCropBoxWidth: self.minWidth,
            minCropBoxHeight: self.minWidth,
            ready: function () {
              self.loading = false;
            }
          });
        }

        // Lazy load Cropper.js CSS and JS
        var cssId = 'cropperjs-css';
        if (!document.getElementById(cssId)) {
          var link = document.createElement('link');
          link.id = cssId;
          link.rel = 'stylesheet';
          link.href = 'https://unpkg.com/cropperjs@1.6.2/dist/cropper.min.css';
          document.head.appendChild(link);
        }

        if (typeof Cropper === 'undefined') {
          var script = document.createElement('script');
          script.src = 'https://unpkg.com/cropperjs@1.6.2/dist/cropper.min.js';
          script.onload = initWhenReady;
          document.head.appendChild(script);
        } else {
          initWhenReady();
        }
      },

      // Apply crop and get result
      applyCrop: function () {
        var self = this;
        if (!self.cropper) return;

        self.loading = true;

        // Get cropped canvas
        var canvas = self.cropper.getCroppedCanvas({
          minWidth: self.minWidth,
          maxWidth: 2048,
          maxHeight: 2048,
          imageSmoothingEnabled: true,
          imageSmoothingQuality: 'high'
        });

        if (!canvas) {
          self.error = 'Error al recortar la imagen.';
          self.loading = false;
          return;
        }

        // Convert to base64
        var base64 = canvas.toDataURL('image/jpeg', 0.9);
        self.croppedImage = base64;
        self.croppedData = base64;

        // Cleanup
        self.cropper.destroy();
        self.cropper = null;
        self.showCropper = false;
        self.originalImage = null;
        self.loading = false;

        // Dispatch event for form integration
        self.$dispatch('image-cropped', { data: base64 });
      },

      // Cancel cropping
      cancelCrop: function () {
        if (this.cropper) {
          this.cropper.destroy();
          this.cropper = null;
        }
        this.showCropper = false;
        this.originalImage = null;
        this.loading = false;
        // Reset file input
        var input = this.$refs.fileInput;
        if (input) input.value = '';
      },

      // Clear the cropped image
      clear: function () {
        this.croppedImage = '';
        this.croppedData = '';
        var input = this.$refs.fileInput;
        if (input) input.value = '';
        this.$dispatch('image-cleared');
      },

      // Rotate image
      rotate: function (degrees) {
        if (this.cropper) {
          this.cropper.rotate(degrees);
        }
      },

      // Zoom image
      zoom: function (ratio) {
        if (this.cropper) {
          this.cropper.zoom(ratio);
        }
      },

      // Reset crop box
      reset: function () {
        if (this.cropper) {
          this.cropper.reset();
        }
      }
    };
  });


  // =========================================================================
  // Photo Gallery with Lightbox
  // =========================================================================
  Alpine.data('photoGallery', function (photosData) {
    return {
      photos: photosData || [],
      currentIndex: 0,
      lightboxOpen: false,
      touchStartX: 0,
      touchEndX: 0,

      init: function () {
        var self = this;

        // Keyboard navigation
        document.addEventListener('keydown', function (e) {
          if (!self.lightboxOpen) return;

          if (e.key === 'Escape') {
            self.closeLightbox();
          } else if (e.key === 'ArrowRight') {
            self.next();
          } else if (e.key === 'ArrowLeft') {
            self.prev();
          }
        });
      },

      openLightbox: function (index) {
        this.currentIndex = index;
        this.lightboxOpen = true;
        document.body.style.overflow = 'hidden';
      },

      closeLightbox: function () {
        this.lightboxOpen = false;
        document.body.style.overflow = '';
      },

      next: function () {
        if (this.photos.length === 0) return;
        this.currentIndex = (this.currentIndex + 1) % this.photos.length;
      },

      prev: function () {
        if (this.photos.length === 0) return;
        this.currentIndex = (this.currentIndex - 1 + this.photos.length) % this.photos.length;
      },

      goTo: function (index) {
        this.currentIndex = index;
      },

      get currentPhoto() {
        return this.photos[this.currentIndex] || {};
      },

      // Touch handlers for swipe gestures
      handleTouchStart: function (e) {
        this.touchStartX = e.touches[0].clientX;
      },

      handleTouchMove: function (e) {
        this.touchEndX = e.touches[0].clientX;
      },

      handleTouchEnd: function () {
        var swipeThreshold = 50;
        var diff = this.touchStartX - this.touchEndX;

        if (Math.abs(diff) > swipeThreshold) {
          if (diff > 0) {
            // Swiped left - go to next
            this.next();
          } else {
            // Swiped right - go to prev
            this.prev();
          }
        }

        this.touchStartX = 0;
        this.touchEndX = 0;
      }
    };
  });


  // =========================================================================
  // Global Search (Cmd+K / Ctrl+K)
  // =========================================================================
  Alpine.data('globalSearch', function () {
    return {
      open: false,
      query: '',
      loading: false,
      results: [],
      recentSearches: [],
      selectedIndex: 0,
      debounceTimer: null,
      minChars: 2,

      init: function () {
        var self = this;

        // Load recent searches from localStorage
        try {
          var stored = localStorage.getItem('statuos_recent_searches');
          if (stored) {
            self.recentSearches = JSON.parse(stored).slice(0, 5);
          }
        } catch (e) {
          self.recentSearches = [];
        }

        // Global keyboard shortcuts
        document.addEventListener('keydown', function (e) {
          // Open with Cmd+K or Ctrl+K
          if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            self.toggle();
          }
          // Close with Escape
          if (e.key === 'Escape' && self.open) {
            self.close();
          }
        });
      },

      toggle: function () {
        if (this.open) {
          this.close();
        } else {
          this.openModal();
        }
      },

      openModal: function () {
        var self = this;
        this.open = true;
        this.query = '';
        this.results = [];
        this.selectedIndex = 0;
        // Focus input after modal opens
        this.$nextTick(function () {
          var input = document.getElementById('global-search-input');
          if (input) input.focus();
        });
      },

      close: function () {
        this.open = false;
        this.query = '';
        this.results = [];
        this.loading = false;
      },

      onInput: function () {
        var self = this;
        self.selectedIndex = 0;

        // Clear previous timer
        if (self.debounceTimer) {
          clearTimeout(self.debounceTimer);
        }

        // Don't search if query is too short
        if (self.query.length < self.minChars) {
          self.results = [];
          self.loading = false;
          return;
        }

        self.loading = true;

        // Debounce search (300ms)
        self.debounceTimer = setTimeout(function () {
          self.performSearch();
        }, 300);
      },

      performSearch: function () {
        var self = this;

        fetch('/api/search/?q=' + encodeURIComponent(self.query), {
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(function (response) {
          return response.json();
        })
        .then(function (data) {
          self.results = data.results || [];
          self.loading = false;
        })
        .catch(function (err) {
          console.error('Search error:', err);
          self.results = [];
          self.loading = false;
        });
      },

      onKeydown: function (e) {
        var totalItems = this.getTotalItems();

        if (e.key === 'ArrowDown') {
          e.preventDefault();
          if (this.selectedIndex < totalItems - 1) {
            this.selectedIndex++;
          } else {
            this.selectedIndex = 0;
          }
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          if (this.selectedIndex > 0) {
            this.selectedIndex--;
          } else {
            this.selectedIndex = totalItems - 1;
          }
        } else if (e.key === 'Enter') {
          e.preventDefault();
          this.selectCurrent();
        }
      },

      getTotalItems: function () {
        var count = 0;
        for (var i = 0; i < this.results.length; i++) {
          count += this.results[i].items.length;
        }
        return count;
      },

      getItemAtIndex: function (index) {
        var count = 0;
        for (var i = 0; i < this.results.length; i++) {
          for (var j = 0; j < this.results[i].items.length; j++) {
            if (count === index) {
              return this.results[i].items[j];
            }
            count++;
          }
        }
        return null;
      },

      isSelected: function (groupIndex, itemIndex) {
        var count = 0;
        for (var i = 0; i < groupIndex; i++) {
          count += this.results[i].items.length;
        }
        return count + itemIndex === this.selectedIndex;
      },

      getTotalItemsBeforeGroup: function (groupIndex) {
        var count = 0;
        for (var i = 0; i < groupIndex; i++) {
          count += this.results[i].items.length;
        }
        return count;
      },

      selectCurrent: function () {
        var item = this.getItemAtIndex(this.selectedIndex);
        if (item && item.url) {
          this.navigateTo(item);
        }
      },

      navigateTo: function (item) {
        // Save to recent searches
        this.addToRecent(item);

        // Navigate
        window.location.href = item.url;
        this.close();
      },

      addToRecent: function (item) {
        var self = this;

        // Remove if already exists
        self.recentSearches = self.recentSearches.filter(function (r) {
          return r.url !== item.url;
        });

        // Add to beginning
        self.recentSearches.unshift({
          title: item.title,
          subtitle: item.subtitle,
          url: item.url,
          type: item.type,
          icon: item.icon
        });

        // Keep only 5 recent
        self.recentSearches = self.recentSearches.slice(0, 5);

        // Save to localStorage
        try {
          localStorage.setItem('statuos_recent_searches', JSON.stringify(self.recentSearches));
        } catch (e) {
          // Ignore storage errors
        }
      },

      clearRecent: function () {
        this.recentSearches = [];
        try {
          localStorage.removeItem('statuos_recent_searches');
        } catch (e) {
          // Ignore storage errors
        }
      },

      getTypeIcon: function (type) {
        var icons = {
          'tenant': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>',
          'property': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>',
          'landlord': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>',
          'ticket': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>'
        };
        return icons[type] || icons['property'];
      },

      getTypeColor: function (type) {
        var colors = {
          'tenant': 'text-blue-600 bg-blue-100',
          'property': 'text-primary-600 bg-primary-100',
          'landlord': 'text-purple-600 bg-purple-100',
          'ticket': 'text-orange-600 bg-orange-100'
        };
        return colors[type] || 'text-gray-600 bg-gray-100';
      }
    };
  });


  // =========================================================================
  // Inspection Checklist Component
  // =========================================================================
  Alpine.data('inspectionChecklist', function (opts) {
    return {
      inspectionId: opts.inspectionId || '',
      saving: false,
      lastSaved: null,
      saveTimer: null,
      itemConditions: {},
      itemNotes: {},
      pendingUpdates: [],

      // Gallery state
      galleryOpen: false,
      galleryPhotos: [],
      galleryIndex: 0,
      touchStartX: 0,
      touchEndX: 0,

      init: function () {
        var self = this;

        // Load any pending updates from localStorage (offline support prep)
        self._loadPendingUpdates();

        // Auto-sync pending updates when online
        window.addEventListener('online', function () {
          self._syncPendingUpdates();
        });
      },

      // Get condition class for a button
      getConditionClass: function (itemId, condition, baseClass) {
        var currentCondition = this.itemConditions[itemId];
        if (currentCondition === condition) {
          return baseClass + ' ring-2 ring-offset-1';
        }
        return 'bg-surface-100 text-surface-600 hover:bg-surface-200';
      },

      // Get item notes from local state
      getItemNotes: function (itemId) {
        return this.itemNotes[itemId] || '';
      },

      // Set item notes in local state
      setItemNotes: function (itemId, notes) {
        this.itemNotes[itemId] = notes;
      },

      // Update condition via API
      updateCondition: function (itemId, condition) {
        var self = this;

        // Update local state immediately for responsive UI
        self.itemConditions[itemId] = condition;
        self.saving = true;

        // CSRF token
        var csrfToken = self._getCsrfToken();

        fetch('/leasing/inspections/item/' + itemId + '/condition/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ condition: condition })
        })
        .then(function (response) {
          if (!response.ok) throw new Error('Failed to update');
          return response.json();
        })
        .then(function (data) {
          self.saving = false;
          self.lastSaved = new Date();
          setTimeout(function () { self.lastSaved = null; }, 2000);
        })
        .catch(function (err) {
          console.error('Error updating condition:', err);
          self.saving = false;
          // Queue for later sync
          self._queueUpdate({ type: 'condition', itemId: itemId, value: condition });
          // Show error toast
          if (window.NitroToast) {
            window.NitroToast.error('Error al guardar. Se sincronizara automaticamente.');
          }
        });
      },

      // Update notes via API (debounced)
      updateNotes: function (itemId, notes) {
        var self = this;

        // Clear existing timer
        if (self.saveTimer) {
          clearTimeout(self.saveTimer);
        }

        self.saving = true;

        // Debounce the save
        self.saveTimer = setTimeout(function () {
          var csrfToken = self._getCsrfToken();

          fetch('/leasing/inspections/item/' + itemId + '/notes/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
              'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ notes: notes })
          })
          .then(function (response) {
            if (!response.ok) throw new Error('Failed to update');
            return response.json();
          })
          .then(function (data) {
            self.saving = false;
            self.lastSaved = new Date();
            setTimeout(function () { self.lastSaved = null; }, 2000);
          })
          .catch(function (err) {
            console.error('Error updating notes:', err);
            self.saving = false;
            self._queueUpdate({ type: 'notes', itemId: itemId, value: notes });
          });
        }, 500);
      },

      // Upload photo
      uploadPhoto: function (itemId, event) {
        var self = this;
        var file = event.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.type.startsWith('image/')) {
          if (window.NitroToast) {
            window.NitroToast.error('Solo se permiten imagenes.');
          }
          event.target.value = '';
          return;
        }

        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
          if (window.NitroToast) {
            window.NitroToast.error('La imagen es muy grande. Maximo 10 MB.');
          }
          event.target.value = '';
          return;
        }

        self.saving = true;

        var formData = new FormData();
        formData.append('photo', file);

        var csrfToken = self._getCsrfToken();

        fetch('/leasing/inspections/item/' + itemId + '/photo/', {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: formData
        })
        .then(function (response) {
          if (!response.ok) throw new Error('Failed to upload');
          return response.json();
        })
        .then(function (data) {
          self.saving = false;
          self.lastSaved = new Date();
          setTimeout(function () { self.lastSaved = null; }, 2000);

          // Refresh the item via HTMX
          if (typeof htmx !== 'undefined') {
            htmx.ajax('GET', '/leasing/inspections/item/' + itemId + '/', '#item-' + itemId);
          } else {
            // Fallback: reload the page
            window.location.reload();
          }
        })
        .catch(function (err) {
          console.error('Error uploading photo:', err);
          self.saving = false;
          if (window.NitroToast) {
            window.NitroToast.error('Error al subir la foto.');
          }
        });

        // Reset file input
        event.target.value = '';
      },

      // Delete photo
      deletePhoto: function (photoId) {
        var self = this;

        if (!confirm('Eliminar esta foto?')) return;

        self.saving = true;
        var csrfToken = self._getCsrfToken();

        fetch('/leasing/inspections/photo/' + photoId + '/', {
          method: 'DELETE',
          headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
        .then(function (response) {
          if (!response.ok) throw new Error('Failed to delete');
          self.saving = false;
          // Reload page to refresh photos
          window.location.reload();
        })
        .catch(function (err) {
          console.error('Error deleting photo:', err);
          self.saving = false;
          if (window.NitroToast) {
            window.NitroToast.error('Error al eliminar la foto.');
          }
        });
      },

      // Open gallery lightbox
      openGallery: function (itemId, index) {
        var self = this;
        self.galleryIndex = index || 0;

        // Get photos from the DOM for this item
        var container = document.getElementById('item-' + itemId);
        if (container) {
          var imgs = container.querySelectorAll('img[src]');
          self.galleryPhotos = Array.from(imgs).map(function (img) {
            return { url: img.src, alt: img.alt };
          });
        }

        if (self.galleryPhotos.length > 0) {
          self.galleryOpen = true;
          document.body.style.overflow = 'hidden';
        }
      },

      closeGallery: function () {
        this.galleryOpen = false;
        document.body.style.overflow = '';
      },

      nextPhoto: function () {
        if (this.galleryPhotos.length === 0) return;
        this.galleryIndex = (this.galleryIndex + 1) % this.galleryPhotos.length;
      },

      prevPhoto: function () {
        if (this.galleryPhotos.length === 0) return;
        this.galleryIndex = (this.galleryIndex - 1 + this.galleryPhotos.length) % this.galleryPhotos.length;
      },

      get currentGalleryPhoto() {
        return this.galleryPhotos[this.galleryIndex] || { url: '', alt: '' };
      },

      // Touch handlers for swipe gestures
      handleTouchStart: function (e) {
        this.touchStartX = e.touches[0].clientX;
      },

      handleTouchMove: function (e) {
        this.touchEndX = e.touches[0].clientX;
      },

      handleTouchEnd: function () {
        var swipeThreshold = 50;
        var diff = this.touchStartX - this.touchEndX;

        if (Math.abs(diff) > swipeThreshold) {
          if (diff > 0) {
            this.nextPhoto();
          } else {
            this.prevPhoto();
          }
        }

        this.touchStartX = 0;
        this.touchEndX = 0;
      },

      // Helper: Get CSRF token
      _getCsrfToken: function () {
        var tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput) return tokenInput.value;
        var cookieMatch = document.cookie.match(/csrftoken=([^;]+)/);
        return cookieMatch ? cookieMatch[1] : '';
      },

      // Offline support helpers
      _queueUpdate: function (update) {
        this.pendingUpdates.push(update);
        try {
          localStorage.setItem('inspection_pending_' + this.inspectionId, JSON.stringify(this.pendingUpdates));
        } catch (e) {
          console.warn('Could not save to localStorage:', e);
        }
      },

      _loadPendingUpdates: function () {
        try {
          var stored = localStorage.getItem('inspection_pending_' + this.inspectionId);
          if (stored) {
            this.pendingUpdates = JSON.parse(stored);
          }
        } catch (e) {
          this.pendingUpdates = [];
        }
      },

      _syncPendingUpdates: function () {
        var self = this;
        if (self.pendingUpdates.length === 0) return;

        var updates = self.pendingUpdates.slice();
        self.pendingUpdates = [];

        updates.forEach(function (update) {
          if (update.type === 'condition') {
            self.updateCondition(update.itemId, update.value);
          } else if (update.type === 'notes') {
            self.updateNotes(update.itemId, update.value);
          }
        });

        try {
          localStorage.removeItem('inspection_pending_' + self.inspectionId);
        } catch (e) {
          // Ignore
        }
      }
    };
  });


  // =========================================================================
  // Inspection Compare Component
  // =========================================================================
  Alpine.data('inspectionCompare', function () {
    return {
      filter: 'all',
      comparisons: {},
      stats: {
        unchanged: 0,
        degraded: 0,
        damaged: 0,
        improved: 0
      },

      // Compare gallery state
      compareGalleryOpen: false,
      compareGalleryPhotos: [],
      compareGalleryIndex: 0,
      compareGalleryType: 'in',

      // Condition severity map
      conditionSeverity: {
        'excellent': 0,
        'good': 1,
        'fair': 2,
        'poor': 3,
        'damaged': 4,
        'missing': 5,
        'na': -1
      },

      conditionColors: {
        'excellent': 'bg-green-100 text-green-800',
        'good': 'bg-blue-100 text-blue-800',
        'fair': 'bg-yellow-100 text-yellow-800',
        'poor': 'bg-orange-100 text-orange-800',
        'damaged': 'bg-red-100 text-red-800',
        'missing': 'bg-purple-100 text-purple-800',
        'na': 'bg-gray-100 text-gray-600'
      },

      init: function () {
        // Stats will be calculated as items register themselves
      },

      // Register a comparison between two conditions
      registerComparison: function (itemId, condition1, condition2) {
        var changeType = this.getChangeType(condition1, condition2);
        this.comparisons[itemId] = { c1: condition1, c2: condition2, changeType: changeType };

        // Update stats
        this._recalculateStats();
      },

      _recalculateStats: function () {
        var stats = { unchanged: 0, degraded: 0, damaged: 0, improved: 0 };

        for (var id in this.comparisons) {
          var comp = this.comparisons[id];
          if (comp.changeType === 'unchanged') stats.unchanged++;
          else if (comp.changeType === 'degraded') stats.degraded++;
          else if (comp.changeType === 'damaged') stats.damaged++;
          else if (comp.changeType === 'improved') stats.improved++;
        }

        this.stats = stats;
      },

      // Determine change type between two conditions
      getChangeType: function (condition1, condition2) {
        var sev1 = this.conditionSeverity[condition1];
        var sev2 = this.conditionSeverity[condition2];

        // N/A handling
        if (sev1 === -1 || sev2 === -1) return 'unchanged';

        if (sev2 > sev1) {
          // Condition got worse
          if (condition2 === 'damaged' || condition2 === 'missing') {
            return 'damaged';
          }
          return 'degraded';
        } else if (sev2 < sev1) {
          return 'improved';
        }
        return 'unchanged';
      },

      // Get CSS class for condition badge
      getConditionColorClass: function (condition) {
        return this.conditionColors[condition] || 'bg-gray-100 text-gray-600';
      },

      // Filter: should show this area?
      shouldShowArea: function (areaId) {
        // If filter is 'all', always show
        if (this.filter === 'all') return true;

        // Check if any items in this area match the filter
        // This is a simplified check - in production you'd want to be more precise
        return true; // For now, show all areas and filter items
      },

      // Filter: should show this item?
      shouldShowItem: function (condition1, condition2) {
        if (this.filter === 'all') return true;

        var changeType = this.getChangeType(condition1, condition2);

        if (this.filter === 'changed') {
          return changeType !== 'unchanged';
        }
        if (this.filter === 'degraded') {
          return changeType === 'degraded';
        }
        if (this.filter === 'damaged') {
          return changeType === 'damaged';
        }

        return true;
      },

      // Open compare gallery
      openCompareGallery: function (itemId, type, index) {
        this.compareGalleryType = type;
        this.compareGalleryIndex = index || 0;

        // Get photos from DOM
        var container = document.getElementById('item-' + itemId);
        if (!container) return;

        var selector = type === 'in' ? '.bg-blue-50\\/50 img' : '.bg-purple-50\\/50 img';
        var imgs = container.querySelectorAll(selector);

        this.compareGalleryPhotos = Array.from(imgs).map(function (img) {
          return { url: img.src, alt: img.alt };
        });

        if (this.compareGalleryPhotos.length > 0) {
          this.compareGalleryOpen = true;
          document.body.style.overflow = 'hidden';
        }
      },

      closeCompareGallery: function () {
        this.compareGalleryOpen = false;
        document.body.style.overflow = '';
      },

      get currentComparePhoto() {
        return this.compareGalleryPhotos[this.compareGalleryIndex] || { url: '', alt: '' };
      }
    };
  });


  // =========================================================================
  // Signature Pad Component
  // =========================================================================
  Alpine.data('signaturePad', function (opts) {
    return {
      // Canvas and context
      canvas: null,
      ctx: null,

      // Drawing state
      isDrawing: false,
      isEmpty: true,
      isSaving: false,
      lastX: 0,
      lastY: 0,

      // Data
      signatureData: '',
      signatureTimestamp: '',

      // Validation
      hasError: false,
      errorMessage: '',

      // Configuration
      lineColor: opts.lineColor || '#000000',
      lineWidth: opts.lineWidth || 2,
      backgroundColor: opts.backgroundColor || '#ffffff',
      name: opts.name || 'signature',
      canvasWidth: opts.width || 400,
      canvasHeight: opts.height || 200,
      required: opts.required !== false,

      // Device pixel ratio for retina support
      dpr: 1,

      init: function () {
        var self = this;
        self.canvas = self.$refs.canvas;

        if (!self.canvas) {
          console.error('Signature pad canvas not found');
          return;
        }

        self.ctx = self.canvas.getContext('2d');

        // Handle high-DPI displays (retina)
        self.dpr = window.devicePixelRatio || 1;
        self.setupCanvas();

        // Handle resize
        self._resizeHandler = function () {
          self.handleResize();
        };
        window.addEventListener('resize', self._resizeHandler);

        // Form validation hook
        var form = self.$el.closest('form');
        if (form) {
          form.addEventListener('submit', function (e) {
            if (!self.validate()) {
              e.preventDefault();
              e.stopPropagation();
            }
          });
        }
      },

      destroy: function () {
        if (this._resizeHandler) {
          window.removeEventListener('resize', this._resizeHandler);
        }
      },

      setupCanvas: function () {
        var self = this;
        var rect = self.canvas.getBoundingClientRect();

        // Set actual size in memory (scaled for retina)
        self.canvas.width = self.canvasWidth * self.dpr;
        self.canvas.height = self.canvasHeight * self.dpr;

        // Scale all drawing operations by the dpr
        self.ctx.scale(self.dpr, self.dpr);

        // Set drawing styles
        self.ctx.fillStyle = self.backgroundColor;
        self.ctx.fillRect(0, 0, self.canvasWidth, self.canvasHeight);
        self.ctx.strokeStyle = self.lineColor;
        self.ctx.lineWidth = self.lineWidth;
        self.ctx.lineCap = 'round';
        self.ctx.lineJoin = 'round';
      },

      handleResize: function () {
        var self = this;
        if (self.isEmpty) {
          self.setupCanvas();
          return;
        }

        // Save current drawing before resize
        var dataUrl = self.canvas.toDataURL();
        var img = new Image();
        img.onload = function () {
          self.setupCanvas();
          // Redraw the saved image
          self.ctx.drawImage(img, 0, 0, self.canvasWidth, self.canvasHeight);
        };
        img.src = dataUrl;
      },

      getCoords: function (e) {
        var rect = this.canvas.getBoundingClientRect();
        var scaleX = this.canvasWidth / rect.width;
        var scaleY = this.canvasHeight / rect.height;
        return {
          x: (e.clientX - rect.left) * scaleX,
          y: (e.clientY - rect.top) * scaleY
        };
      },

      getTouchCoords: function (e) {
        var touch = e.touches[0];
        return this.getCoords(touch);
      },

      startDrawing: function (e) {
        this.isDrawing = true;
        this.hasError = false;
        var coords = this.getCoords(e);
        this.lastX = coords.x;
        this.lastY = coords.y;
        this.ctx.beginPath();
        this.ctx.moveTo(coords.x, coords.y);
      },

      startDrawingTouch: function (e) {
        // Prevent scrolling while signing
        e.preventDefault();
        this.isDrawing = true;
        this.hasError = false;
        var coords = this.getTouchCoords(e);
        this.lastX = coords.x;
        this.lastY = coords.y;
        this.ctx.beginPath();
        this.ctx.moveTo(coords.x, coords.y);
      },

      draw: function (e) {
        if (!this.isDrawing) return;
        var coords = this.getCoords(e);
        this.drawLine(coords.x, coords.y);
      },

      drawTouch: function (e) {
        if (!this.isDrawing) return;
        // Prevent scrolling while drawing
        e.preventDefault();
        var coords = this.getTouchCoords(e);
        this.drawLine(coords.x, coords.y);
      },

      drawLine: function (x, y) {
        this.ctx.lineTo(x, y);
        this.ctx.stroke();
        this.ctx.beginPath();
        this.ctx.moveTo(x, y);
        this.lastX = x;
        this.lastY = y;
        this.isEmpty = false;
      },

      stopDrawing: function () {
        if (this.isDrawing) {
          this.isDrawing = false;
          this.ctx.closePath();
          this.saveSignature();
        }
      },

      confirmClear: function () {
        var self = this;
        if (self.isEmpty) return;

        // Use built-in confirm for simplicity, or dispatch to NitroConfirm
        if (window.NitroConfirm) {
          window.NitroConfirm.ask({
            title: 'Borrar firma',
            message: 'Esta seguro de que desea borrar la firma?',
            confirmText: 'Borrar',
            danger: true,
            onConfirm: function () {
              self.clear();
            }
          });
        } else {
          if (confirm('Esta seguro de que desea borrar la firma?')) {
            self.clear();
          }
        }
      },

      clear: function () {
        var self = this;
        // Reset canvas
        self.ctx.setTransform(1, 0, 0, 1, 0, 0);
        self.ctx.scale(self.dpr, self.dpr);
        self.ctx.fillStyle = self.backgroundColor;
        self.ctx.fillRect(0, 0, self.canvasWidth, self.canvasHeight);
        self.ctx.strokeStyle = self.lineColor;
        self.ctx.lineWidth = self.lineWidth;
        self.ctx.lineCap = 'round';
        self.ctx.lineJoin = 'round';

        self.isEmpty = true;
        self.signatureData = '';
        self.signatureTimestamp = '';
        self.hasError = false;
        self.errorMessage = '';

        // Dispatch event
        self.$dispatch('signature-cleared');
      },

      saveSignature: function () {
        var self = this;
        if (self.isEmpty) {
          self.signatureData = '';
          self.signatureTimestamp = '';
          return;
        }

        self.isSaving = true;

        // Small delay to show saving indicator
        setTimeout(function () {
          self.signatureData = self.canvas.toDataURL('image/png');
          self.signatureTimestamp = new Date().toISOString();
          self.isSaving = false;

          // Dispatch event with signature data
          self.$dispatch('signature-saved', {
            data: self.signatureData,
            timestamp: self.signatureTimestamp
          });
        }, 100);
      },

      validate: function () {
        if (this.required && this.isEmpty) {
          this.hasError = true;
          this.errorMessage = 'La firma es requerida';
          return false;
        }
        this.hasError = false;
        this.errorMessage = '';
        return true;
      },

      // Get signature as Blob for upload
      getBlob: function (callback) {
        var self = this;
        if (self.isEmpty) {
          callback(null);
          return;
        }
        self.canvas.toBlob(callback, 'image/png');
      },

      // Check if signature has content
      hasSignature: function () {
        return !this.isEmpty && this.signatureData !== '';
      }
    };
  });


  // =========================================================================
  // Document Viewer Component
  // =========================================================================
  Alpine.data('documentViewer', function (opts) {
    return {
      // Configuration
      hasPdf: opts.hasPdf || false,
      hasContent: opts.hasContent || false,
      pdfUrl: opts.pdfUrl || '',
      title: opts.title || '',

      // Zoom state
      zoom: 100,
      minZoom: 50,
      maxZoom: 200,
      zoomStep: 10,

      // Content dimensions
      contentWidth: 800,

      // Fullscreen state
      isFullscreen: false,

      init: function () {
        var self = this;

        // Set initial content width based on container
        self.$nextTick(function () {
          self.calculateContentWidth();
        });

        // Handle resize
        window.addEventListener('resize', function () {
          self.calculateContentWidth();
        });

        // Handle fullscreen change
        document.addEventListener('fullscreenchange', function () {
          self.isFullscreen = !!document.fullscreenElement;
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', function (e) {
          // Only handle if this viewer is visible/focused
          if (!self.$el.contains(document.activeElement) && document.activeElement !== document.body) {
            return;
          }

          // Ctrl/Cmd + Plus: Zoom in
          if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
            e.preventDefault();
            self.zoomIn();
          }
          // Ctrl/Cmd + Minus: Zoom out
          if ((e.ctrlKey || e.metaKey) && e.key === '-') {
            e.preventDefault();
            self.zoomOut();
          }
          // Ctrl/Cmd + 0: Reset zoom
          if ((e.ctrlKey || e.metaKey) && e.key === '0') {
            e.preventDefault();
            self.resetZoom();
          }
          // Escape: Exit fullscreen
          if (e.key === 'Escape' && self.isFullscreen) {
            self.exitFullscreen();
          }
        });
      },

      calculateContentWidth: function () {
        var wrapper = this.$refs.contentWrapper;
        if (wrapper) {
          // Calculate based on container width minus padding
          var containerWidth = wrapper.clientWidth - 64; // 32px padding on each side
          this.contentWidth = Math.min(containerWidth, 800);
        }
      },

      zoomIn: function () {
        if (this.zoom < this.maxZoom) {
          this.zoom = Math.min(this.zoom + this.zoomStep, this.maxZoom);
        }
      },

      zoomOut: function () {
        if (this.zoom > this.minZoom) {
          this.zoom = Math.max(this.zoom - this.zoomStep, this.minZoom);
        }
      },

      resetZoom: function () {
        this.zoom = 100;
      },

      fitToWidth: function () {
        var self = this;
        var container = self.$refs.viewerContainer;
        var content = self.$refs.documentContent;

        if (!container || !content) {
          self.zoom = 100;
          return;
        }

        // Calculate zoom to fit width
        var containerWidth = container.clientWidth - 64; // Account for padding
        var contentNaturalWidth = self.contentWidth;
        var fitZoom = Math.floor((containerWidth / contentNaturalWidth) * 100);

        // Clamp to min/max
        self.zoom = Math.max(self.minZoom, Math.min(fitZoom, self.maxZoom));
      },

      print: function () {
        var self = this;

        if (self.hasPdf && self.$refs.pdfFrame) {
          // Print PDF via iframe
          self.$refs.pdfFrame.contentWindow.print();
        } else if (self.hasContent) {
          // Print HTML content
          var content = self.$refs.documentContent;
          if (!content) return;

          var printWindow = window.open('', '_blank');
          printWindow.document.write('<html><head><title>' + (self.title || 'Document') + '</title>');
          printWindow.document.write('<style>');
          printWindow.document.write('body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 20mm; }');
          printWindow.document.write('.document-content { max-width: 170mm; margin: 0 auto; }');
          printWindow.document.write('@media print { @page { margin: 15mm; } }');
          printWindow.document.write('</style>');
          printWindow.document.write('</head><body>');
          printWindow.document.write('<div class="document-content">' + content.innerHTML + '</div>');
          printWindow.document.write('</body></html>');
          printWindow.document.close();
          printWindow.focus();

          // Delay print to allow styles to load
          setTimeout(function () {
            printWindow.print();
            printWindow.close();
          }, 250);
        }
      },

      toggleFullscreen: function () {
        if (this.isFullscreen) {
          this.exitFullscreen();
        } else {
          this.enterFullscreen();
        }
      },

      enterFullscreen: function () {
        var container = this.$refs.viewerContainer;
        if (!container) return;

        if (container.requestFullscreen) {
          container.requestFullscreen();
        } else if (container.webkitRequestFullscreen) {
          container.webkitRequestFullscreen();
        } else if (container.msRequestFullscreen) {
          container.msRequestFullscreen();
        }
      },

      exitFullscreen: function () {
        if (document.exitFullscreen) {
          document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
          document.msExitFullscreen();
        }
      }
    };
  });


  // =========================================================================
  // Inline Create Component (searchable select with quick-create)
  // =========================================================================
  Alpine.data('inlineCreate', function (config) {
    return {
      // State
      open: false,
      search: '',
      selectedValue: config.value || '',
      selectedLabel: config.label || '',
      options: config.options || [],
      filteredOptions: [],
      searchUrl: config.searchUrl || '',
      createUrl: config.createUrl || '',
      modelName: config.modelName || 'elemento',
      displayField: config.displayField || 'name',
      valueField: config.valueField || 'id',
      loading: false,
      creating: false,
      showCreateForm: false,
      highlightIndex: -1,
      error: '',
      createFormHtml: '',

      init: function () {
        var self = this;
        this.filteredOptions = this.options;
        if (this.selectedValue) {
          var found = this.options.find(function (o) { return o.value === self.selectedValue; });
          if (found) this.selectedLabel = found.label;
        }
      },

      filter: function () {
        var self = this;
        self.highlightIndex = -1;
        self.error = '';

        if (self.searchUrl) {
          // Server-side search
          self.loading = true;
          fetch(self.searchUrl + (self.searchUrl.indexOf('?') !== -1 ? '&' : '?') + 'q=' + encodeURIComponent(self.search), {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          })
            .then(function (r) { return r.json(); })
            .then(function (data) {
              self.filteredOptions = data.results || [];
              self.loading = false;
            })
            .catch(function () {
              self.loading = false;
              self.error = 'Error al buscar';
            });
        } else {
          // Client-side search
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
        this.showCreateForm = false;
        this.filteredOptions = this.options;
        this.$refs.hiddenInput.value = value;
        this.$refs.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
      },

      clear: function () {
        this.selectedValue = '';
        this.selectedLabel = '';
        this.search = '';
        this.showCreateForm = false;
        this.filteredOptions = this.options;
        this.$refs.hiddenInput.value = '';
        this.$refs.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
      },

      openCreateForm: function () {
        var self = this;
        self.showCreateForm = true;
        self.open = false;
        self.error = '';

        // Load the create form HTML if createUrl is provided
        if (self.createUrl && !self.createFormHtml) {
          self.loading = true;
          fetch(self.createUrl, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
          })
            .then(function (r) { return r.text(); })
            .then(function (html) {
              self.createFormHtml = html;
              self.loading = false;
              // Initialize any Alpine components in the loaded form
              self.$nextTick(function () {
                var formContainer = self.$refs.createFormContainer;
                if (formContainer && window.Alpine) {
                  Alpine.initTree(formContainer);
                }
              });
            })
            .catch(function () {
              self.loading = false;
              self.error = 'Error al cargar el formulario';
            });
        }
      },

      closeCreateForm: function () {
        this.showCreateForm = false;
        this.error = '';
      },

      submitCreate: function (event) {
        var self = this;
        event.preventDefault();

        if (!self.createUrl) {
          self.error = 'URL de creacion no configurada';
          return;
        }

        var form = event.target;
        var formData = new FormData(form);

        self.creating = true;
        self.error = '';

        // Get CSRF token
        var csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (!csrfToken) {
          csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
        }
        var headers = { 'X-Requested-With': 'XMLHttpRequest' };
        if (csrfToken) {
          headers['X-CSRFToken'] = csrfToken.content || csrfToken.value;
        }

        fetch(self.createUrl, {
          method: 'POST',
          headers: headers,
          body: formData
        })
          .then(function (response) {
            if (!response.ok) {
              return response.json().then(function (data) {
                throw new Error(data.error || 'Error al crear');
              });
            }
            return response.json();
          })
          .then(function (data) {
            self.creating = false;
            if (data.success) {
              // Add new option to the list
              var newOption = {
                value: String(data[self.valueField] || data.id),
                label: data[self.displayField] || data.name || data.label
              };
              self.options.push(newOption);
              self.filteredOptions = self.options;
              // Select the newly created item
              self.select(newOption.value, newOption.label);
              self.showCreateForm = false;
              self.createFormHtml = ''; // Reset form for next use
              // Show success toast
              if (window.NitroToast) {
                window.NitroToast.success(self.modelName + ' creado exitosamente');
              }
            } else {
              self.error = data.error || 'Error al crear ' + self.modelName;
            }
          })
          .catch(function (err) {
            self.creating = false;
            self.error = err.message || 'Error al crear ' + self.modelName;
          });
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
          if (this.showCreateForm) {
            this.closeCreateForm();
          } else {
            this.open = false;
          }
        }
      }
    };
  });


});


// =============================================================================
// HTMX Extensions
// =============================================================================

// Handle confirm-action events from modals
document.addEventListener('DOMContentLoaded', function () {
  document.body.addEventListener('confirm-action', function (event) {
    var action = event.detail.action;
    var method = event.detail.method;
    if (action && method && typeof htmx !== 'undefined') {
      htmx.ajax(method.toUpperCase(), action, { target: 'body' });
    }
  });
});
