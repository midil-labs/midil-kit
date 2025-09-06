from midil.event.producer.base import EventProducer
from midil.event.producer.base import BaseProducerConfig
from pydantic import Field
from typing import Dict, Any, Literal
import json
from redis.asyncio import Redis


class RedisProducerEventConfig(BaseProducerConfig):
    type: Literal["redis"] = Field(
        "redis", description="Type of the producer configuration"
    )
    channel: str = Field(..., description="Channel to publish the event to")
    url: str = Field(..., description="Endpoint of the Redis server")


class RedisProducer(EventProducer):
    def __init__(self, config: RedisProducerEventConfig):
        self.config = config
        self.redis = Redis.from_url(config.url)

    async def publish(self, payload: Dict[str, Any], **kwargs) -> None:
        message = json.dumps(payload)
        await self.redis.publish(self.config.channel, message)

    async def close(self) -> None:
        return await self.redis.close()
