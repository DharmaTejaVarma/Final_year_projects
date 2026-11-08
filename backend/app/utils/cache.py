import asyncio
import time
from typing import Any, Callable, Dict, Optional, Tuple
from threading import Lock

try:
    from app.core.config import settings
    from app.core.logger import logger
except ImportError:
    from backend.app.core.config import settings
    from backend.app.core.logger import logger


class TTLCache:
    """Thread-safe in-memory cache with Time-To-Live (TTL) expiration."""

    def __init__(self, default_ttl: int = 3600):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expires_at = self._cache[key]
            if time.monotonic() > expires_at:
                # Expired entry
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.monotonic() + ttl
        with self._lock:
            self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self._hits + self._misses
            hit_ratio = round((self._hits / total_requests) * 100, 2) if total_requests > 0 else 0.0
            return {
                "size": len(self._cache),
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio_percent": hit_ratio,
            }


# Global in-memory cache instance
api_cache = TTLCache(default_ttl=settings.CACHE_DEFAULT_TTL_SECONDS)


async def execute_with_retry(
    coro_fn: Callable[[], Any],
    max_retries: int = 2,
    base_delay: float = 0.5,
    operation_name: str = "API request",
) -> Any:
    """Execute an asynchronous operation with exponential backoff on transient errors."""
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_fn()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"Transient error during {operation_name} (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"Exhausted retries ({max_retries + 1}) for {operation_name}: {e}")
                raise last_exception

