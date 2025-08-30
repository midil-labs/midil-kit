from midil.event.producer.base import EventProducer
from midil.event.producer.base import EventProducerConfig
from pydantic import Field
from typing import Dict, Any
import json
from redis import Redis


class RedisProducerConfig(EventProducerConfig):
    type: str = Field("redis", description="Type of the producer configuration")
    channel: str = Field(..., description="Channel to publish the event to")
    url: str = Field(..., description="Endpoint of the Redis server")


class RedisProducer(EventProducer):
    def __init__(self, config: RedisProducerConfig):
        self.config = config
        self.redis = Redis.from_url(config.url)

    async def publish(self, payload: Dict[str, Any], **kwargs) -> None:
        message = json.dumps(payload)
        await self.redis.publish(self.config.channel, message)

    def close(self) -> None:
        self.redis.close()
