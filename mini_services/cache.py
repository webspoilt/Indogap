"""
Simple In-Memory Cache for IndoGap API

Provides TTL-based caching for API responses to reduce database load
and improve response times. For production, consider Redis.
"""
import time
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
import hashlib
import json

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL (Time-To-Live) support.
    
    For production deployments, consider using Redis for:
    - Persistence across restarts
    - Distributed caching across multiple instances
    - Better memory management
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self._cache: Dict[str, tuple] = {}
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._hits += 1
                return value
            # Expired, remove it
            del self._cache[key]
        self._misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache with optional custom TTL."""
        self._cache[key] = (value, time.time() + (ttl or self.default_ttl))
    
    def delete(self, key: str) -> bool:
        """Delete a specific key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if expiry < current_time
        ]
        for key in expired_keys:
            del self._cache[key]
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
        }


# Global cache instance
cache = SimpleCache(default_ttl=300)  # 5 minute default TTL


def cached(ttl: int = None, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live in seconds (uses default if None)
        key_prefix: Prefix for cache key
    
    Usage:
        @cached(ttl=60)
        async def get_data(id: str):
            return await fetch_from_db(id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            if args:
                key_parts.extend(str(a) for a in args)
            if kwargs:
                key_parts.append(hashlib.md5(
                    json.dumps(kwargs, sort_keys=True, default=str).encode()
                ).hexdigest()[:8])
            cache_key = ":".join(key_parts)
            
            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key_parts = [key_prefix or func.__name__]
            if args:
                key_parts.extend(str(a) for a in args)
            if kwargs:
                key_parts.append(hashlib.md5(
                    json.dumps(kwargs, sort_keys=True, default=str).encode()
                ).hexdigest()[:8])
            cache_key = ":".join(key_parts)
            
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern.
    
    Args:
        pattern: String pattern to match (simple contains check)
    
    Returns:
        Number of invalidated entries
    """
    keys_to_delete = [
        key for key in cache._cache.keys()
        if pattern in key
    ]
    for key in keys_to_delete:
        cache.delete(key)
    return len(keys_to_delete)
