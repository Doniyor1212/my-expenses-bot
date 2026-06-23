import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        value = self._data.get(key)
        if not value:
            return None
        expires_at, payload = value
        if expires_at < time.time():
            self._data.pop(key, None)
            return None
        return payload

    def set(self, key: str, value: Any) -> None:
        self._data[key] = (time.time() + self.ttl_seconds, value)

    def clear(self) -> None:
        self._data.clear()


cache = TTLCache()
