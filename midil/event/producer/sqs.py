from midil.event.producer.base import EventProducer
from midil.event.producer.base import EventProducerConfig
import aioboto3
from typing import Dict, Any
import json
from pydantic import Field
from midil.event.utils import get_region_from_queue_url


class SQSProducerConfig(EventProducerConfig):
    type: str = Field("sqs", description="Type of the producer configuration")
    queue_url: str = Field(..., description="URL of the queue")

    @property
    def region(self) -> str:
        return get_region_from_queue_url(self.queue_url)


class SQSProducer(EventProducer):
    def __init__(self, config: SQSProducerConfig):
        self.session = aioboto3.Session()
        self.config = config

    async def publish(self, payload: Dict[str, Any], **kwargs) -> None:
        message = json.dumps(payload)
        async with self.session.client("sqs", region_name=self.config.region) as sqs:
            await sqs.send_message(QueueUrl=self.config.queue_url, MessageBody=message)

    def close(self) -> None:
        pass
