from typing import Any, Dict, Optional, Literal, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

from midil.event.producer.base import EventProducer, EventProducerConfig
from midil.event.consumer.strategies.base import EventConsumerConfig
from midil.event.consumer.strategies.pull import PullEventConsumer
from midil.event.consumer.strategies.push import PushEventConsumer

from midil.event.producer.redis import RedisProducer, RedisProducerConfig
from midil.event.producer.sqs import SQSProducer, SQSProducerConfig

from midil.event.consumer.sqs import SQSConsumer, SQSConsumerConfig
from midil.event.consumer.webhook import WebhookPushConsumer, WebhookPushConsumerConfig

from midil.event.subscriber.base import (
    EventSubscriber,
    FunctionSubscriber,
    SubscriberMiddleware,
)
from midil.event.exceptions import (
    ConsumerNotImplementedError,
    ProducerNotImplementedError,
    TransportNotImplementedError,
)


SupportedProducers = Literal["redis", "sqs", "webhook"]
SupportedConsumers = Literal["sqs", "webhook"]


class EventConfig(BaseSettings):
    """
    Configuration model for the EventBus.

    Attributes:
        producer: The configuration for the event producer. Can be one of EventProducerConfig,
                  SQSProducerConfig, RedisProducerConfig, or None.
        consumer: The configuration for the event consumer. Can be one of EventConsumerConfig,
                  SQSConsumerConfig, WebhookPushConsumerConfig, or None.
    """

    consumer: Optional[
        Union[SQSConsumerConfig, WebhookPushConsumerConfig, EventConsumerConfig]
    ] = None
    producer: Optional[EventProducerConfig] = None

    model_config = SettingsConfigDict(
        env_prefix="MIDIL__EVENT__",
        env_nested_delimiter="__",
        extra="ignore",
        # env_parse_json=True
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return env_settings, init_settings, dotenv_settings, file_secret_settings


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
        "webhook": WebhookPushConsumer,
    }
    CONFIG_MAP = {
        "sqs": {"producer": SQSProducerConfig, "consumer": SQSConsumerConfig},
        "webhook": {
            "consumer": WebhookPushConsumerConfig,
        },
        "redis": {"producer": RedisProducerConfig},
    }

    @classmethod
    def create_producer(cls, config: EventProducerConfig) -> EventProducer:
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
        cls,
        config: Union[
            SQSConsumerConfig, WebhookPushConsumerConfig, EventConsumerConfig
        ],
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
        print(config.model_dump())

        consumer_cls = cls.CONSUMER_MAP.get(config.type)
        if not consumer_cls:
            raise ConsumerNotImplementedError(config.type)
        if config.type == "webhook":
            return consumer_cls(config)
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
            self.producer.close()
