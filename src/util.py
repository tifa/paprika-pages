import threading
import time
from typing import Any


def get_all_subclasses(cls) -> set[type]:
    subclasses = set(cls.__subclasses__())
    for subclass in cls.__subclasses__():
        subclasses.update(get_all_subclasses(subclass))
    return subclasses


class InMemoryCache:
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def setex(
        self, key: str, ttl: int | None = None, value: Any | None = None
    ) -> None:
        expire_at = time.time() + ttl
        with self._lock:
            self._store[key] = (value, expire_at)

    def get(self, key) -> Any | None:
        with self._lock:
            item = self._store.get(key)
            if not item:
                return None
            value, expire_at = item
            if expire_at and time.time() >= expire_at:
                del self._store[key]
                return None
            return value


_CACHE: InMemoryCache | None = None


def cache_client() -> InMemoryCache:
    global _CACHE
    if _CACHE is None:
        _CACHE = InMemoryCache()
    return _CACHE
