import json
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logger


class RedisClient:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._fallback: dict = {}
        self._use_fallback = False

    def connect(self) -> None:
        if not self._client:
            try:
                self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                logger.info("Connecting to Redis", extra={"redis_url": settings.REDIS_URL})
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {str(e)}. Using local in-memory fallback.")
                self._use_fallback = True

    async def disconnect(self) -> None:
        if self._client:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None
            logger.info("Disconnected from Redis")

    @property
    def client(self) -> Optional[redis.Redis]:
        if self._use_fallback:
            return None
        if not self._client:
            self.connect()
        return self._client

    async def get(self, key: str) -> Optional[str]:
        if self.client is None:
            return self._fallback.get(key)
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Switching to in-memory fallback.")
            self._use_fallback = True
            return self._fallback.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self.client is None:
            self._fallback[key] = value
            return True
        try:
            await self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Switching to in-memory fallback.")
            self._use_fallback = True
            self._fallback[key] = value
            return True

    async def delete(self, key: str) -> bool:
        if self.client is None:
            self._fallback.pop(key, None)
            return True
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}. Switching to in-memory fallback.")
            self._use_fallback = True
            self._fallback.pop(key, None)
            return True

    async def get_json(self, key: str) -> Optional[Any]:
        data = await self.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return None
        return None

    async def set_json(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        try:
            return await self.set(key, json.dumps(value), ex=ex)
        except Exception as e:
            logger.error(f"Redis set_json error: {str(e)}", extra={"key": key})
            return False


redis_client = RedisClient()
