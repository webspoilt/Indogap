"""
Cache Module Tests for IndoGap

Tests the caching functionality.
Run with: pytest tests/test_cache.py -v
"""
import pytest
import time
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mini_services.cache import SimpleCache, cached, cache, invalidate_cache_pattern


class TestSimpleCache:
    """Tests for SimpleCache class"""
    
    def test_set_and_get(self):
        """Test basic set and get operations"""
        test_cache = SimpleCache()
        test_cache.set("key1", "value1")
        assert test_cache.get("key1") == "value1"
    
    def test_get_missing_key(self):
        """Test getting a key that doesn't exist"""
        test_cache = SimpleCache()
        assert test_cache.get("nonexistent") is None
    
    def test_ttl_expiration(self):
        """Test that items expire after TTL"""
        test_cache = SimpleCache(default_ttl=1)  # 1 second TTL
        test_cache.set("key1", "value1")
        assert test_cache.get("key1") == "value1"
        time.sleep(1.1)  # Wait for expiration
        assert test_cache.get("key1") is None
    
    def test_custom_ttl(self):
        """Test custom TTL per item"""
        test_cache = SimpleCache(default_ttl=10)
        test_cache.set("short", "value", ttl=1)
        test_cache.set("long", "value", ttl=10)
        time.sleep(1.1)
        assert test_cache.get("short") is None
        assert test_cache.get("long") == "value"
    
    def test_delete(self):
        """Test deleting a key"""
        test_cache = SimpleCache()
        test_cache.set("key1", "value1")
        assert test_cache.delete("key1") is True
        assert test_cache.get("key1") is None
        assert test_cache.delete("nonexistent") is False
    
    def test_clear(self):
        """Test clearing all items"""
        test_cache = SimpleCache()
        test_cache.set("key1", "value1")
        test_cache.set("key2", "value2")
        test_cache.clear()
        assert test_cache.get("key1") is None
        assert test_cache.get("key2") is None
    
    def test_cache_stats(self):
        """Test cache statistics"""
        test_cache = SimpleCache()
        test_cache.set("key1", "value1")
        test_cache.get("key1")  # Hit
        test_cache.get("key1")  # Hit
        test_cache.get("missing")  # Miss
        
        stats = test_cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries"""
        test_cache = SimpleCache(default_ttl=1)
        test_cache.set("key1", "value1")
        test_cache.set("key2", "value2")
        time.sleep(1.1)
        removed = test_cache.cleanup_expired()
        assert removed == 2


class TestCachedDecorator:
    """Tests for @cached decorator"""
    
    def test_sync_function_caching(self):
        """Test caching a synchronous function"""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call - should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call - should return cached value
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Function not called again
    
    @pytest.mark.asyncio
    async def test_async_function_caching(self):
        """Test caching an async function"""
        call_count = 0
        
        @cached(ttl=60)
        async def async_expensive_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = await async_expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        result2 = await async_expensive_function(5)
        assert result2 == 10
        assert call_count == 1


class TestInvalidatePattern:
    """Tests for cache pattern invalidation"""
    
    def test_invalidate_by_pattern(self):
        """Test invalidating keys by pattern"""
        cache.clear()
        cache.set("user:1:profile", {"name": "Alice"})
        cache.set("user:2:profile", {"name": "Bob"})
        cache.set("post:1:content", {"title": "Hello"})
        
        # Invalidate all user keys
        count = invalidate_cache_pattern("user:")
        assert count == 2
        assert cache.get("user:1:profile") is None
        assert cache.get("post:1:content") is not None
