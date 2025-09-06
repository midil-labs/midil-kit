from midil.event.producer.base import EventProducer
from midil.event.producer.base import BaseProducerConfig
import aioboto3
from typing import Dict, Any, Literal
import json
from pydantic import Field
from midil.event.utils import get_region_from_sqs_queue_url


class SQSProducerEventConfig(BaseProducerConfig):
    type: Literal["sqs"] = "sqs"
    queue_url: str = Field(..., description="URL of the queue")

    @property
    def region(self) -> str:
        return get_region_from_sqs_queue_url(self.queue_url)


class SQSProducer(EventProducer):
    def __init__(self, config: SQSProducerEventConfig):
        self.session = aioboto3.Session()
        self.config = config

    async def publish(self, payload: Dict[str, Any], **kwargs) -> None:
        message = json.dumps(payload)
        async with self.session.client("sqs", region_name=self.config.region) as sqs:
            await sqs.send_message(QueueUrl=self.config.queue_url, MessageBody=message)

    async def close(self) -> None:
        pass
