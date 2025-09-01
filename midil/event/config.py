from __future__ import annotations

from typing import Annotated, Optional, Union, TypeAlias

from pydantic import BaseModel, Field, Json
from midil.event.consumer.sqs import SQSConsumerEventConfig
from midil.event.consumer.webhook import WebhookConsumerEventConfig
from midil.event.producer.redis import RedisProducerEventConfig
from midil.event.producer.sqs import SQSProducerEventConfig


# Union types for producers and consumers
ProducerConfig = Annotated[
    Union[SQSProducerEventConfig, RedisProducerEventConfig], Field(discriminator="type")
]

ConsumerConfig = Annotated[
    Union[SQSConsumerEventConfig, WebhookConsumerEventConfig],
    Field(discriminator="type"),
]

ProducerField: TypeAlias = Annotated[
    Union[ProducerConfig, Json[ProducerConfig]],
    Field(..., description="Event producer configuration"),
]

ConsumerField: TypeAlias = Annotated[
    Union[ConsumerConfig, Json[ConsumerConfig]],
    Field(..., description="Event consumer configuration"),
]


class EventConfig(BaseModel):
    """
    Configuration model for the EventBus.

    Attributes:
        producer: The configuration for the event producer (optional).
        consumer: The configuration for the event consumer (optional).
    """

    consumer: Optional[ConsumerField] = None
    producer: Optional[ProducerField] = None
