from typing import Any, Dict, Optional, Literal
from pydantic_settings import BaseSettings

from midil.event.consumer.strategies.pull import PullEventConsumer
from midil.event.consumer.strategies.push import PushEventConsumer

from midil.event.producer.redis import RedisProducer, RedisProducerEventConfig
from midil.event.producer.sqs import SQSProducer, SQSProducerEventConfig

from midil.event.consumer.sqs import SQSConsumer, SQSConsumerEventConfig
from midil.event.consumer.webhook import WebhookConsumer, WebhookConsumerEventConfig

from midil.event.subscriber.base import (
    EventSubscriber,
    FunctionSubscriber,
    SubscriberMiddleware,
)
from midil.event.producer.base import EventProducer

from midil.event.exceptions import (
    ConsumerNotImplementedError,
    ProducerNotImplementedError,
    TransportNotImplementedError,
)

from midil.event.config import (
    EventConfig,
    ProducerConfig,
    ConsumerConfig,
)


SupportedProducers = Literal["redis", "sqs", "webhook"]
SupportedConsumers = Literal["sqs", "webhook"]


class EventBusFactory:
    """
    Factory class for creating event producers, consumers, and their configurations.

    Class Attributes:
        PRODUCER_MAP: Maps producer type strings to their corresponding producer classes.
        CONSUMER_MAP: Maps consumer type strings to their corresponding consumer classes.
        CONFIG_MAP: Maps transport types to their configuration classes for both producer and consumer.

    Methods:
        create_producer: Instantiates an EventProducer based on the provided configuration.
        create_consumer: Instantiates an EventConsumer (pull or push) based on the provided configuration.
        create_config: Instantiates a configuration object for a given transport type.
    """

    PRODUCER_MAP = {
        "redis": RedisProducer,
        "sqs": SQSProducer,
    }
    CONSUMER_MAP = {
        "sqs": SQSConsumer,
        "webhook": WebhookConsumer,
    }
    CONFIG_MAP = {
        "sqs": {"producer": SQSProducerEventConfig, "consumer": SQSConsumerEventConfig},
        "webhook": {
            "consumer": WebhookConsumerEventConfig,
        },
        "redis": {"producer": RedisProducerEventConfig},
    }

    @classmethod
    def create_producer(cls, config: ProducerConfig) -> EventProducer:
        """
        Create an event producer instance based on the provided configuration.

        Args:
            config: The configuration object for the producer.

        Returns:
            An instance of EventProducer.

        Raises:
            ValueError: If the producer type is not supported.
        """
        producer_cls = cls.PRODUCER_MAP.get(config.type)
        if not producer_cls:
            raise ProducerNotImplementedError(config.type)
        return producer_cls(config)

    @classmethod
    def create_consumer(
        cls, config: ConsumerConfig
    ) -> PullEventConsumer | PushEventConsumer:
        """
        Create an event consumer instance (pull or push) based on the provided configuration.

        Args:
            config: The configuration object for the consumer.

        Returns:
            An instance of PullEventConsumer or PushEventConsumer.

        Raises:
            ValueError: If the consumer type is not supported.
        """

        consumer_cls = cls.CONSUMER_MAP.get(config.type)
        if not consumer_cls:
            raise ConsumerNotImplementedError(config.type)
        return consumer_cls(config)

    @classmethod
    def create_config(
        cls, transport: SupportedProducers | SupportedConsumers, **kwargs
    ) -> BaseSettings:
        """
        Create a configuration object for the specified transport type.

        Args:
            transport: The transport type (e.g., "redis", "sqs", "webhook").
            **kwargs: Additional keyword arguments to pass to the config class.

        Returns:
            An instance of a configuration class derived from BaseSettings.

        Raises:
            ValueError: If the transport type is not supported.
        """
        config_map = cls.CONFIG_MAP.get(transport)
        if not isinstance(config_map, dict):
            raise TransportNotImplementedError(transport)
        config_cls = config_map.get("producer") or config_map.get("consumer")
        if not config_cls:
            raise TransportNotImplementedError(transport)
        return config_cls(**kwargs)


class EventBus:
    """
    The main interface for event-driven communication, providing methods to publish events,
    subscribe handlers, and manage the lifecycle of event producers and consumers.

    Attributes:
        producer: The event producer instance, if configured.
        consumer: The event consumer instance, if configured.

    Methods:
        publish: Publish an event to the configured producer.
        subscribe: Register an event subscriber/handler.
        subscriber: Decorator to register a function as an event subscriber.
        start: Start the event consumer.
        stop: Stop the event consumer and close the producer.
    """

    def __init__(
        self,
        config: Optional[EventConfig] = None,
    ):
        """
        Initialize the EventBus with the given configuration.

        Args:
            config: An EventBusConfig instance specifying producer and/or consumer configuration.
        """
        if config is None:
            config = EventConfig()

        if config.producer:
            self.producer = EventBusFactory.create_producer(config.producer)
        if config.consumer:
            self.consumer = EventBusFactory.create_consumer(config.consumer)

    async def publish(
        self,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish an event to the configured producer.

        Args:
            payload: The event payload as a dictionary.
            metadata: Optional metadata to include with the event.

        Raises:
            ValueError: If the producer is not configured.
        """
        if not self.producer:
            raise ValueError("Producer not configured")
        await self.producer.publish(payload, metadata=metadata)

    def subscribe(self, handler: EventSubscriber) -> None:
        """
        Register an event subscriber/handler to receive events from the consumer.

        Args:
            handler: An instance of EventSubscriber.

        Raises:
            ValueError: If the consumer is not configured.
        """
        if not self.consumer:
            raise ValueError("Consumer not configured")
        self.consumer.subscribe(handler)

    def subscriber(
        self, middlewares: Optional[list[SubscriberMiddleware]] = None, **kwargs
    ):
        """
        Decorator to register a function as an event subscriber.

        Args:
            middlewares: Optional list of SubscriberMiddleware to apply to the subscriber.
            **kwargs: Additional keyword arguments passed to FunctionSubscriber.

        Returns:
            A decorator that registers the decorated function as an event subscriber.
        """

        def decorator(func):
            self.subscribe(FunctionSubscriber(func, middlewares=middlewares, **kwargs))
            return func

        return decorator

    async def start(self) -> None:
        """
        Start the event consumer to begin receiving and dispatching events.

        Raises:
            ValueError: If the consumer is not configured.
        """
        if not self.consumer:
            raise ValueError("Consumer not configured")
        await self.consumer.start()

    async def stop(self) -> None:
        """
        Stop the event consumer and close the event producer, performing any necessary cleanup.
        """
        if self.consumer:
            await self.consumer.stop()
        if hasattr(self, "producer") and self.producer:
            await self.producer.close()
