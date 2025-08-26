import abc
from typing import Any, Dict, List, Optional, Sequence
import json
import traceback

import redis.asyncio as aioredis


class StateStore(abc.ABC):
    """Abstract interface for persisting handler execution state"""

    @abc.abstractmethod
    async def init_message(self, message_id: str, handler_names: List[str]) -> None:
        ...

    @abc.abstractmethod
    async def save_handler_result(
        self, message_id: str, name: str, result: Any, attempts: int, status: str
    ) -> None:
        ...

    @abc.abstractmethod
    async def load_message_state(self, message_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abc.abstractmethod
    async def mark_handler_failed(
        self, message_id: str, name: str, exc: Exception
    ) -> None:
        ...

    @abc.abstractmethod
    async def close(self) -> None:
        ...


class InMemoryStateStore(StateStore):
    """Simple in-process state store (non-persistent)."""

    _store: Dict[str, Dict[str, Any]] = {}

    async def init_message(self, message_id: str, handler_names: Sequence[str]) -> None:
        self._store[message_id] = {
            "handlers": {
                n: {"status": "PENDING", "attempts": 0, "result": None, "error": None}
                for n in handler_names
            }
        }

    async def save_handler_result(
        self, message_id: str, name: str, result: Any, attempts: int, status: str
    ) -> None:
        msg = self._store.setdefault(message_id, {"handlers": {}})
        msg["handlers"].setdefault(name, {})
        msg["handlers"][name].update(
            {"status": status, "attempts": attempts, "result": result, "error": None}
        )

    async def load_message_state(self, message_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(message_id)

    async def mark_handler_failed(
        self, message_id: str, name: str, exc: Exception
    ) -> None:
        msg = self._store.setdefault(message_id, {"handlers": {}})
        msg["handlers"].setdefault(name, {})
        msg["handlers"][name].update({"status": "FAILED", "error": repr(exc)})

    async def close(self) -> None:
        self._store.clear()


class RedisStateStore(StateStore):
    """
    Redis-based implementation of StateStore for persisting message and handler states.
    Uses Redis hashes to store data per message_id.
    - Key format: 'message:{message_id}'
    - Fields: 'handler_states' (JSON dict of handler states), 'results' (JSON dict of results), 'overall_status'
    Serialization uses JSON for complex data.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl_seconds: Optional[int] = None,
    ):
        """
        Initialize the RedisStateStore.

        Args:
            redis_url: Redis connection URL (e.g., 'redis://localhost:6379').
            ttl_seconds: Optional TTL for message keys (auto-expire after processing).
        """
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        """Lazy initialization of Redis connection."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def init_message(self, message_id: str, handler_names: List[str]) -> None:
        """Initialize state for a new message."""
        redis = await self._get_redis()
        key = f"message:{message_id}"
        handler_states = {
            name: {
                "status": "pending",
                "attempts": 0,
                "result": None,
                "last_error": None,
            }
            for name in handler_names
        }
        data = {
            "handler_states": json.dumps(handler_states),
            "results": json.dumps({}),
            "overall_status": "processing",
        }
        _ = await redis.hmset(key, data)  # type: ignore
        if self.ttl_seconds:
            await redis.expire(key, self.ttl_seconds)

    async def save_handler_result(
        self, message_id: str, name: str, result: Any, attempts: int, status: str
    ) -> None:
        """Save handler execution result."""
        redis = await self._get_redis()
        key = f"message:{message_id}"
        # Load current states
        handler_states_str = await redis.hget(key, "handler_states")  # type: ignore
        results_str = await redis.hget(key, "results")  # type: ignore

        handler_states = json.loads(handler_states_str) if handler_states_str else {}
        results = json.loads(results_str) if results_str else {}

        # Update handler state
        if name in handler_states:
            handler_states[name]["status"] = status
            handler_states[name]["attempts"] = attempts
            handler_states[name]["result"] = result  # Will be serialized later
            handler_states[name]["last_error"] = None  # Clear error on success

        results[name] = result

        # Save back
        _ = await redis.hmset(  # type: ignore
            key,
            {
                "handler_states": json.dumps(handler_states),
                "results": json.dumps(results),
            },
        )

    async def load_message_state(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Load saved message state."""
        redis = await self._get_redis()
        key = f"message:{message_id}"
        if not await redis.exists(key):
            return None

        data = await redis.hgetall(key)  # type: ignore
        if not data:
            return None

        return {
            "handler_states": json.loads(data.get("handler_states", "{}")),
            "results": json.loads(data.get("results", "{}")),
            "overall_status": data.get("overall_status", "processing"),
        }

    async def mark_handler_failed(
        self, message_id: str, name: str, exc: Exception
    ) -> None:
        """Mark handler as failed with exception details."""
        redis = await self._get_redis()
        key = f"message:{message_id}"
        # Load current handler_states
        handler_states_str = await redis.hget(key, "handler_states")  # type: ignore
        handler_states = json.loads(handler_states_str) if handler_states_str else {}

        if name in handler_states:
            handler_states[name]["status"] = "failed"
            handler_states[name]["last_error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }

        await redis.hset(key, "handler_states", json.dumps(handler_states))  # type: ignore

    async def close(self) -> None:
        """Clean up resources."""
        if self._redis:
            await self._redis.close()
            self._redis = None
