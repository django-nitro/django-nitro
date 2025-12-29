# SEO-Friendly Template Tags

For public-facing content that needs search engine optimization (SEO), Nitro provides special template tags that render static HTML for crawlers while maintaining Alpine.js reactivity.

## Why SEO Matters

Traditional Alpine.js templates are not SEO-friendly:

```html
<!-- ❌ Not SEO-friendly -->
<template x-for="product in products" :key="product.id">
    <div class="card">
        <h2 x-text="product.name"></h2>
        <p x-text="product.description"></p>
    </div>
</template>
```

**What search engines see:** Nothing! The `<template>` tag is not rendered, and `x-text` bindings are empty until JavaScript loads.

**The problem:**
- Google can't index your products
- No rich snippets in search results
- Poor SEO rankings for public content

## The Solution: Hybrid Rendering

Nitro's SEO template tags render content **twice**:
1. **Static HTML** - For search engines and initial page load
2. **Alpine.js bindings** - For reactivity and updates

**Result:** Search engines see your content, users get reactivity.

---

## Template Tags

### {% nitro_scripts %}

Load Nitro CSS and JavaScript files.

```html
{% load nitro_tags %}
<!DOCTYPE html>
<html>
<head>
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <!-- Loads nitro.css and nitro.js -->
    {% nitro_scripts %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
```

**Expands to:**
```html
<link rel="stylesheet" href="/static/nitro/nitro.css">
<script defer src="/static/nitro/nitro.js"></script>
```

**Benefits:**
- Includes toast notification styles
- Single tag instead of two `{% static %}` calls
- Automatic versioning if you use ManifestStaticFilesStorage

---

### {% nitro_text %}

Render text content that's both static (SEO) and reactive (Alpine.js).

#### Basic Usage

```html
{% load nitro_tags %}

<!-- Traditional Alpine (not SEO-friendly) -->
<h1 x-text="product.name"></h1>
<!-- Search engines see: <h1 x-text="product.name"></h1> (empty) -->

<!-- Nitro SEO tag -->
<h1>{% nitro_text 'product.name' %}</h1>
<!-- Search engines see: <h1><span x-text="product.name">Gaming Laptop</span></h1> -->
```

#### How It Works

1. Server renders the actual value from state: `"Gaming Laptop"`
2. Wraps in `<span>` with `x-text` binding
3. Search engines index the static text
4. When state changes, Alpine updates the content

#### Example: Product Card

```html
{% load nitro_tags %}

<div class="product-card">
    <h2>{% nitro_text 'item.name' %}</h2>
    <p class="price">${% nitro_text 'item.price' %}</p>
    <p class="description">{% nitro_text 'item.description' %}</p>
    <span class="stock">{% nitro_text 'item.stock' %} in stock</span>
</div>
```

**Rendered HTML:**
```html
<div class="product-card">
    <h2><span x-text="item.name">Gaming Laptop RTX 4090</span></h2>
    <p class="price">$<span x-text="item.price">1299.99</span></p>
    <p class="description"><span x-text="item.description">High-performance gaming laptop...</span></p>
    <span class="stock"><span x-text="item.stock">15</span> in stock</span>
</div>
```

**SEO benefit:** Google sees "Gaming Laptop RTX 4090", "$1299.99", full description, and stock count.

#### When to Use

✅ **Use nitro_text for:**
- Product names, prices, descriptions
- Blog post titles and content
- Property listings (address, price, features)
- Public profiles (names, bios)
- Any text you want indexed by Google

❌ **Don't use for:**
- Admin panels (not crawled)
- Authenticated-only content
- Dynamic UI labels (buttons, tooltips)
- Content that changes frequently client-side

---

### {% nitro_for %}

Render list items on the server for SEO while keeping Alpine.js reactivity.

#### Basic Usage

```html
{% load nitro_tags %}

<!-- Traditional Alpine (not SEO-friendly) -->
<template x-for="product in products" :key="product.id">
    <div class="card">
        <h3 x-text="product.name"></h3>
    </div>
</template>
<!-- Crawlers see: Nothing (template is not rendered) -->

<!-- Nitro SEO tag -->
{% nitro_for 'products' as 'product' %}
    <div class="card">
        <h3>{% nitro_text 'product.name' %}</h3>
        <p>{% nitro_text 'product.description' %}</p>
    </div>
{% end_nitro_for %}
<!-- Crawlers see: All product cards with real content -->
```

#### How It Works

1. **Server renders all items** - Full HTML with actual values
2. **Wraps in hidden div** - Uses `x-show="false"` to hide static content
3. **Adds Alpine template** - `<template x-for>` for reactivity
4. **Search engines index** - Static content
5. **Alpine shows reactive version** - When JavaScript loads

**Generated HTML:**
```html
<!-- Static content (hidden when Alpine loads, visible for SEO) -->
<div x-show="false" class="nitro-seo-content">
    <div class="card">
        <h3><span x-text="product.name">Product 1</span></h3>
        <p><span x-text="product.description">Description 1</span></p>
    </div>
    <div class="card">
        <h3><span x-text="product.name">Product 2</span></h3>
        <p><span x-text="product.description">Description 2</span></p>
    </div>
    <!-- ... all products ... -->
</div>

<!-- Alpine reactive template -->
<template x-for="(product, index) in products" :key="product.id || index">
    <div class="card">
        <h3><span x-text="product.name">Product 1</span></h3>
        <p><span x-text="product.description">Description 1</span></p>
    </div>
</template>
```

#### Complete Example: Property Listings

```python
# components/property_list.py
from pydantic import BaseModel
from nitro import BaseListComponent, BaseListState, register_component
from properties.models import Property


class PropertySchema(BaseModel):
    id: int
    title: str
    address: str
    price: float
    bedrooms: int
    bathrooms: float
    image_url: str

    class Config:
        from_attributes = True


class PropertyListState(BaseListState):
    items: list[PropertySchema] = []


@register_component
class PropertyList(BaseListComponent[PropertyListState]):
    template_name = "components/property_list.html"
    state_class = PropertyListState
    model = Property

    search_fields = ['title', 'address', 'city']
    per_page = 20
    order_by = '-created_at'
```

```html
<!-- templates/components/property_list.html -->
{% load nitro_tags %}

<div class="property-list">
    <h1>Available Properties</h1>

    <!-- Search bar -->
    <input
        type="text"
        x-model="search"
        @input.debounce.300ms="call('search_items', {search: $el.value})"
        placeholder="Search by title, address, or city..."
        class="search-input"
    >

    <!-- SEO-friendly property grid -->
    <div class="grid">
        {% nitro_for 'items' as 'item' %}
            <div class="property-card">
                <img :src="item.image_url" alt="Property image" class="property-image">

                <div class="property-info">
                    <h2>{% nitro_text 'item.title' %}</h2>
                    <p class="address">{% nitro_text 'item.address' %}</p>

                    <div class="price">
                        ${% nitro_text 'item.price' %}
                    </div>

                    <div class="features">
                        <span>{% nitro_text 'item.bedrooms' %} bed</span>
                        <span>{% nitro_text 'item.bathrooms' %} bath</span>
                    </div>

                    <button @click="call('view_details', {id: item.id})">
                        View Details
                    </button>
                </div>
            </div>
        {% end_nitro_for %}
    </div>

    <!-- Pagination -->
    <div class="pagination" x-show="num_pages > 1">
        <button
            @click="call('previous_page')"
            :disabled="!has_previous || isLoading"
        >
            Previous
        </button>

        <span>Page {% nitro_text 'page' %} of {% nitro_text 'num_pages' %}</span>

        <button
            @click="call('next_page')"
            :disabled="!has_next || isLoading"
        >
            Next
        </button>
    </div>
</div>
```

**SEO Result:**
- Google indexes all property titles, addresses, prices
- Rich snippets in search results
- Property images appear in Google Images
- Each property can be a separate search result

#### When to Use

✅ **Use nitro_for for:**
- Product listings (e-commerce)
- Property/real estate listings
- Blog post archives
- Public search results
- Directory listings (businesses, users, etc.)
- Any public list you want indexed

❌ **Don't use for:**
- Private user dashboards
- Admin panels
- Internal tools
- Lists that change constantly client-side
- Lists behind authentication

---

## Complete Example: E-Commerce Product Page

### Component

```python
# products/components/product_catalog.py
from pydantic import BaseModel
from nitro import BaseListComponent, BaseListState, register_component
from products.models import Product


class ProductSchema(BaseModel):
    id: int
    name: str
    slug: str
    price: float
    description: str
    rating: float
    review_count: int
    in_stock: bool
    image_url: str

    class Config:
        from_attributes = True


class ProductCatalogState(BaseListState):
    items: list[ProductSchema] = []


@register_component
class ProductCatalog(BaseListComponent[ProductCatalogState]):
    template_name = "components/product_catalog.html"
    state_class = ProductCatalogState
    model = Product

    search_fields = ['name', 'description', 'category__name']
    per_page = 24
    order_by = '-created_at'
```

### Template

```html
<!-- templates/components/product_catalog.html -->
{% load nitro_tags %}

<div class="catalog">
    <!-- SEO: Page title -->
    <h1>Our Products</h1>

    <!-- Search (functional, but not critical for SEO) -->
    <div class="search-bar">
        <input
            type="text"
            x-model="search"
            @input.debounce.300ms="call('search_items', {search: $el.value})"
            placeholder="Search products..."
        >
    </div>

    <!-- SEO-friendly product grid -->
    <div class="product-grid">
        {% nitro_for 'items' as 'item' %}
            <article class="product-card" itemscope itemtype="https://schema.org/Product">
                <!-- SEO: Structured data for Google -->
                <meta itemprop="name" content="{% nitro_text 'item.name' %}">
                <meta itemprop="description" content="{% nitro_text 'item.description' %}">

                <a :href="`/products/${item.slug}/`" itemprop="url">
                    <img
                        :src="item.image_url"
                        :alt="item.name"
                        itemprop="image"
                        class="product-image"
                    >
                </a>

                <div class="product-info">
                    <h2 itemprop="name">
                        {% nitro_text 'item.name' %}
                    </h2>

                    <p class="description" itemprop="description">
                        {% nitro_text 'item.description' %}
                    </p>

                    <div class="price" itemprop="offers" itemscope itemtype="https://schema.org/Offer">
                        <meta itemprop="priceCurrency" content="USD">
                        <span itemprop="price">${% nitro_text 'item.price' %}</span>
                        <meta itemprop="availability" content="https://schema.org/InStock">
                    </div>

                    <div class="rating" itemprop="aggregateRating" itemscope itemtype="https://schema.org/AggregateRating">
                        <span itemprop="ratingValue">{% nitro_text 'item.rating' %}</span> ⭐
                        <span>(<span itemprop="reviewCount">{% nitro_text 'item.review_count' %}</span> reviews)</span>
                    </div>

                    <template x-if="item.in_stock">
                        <button
                            @click="call('add_to_cart', {product_id: item.id})"
                            class="btn-primary"
                        >
                            Add to Cart
                        </button>
                    </template>

                    <template x-if="!item.in_stock">
                        <span class="out-of-stock">Out of Stock</span>
                    </template>
                </div>
            </article>
        {% end_nitro_for %}
    </div>

    <!-- Pagination with SEO-friendly page numbers -->
    <nav class="pagination" x-show="num_pages > 1">
        <a
            @click.prevent="call('previous_page')"
            :class="{'disabled': !has_previous}"
            href="?page={% nitro_text 'page' %}"
        >
            Previous
        </a>

        <span>Page {% nitro_text 'page' %} of {% nitro_text 'num_pages' %}</span>

        <a
            @click.prevent="call('next_page')"
            :class="{'disabled': !has_next}"
            href="?page={% nitro_text 'page' %}"
        >
            Next
        </a>
    </nav>
</div>
```

**SEO Benefits:**
- ✅ Google indexes all product names, prices, descriptions
- ✅ Star ratings appear in search results
- ✅ Products appear in Google Shopping
- ✅ Rich snippets with price and availability
- ✅ All product images indexed

---

## Performance Considerations

### Server-Side Rendering Cost

SEO tags render content twice (static + Alpine template), which increases HTML size:

```html
<!-- Without SEO tags: ~500 bytes per item -->
<template x-for="item in items">
    <div x-text="item.name"></div>
</template>

<!-- With SEO tags: ~1KB per item (2x size) -->
{% nitro_for 'items' as 'item' %}
    <div>{% nitro_text 'item.name' %}</div>
{% end_nitro_for %}
```

**Best practices:**
- ✅ Use for public content (< 100 items per page)
- ✅ Combine with pagination to limit items
- ❌ Avoid for huge lists (500+ items) - use traditional Alpine
- ❌ Don't use for private/authenticated pages

### Pagination Helps SEO

```python
@register_component
class ProductCatalog(BaseListComponent[ProductCatalogState]):
    per_page = 24  # ✅ Limit to 24 items per page

    # Google can crawl:
    # /products/?page=1 (24 products)
    # /products/?page=2 (24 more products)
    # etc.
```

---

## Best Practices

### 1. Use SEO Tags for Public Content Only

```python
# ✅ Good - Public product catalog
class ProductCatalog(BaseListComponent):
    template_name = "products/catalog.html"  # Uses {% nitro_for %}

# ❌ Bad - Admin dashboard
class AdminDashboard(BaseListComponent):
    template_name = "admin/dashboard.html"  # Use regular x-for
```

### 2. Combine with Schema.org Markup

```html
{% nitro_for 'items' as 'item' %}
    <div itemscope itemtype="https://schema.org/Product">
        <h2 itemprop="name">{% nitro_text 'item.name' %}</h2>
        <span itemprop="price">{% nitro_text 'item.price' %}</span>
    </div>
{% end_nitro_for %}
```

### 3. Use Semantic HTML

```html
<!-- ✅ Good - Semantic and SEO-friendly -->
{% nitro_for 'articles' as 'article' %}
    <article>
        <h2>{% nitro_text 'article.title' %}</h2>
        <time datetime="...">{% nitro_text 'article.date' %}</time>
        <p>{% nitro_text 'article.summary' %}</p>
    </article>
{% end_nitro_for %}

<!-- ❌ Bad - Generic divs -->
{% nitro_for 'articles' as 'article' %}
    <div>
        <div>{% nitro_text 'article.title' %}</div>
    </div>
{% end_nitro_for %}
```

### 4. Add Alt Text to Images

```html
{% nitro_for 'products' as 'product' %}
    <img
        :src="product.image_url"
        :alt="product.name"  <!-- SEO: Image description -->
        loading="lazy"  <!-- Performance: Lazy load -->
    >
{% end_nitro_for %}
```

## See Also

- [API Reference: Template Tags](../api-reference.md#template-tags-v040)
- [BaseListComponent](../components/base-list-component.md)
- [Performance Optimization](smart-updates.md)
