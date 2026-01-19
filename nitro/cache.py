"""
Django Nitro Cache Module (v0.7.0)

Provides component state and HTML caching for improved performance.

Features:
- State caching: Reduces serialization overhead between requests
- HTML caching: Caches rendered output when state is unchanged
- Automatic cache invalidation on state changes
- Configurable TTL per component

Usage:
    from nitro import NitroComponent
    from nitro.cache import CacheMixin

    class MyComponent(CacheMixin, NitroComponent[MyState]):
        cache_enabled = True
        cache_ttl = 300  # 5 minutes

        def get_cache_key_parts(self):
            # Optional: customize cache key
            return [self.request.user.id, self.some_filter]
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_state_hash(state_dict: dict) -> str:
    """Generate a hash of the state dictionary for cache invalidation."""
    # Sort keys for consistent hashing
    state_str = json.dumps(state_dict, sort_keys=True, default=str)
    return hashlib.md5(state_str.encode()).hexdigest()[:16]


class CacheMixin:
    """
    Mixin that adds caching capabilities to NitroComponent.

    Add this mixin BEFORE NitroComponent in the inheritance chain:
        class MyComponent(CacheMixin, NitroComponent[MyState]):

    Configuration attributes:
        cache_enabled: Enable/disable caching (default: True)
        cache_ttl: Cache TTL in seconds (default: 300 = 5 minutes)
        cache_html: Also cache rendered HTML (default: True)
        cache_prefix: Custom cache key prefix (default: 'nitro')
    """

    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes default
    cache_html: bool = True
    cache_prefix: str = "nitro"

    def get_cache_key_parts(self) -> list[Any]:
        """
        Override to customize cache key generation.

        Returns a list of values that make this component's cache unique.
        By default includes: component class name, component_id, user_id (if authenticated).

        Example:
            def get_cache_key_parts(self):
                return [self.request.user.id, self.state.filter_value]
        """
        parts = [self.__class__.__name__, self.component_id]

        # Include user ID if authenticated
        if hasattr(self, "request") and self.request and hasattr(self.request, "user"):
            if self.request.user.is_authenticated:
                parts.append(f"user:{self.request.user.id}")
            else:
                parts.append("anon")

        return parts

    def _get_cache_key(self, suffix: str = "") -> str:
        """Generate cache key from parts."""
        parts = self.get_cache_key_parts()
        key_parts = [self.cache_prefix] + [str(p) for p in parts]
        if suffix:
            key_parts.append(suffix)
        return ":".join(key_parts)

    def _get_state_cache_key(self) -> str:
        """Cache key for component state."""
        return self._get_cache_key("state")

    def _get_html_cache_key(self, state_hash: str) -> str:
        """Cache key for rendered HTML (includes state hash for invalidation)."""
        return self._get_cache_key(f"html:{state_hash}")

    def cache_state(self) -> None:
        """Save current state to cache."""
        if not self.cache_enabled:
            return

        try:
            state_dict = self.state.model_dump() if hasattr(self.state, "model_dump") else dict(self.state)
            cache_key = self._get_state_cache_key()
            cache.set(cache_key, state_dict, self.cache_ttl)
            logger.debug(f"Nitro cache: saved state for {cache_key}")
        except Exception as e:
            logger.warning(f"Nitro cache: failed to save state: {e}")

    def load_cached_state(self) -> dict | None:
        """Load state from cache if available."""
        if not self.cache_enabled:
            return None

        try:
            cache_key = self._get_state_cache_key()
            state_dict = cache.get(cache_key)
            if state_dict:
                logger.debug(f"Nitro cache: loaded state from {cache_key}")
            return state_dict
        except Exception as e:
            logger.warning(f"Nitro cache: failed to load state: {e}")
            return None

    def invalidate_cache(self) -> None:
        """Invalidate all cached data for this component."""
        if not self.cache_enabled:
            return

        try:
            state_key = self._get_state_cache_key()
            cache.delete(state_key)

            # HTML cache keys include state hash, so we can't easily delete them
            # They'll expire naturally based on TTL
            logger.debug(f"Nitro cache: invalidated {state_key}")
        except Exception as e:
            logger.warning(f"Nitro cache: failed to invalidate: {e}")

    def render(self):
        """
        Override render to add HTML caching.

        If cache_html is enabled, caches the rendered HTML keyed by state hash.
        When state changes, the hash changes, causing a cache miss and re-render.
        """
        # If caching disabled or html caching disabled, use parent render
        if not self.cache_enabled or not self.cache_html:
            return super().render()

        # Generate state hash for cache key
        state_dict = self.state.model_dump() if hasattr(self.state, "model_dump") else dict(self.state)
        state_hash = get_state_hash(state_dict)

        # Check HTML cache
        html_key = self._get_html_cache_key(state_hash)
        cached_html = cache.get(html_key)

        if cached_html is not None:
            logger.debug(f"Nitro cache: HTML hit for {html_key}")
            return cached_html

        # Cache miss - render and cache
        html = super().render()

        try:
            cache.set(html_key, html, self.cache_ttl)
            logger.debug(f"Nitro cache: HTML cached for {html_key}")
        except Exception as e:
            logger.warning(f"Nitro cache: failed to cache HTML: {e}")

        return html


class CacheableComponent:
    """
    Alternative: Decorator-based caching for components.

    Usage:
        @cacheable(ttl=300, cache_html=True)
        class MyComponent(NitroComponent[MyState]):
            pass
    """

    pass  # Placeholder for future decorator implementation


def cache_action(ttl: int = 60):
    """
    Decorator to cache action results.

    Useful for expensive actions that don't change state.

    Usage:
        @cache_action(ttl=120)
        def load_expensive_data(self):
            # This result will be cached for 2 minutes
            return expensive_calculation()
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key from function name and args
            cache_key = f"nitro:action:{self.__class__.__name__}:{func.__name__}"
            if args:
                cache_key += f":{':'.join(str(a) for a in args)}"

            # Check cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Nitro cache: action hit for {cache_key}")
                return result

            # Execute and cache
            result = func(self, *args, **kwargs)
            if result is not None:
                cache.set(cache_key, result, ttl)
                logger.debug(f"Nitro cache: action cached for {cache_key}")

            return result

        return wrapper

    return decorator
