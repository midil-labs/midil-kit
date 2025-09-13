from typing import Any, Dict, Optional, Mapping
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
    EventProducerType,
    EventConsumerType,
)


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

    _PRODUCER_MAP = {
        "redis": RedisProducer,
        "sqs": SQSProducer,
    }
    _CONSUMER_MAP = {
        "sqs": SQSConsumer,
        "webhook": WebhookConsumer,
    }
    _CONFIG_MAP = {
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
        producer_cls = cls._PRODUCER_MAP.get(config.type)
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

        consumer_cls = cls._CONSUMER_MAP.get(config.type)
        if not consumer_cls:
            raise ConsumerNotImplementedError(config.type)
        return consumer_cls(config)

    @classmethod
    def create_config(
        cls, transport: EventProducerType | EventConsumerType, **kwargs
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
        config_map = cls._CONFIG_MAP.get(transport)
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
        consumers: Dictionary of named consumer instances, if configured.

    Methods:
        publish: Publish an event to the configured producer.
        subscribe: Register an event subscriber/handler to one or all consumers.
        subscriber: Decorator to register a function as an event subscriber.
        start: Start all event consumers.
        stop: Stop all event consumers and close the producer.
    """

    def __init__(
        self,
        config: Optional[EventConfig] = None,
    ):
        """
        Initialize the EventBus with the given configuration.

        Args:
            config: An EventBusConfig instance specifying producer and/or consumer configurations.
        """
        if config is None:
            config = EventConfig()

        self.producers: Mapping[str, EventProducer] = {}
        if config.producers:
            for name, producer_config in config.producers.items():
                self.producers[name] = EventBusFactory.create_producer(producer_config)

        self.consumers: Mapping[str, PullEventConsumer | PushEventConsumer] = {}
        if config.consumers:
            for name, consumer_config in config.consumers.items():
                self.consumers[name] = EventBusFactory.create_consumer(consumer_config)

    async def publish(
        self,
        payload: Dict[str, Any],
        target: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Publish an event to a specific producer or all producers.

        Args:
            payload: The event payload as a dictionary.
            target: Optional name of the specific producer to publish to.
                         If None, publishes to all producers.
            metadata: Optional metadata to include with the event.

        Raises:
            ValueError: If no producers are configured or if the specified producer is not found.
        """
        if not self.producers:
            raise ValueError("No producers configured")

        if target:
            if target not in self.producers:
                available_producers = list(self.producers.keys())
                raise ValueError(
                    f"Producer '{target}' not found. Available producers: {available_producers}"
                )
            await self.producers[target].publish(payload, metadata=metadata)
        else:
            for producer in self.producers.values():
                await producer.publish(payload, metadata=metadata)

    def subscribe(self, handler: EventSubscriber, target: Optional[str] = None) -> None:
        """
        Register an event subscriber/handler to receive events from one or all consumers.

        Args:
            handler: An instance of EventSubscriber.
            target: Optional name of the specific consumer to subscribe to.
                         If None, subscribes to all consumers.

        Raises:
            ValueError: If no consumers are configured or if the specified consumer is not found.
        """
        if not self.consumers:
            raise ValueError("No consumers configured")

        if target:
            if target not in self.consumers:
                available_consumers = list(self.consumers.keys())
                raise ValueError(
                    f"Consumer '{target}' not found. Available consumers: {available_consumers}"
                )
            self.consumers[target].subscribe(handler)
        else:
            for consumer in self.consumers.values():
                consumer.subscribe(handler)

    def subscriber(
        self,
        target: Optional[str] = None,
        middlewares: Optional[list[SubscriberMiddleware]] = None,
        **kwargs,
    ):
        """
        Decorator to register a function as an event subscriber.

        Args:
            target: Optional name of the specific consumer to subscribe to.
                         If None, subscribes to all consumers.
            middlewares: Optional list of SubscriberMiddleware to apply to the subscriber.
            **kwargs: Additional keyword arguments passed to FunctionSubscriber.

        Returns:
            A decorator that registers the decorated function as an event subscriber.
        """

        def decorator(func):
            self.subscribe(
                FunctionSubscriber(func, middlewares=middlewares, **kwargs),
                target=target,
            )
            return func

        return decorator

    async def start(self) -> None:
        """
        Start all event consumers to begin receiving and dispatching events.

        Raises:
            ValueError: If no consumers are configured.
        """
        if not self.consumers:
            raise ValueError("No consumers configured")

        for _, consumer in self.consumers.items():
            await consumer.start()

    async def stop(self) -> None:
        """
        Stop all event consumers and close the event producer, performing any necessary cleanup.
        """
        for _, consumer in self.consumers.items():
            await consumer.stop()

        for _, producer in self.producers.items():
            await producer.close()
