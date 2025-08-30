from midil.event.producer.base import EventProducer
from midil.event.producer.base import EventProducerConfig
import aioboto3
from typing import Dict, Any
import json


class SQSProducerConfig(EventProducerConfig):
    type: str = "sqs"


class SQSProducer(EventProducer):
    def __init__(self, config: SQSProducerConfig):
        self.session = aioboto3.Session()
        self.config = config

    async def publish(self, payload: Dict[str, Any], **kwargs) -> None:
        message = json.dumps(payload)
        async with self.session.client("sqs") as sqs:
            await sqs.send_message(QueueUrl=self.config.endpoint, MessageBody=message)

    def close(self) -> None:
        pass
