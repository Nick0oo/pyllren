"""
Redis Cache Module

Provides caching functionality using Redis with connection pooling,
error handling, and graceful fallback when Redis is unavailable.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

import redis
from redis.connection import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance."""
    return _redis_client


def init_redis() -> bool:
    """
    Initialize Redis connection pool and client.
    Returns True if successful, False otherwise.
    """
    global _redis_pool, _redis_client
    
    try:
        # Create connection pool
        _redis_pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            health_check_interval=30,
        )
        
        # Create Redis client
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        
        # Test connection
        _redis_client.ping()
        
        logger.info(f"Redis connected successfully to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return True
        
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        _redis_pool = None
        _redis_client = None
        return False


def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool, _redis_client
    
    if _redis_client:
        try:
            _redis_client.close()
        except Exception as e:
            logger.warning(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None
    
    if _redis_pool:
        try:
            _redis_pool.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting Redis pool: {e}")
        finally:
            _redis_pool = None


def is_redis_available() -> bool:
    """Check if Redis is available."""
    return _redis_client is not None


def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache.
    Returns None if key doesn't exist or Redis is unavailable.
    """
    if not is_redis_available():
        return None
    
    try:
        value = _redis_client.get(key)
        if value is not None:
            logger.debug(f"Cache HIT for key: {key}")
            return json.loads(value)
        else:
            logger.debug(f"Cache MISS for key: {key}")
            return None
    except Exception as e:
        logger.warning(f"Error getting cache key {key}: {e}")
        return None


def set_cache(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Set value in cache with TTL.
    Returns True if successful, False otherwise.
    """
    if not is_redis_available():
        return False
    
    try:
        serialized_value = json.dumps(value, default=str)
        result = _redis_client.setex(key, ttl, serialized_value)
        logger.debug(f"Cache SET for key: {key} (TTL: {ttl}s)")
        return bool(result)
    except Exception as e:
        logger.warning(f"Error setting cache key {key}: {e}")
        return False


def delete_cache(key: str) -> bool:
    """
    Delete key from cache.
    Returns True if successful, False otherwise.
    """
    if not is_redis_available():
        return False
    
    try:
        result = _redis_client.delete(key)
        logger.debug(f"Cache DELETE for key: {key}")
        return bool(result)
    except Exception as e:
        logger.warning(f"Error deleting cache key {key}: {e}")
        return False


def invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all keys matching pattern.
    Returns number of keys deleted.
    """
    if not is_redis_available():
        return 0
    
    try:
        keys = _redis_client.keys(pattern)
        if keys:
            deleted = _redis_client.delete(*keys)
            logger.info(f"Cache INVALIDATE pattern: {pattern} ({deleted} keys)")
            return deleted
        return 0
    except Exception as e:
        logger.warning(f"Error invalidating cache pattern {pattern}: {e}")
        return 0


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from prefix and parameters.
    """
    # Create a hash of all parameters
    params = []
    
    # Add positional arguments
    for arg in args:
        if arg is not None:
            params.append(str(arg))
    
    # Add keyword arguments (sorted for consistency)
    for key, value in sorted(kwargs.items()):
        if value is not None:
            params.append(f"{key}={value}")
    
    # Create hash of parameters
    if params:
        param_string = ":".join(params)
        param_hash = hashlib.md5(param_string.encode()).hexdigest()[:8]
        return f"{prefix}:{param_hash}"
    else:
        return prefix


def cached(
    prefix: str,
    ttl: int = 300,
    key_func: Optional[Callable] = None,
    invalidate_on: Optional[list[str]] = None
):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Optional function to generate cache key from function arguments
        invalidate_on: List of patterns to invalidate when this function is called
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = get_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            set_cache(cache_key, result, ttl)
            
            # Invalidate related patterns if specified
            if invalidate_on:
                for pattern in invalidate_on:
                    invalidate_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


# Cache key generators for common patterns
def list_cache_key(prefix: str, skip: int = 0, limit: int = 100, **filters) -> str:
    """Generate cache key for paginated lists with filters."""
    return generate_cache_key(f"{prefix}:list", skip, limit, **filters)


def item_cache_key(prefix: str, item_id: Any) -> str:
    """Generate cache key for individual items."""
    return f"{prefix}:{item_id}"


def stats_cache_key(prefix: str) -> str:
    """Generate cache key for statistics."""
    return f"{prefix}:stats"


# Common invalidation patterns
def invalidate_entity_cache(entity_name: str) -> int:
    """Invalidate all cache entries for an entity."""
    return invalidate_pattern(f"{entity_name}:*")


def invalidate_list_cache(entity_name: str) -> int:
    """Invalidate list cache entries for an entity."""
    return invalidate_pattern(f"{entity_name}:list:*")


def invalidate_item_cache(entity_name: str, item_id: Any) -> bool:
    """Invalidate specific item cache."""
    return delete_cache(f"{entity_name}:{item_id}")


def invalidate_stats_cache(entity_name: str) -> bool:
    """Invalidate statistics cache for an entity."""
    return delete_cache(f"{entity_name}:stats")
