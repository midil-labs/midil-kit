from midil.event.producer.base import EventProducer
from midil.event.producer.base import EventProducerConfig
from typing import Dict, Any
import json
from redis import Redis


class RedisProducerConfig(EventProducerConfig):
    type: str = "redis"
    channel: str


class RedisProducer(EventProducer):
    def __init__(self, config: RedisProducerConfig):
        self.config = config
        self.redis = Redis.from_url(config.endpoint)

    async def publish(self, payload: Dict[str, Any], **kwargs) -> None:
        message = json.dumps(payload)
        await self.redis.publish(self.config.channel, message)

    def close(self) -> None:
        self.redis.close()
