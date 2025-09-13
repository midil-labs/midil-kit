from enum import Enum
from typing import Dict, Optional, Literal, TypeVar, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from midil.auth.config import AuthConfig
from midil.midilapi.config import MidilApiConfig
from midil.event.config import (
    EventConfig,
    ConsumerConfig,
    ProducerConfig,
    EventConsumerType,
    EventProducerType,
)
from functools import lru_cache
from loguru import logger

T = TypeVar("T", bound=BaseSettings)


class _BaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MIDIL__",
        env_file=".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


class MIDILSettings(_BaseSettings):
    api: Optional[MidilApiConfig] = None
    auth: Optional[AuthConfig] = None
    event: Optional[EventConfig] = None

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation of settings."""
        if self.event and self.event.consumers is None and self.event.producers is None:
            raise EventSettingsError(
                "Event settings are configured but contain no producers or consumers. "
                "Ensure at least one producer or consumer is defined in MIDIL__EVENT."
            )


class SettingsError(Exception):
    """Base exception for settings-related errors."""


class AuthSettingsError(SettingsError):
    """Exception for authentication settings errors."""


class EventSettingsError(SettingsError):
    """Exception for event settings errors."""


class ApiSettingsError(SettingsError):
    """Exception for API settings errors."""


class AuthType(str, Enum):
    COGNITO = "cognito"


@lru_cache(maxsize=1)
def get_settings() -> MIDILSettings:
    """Get the singleton MIDILSettings instance, cached for performance."""
    logger.info("Loading MIDIL settings from environment or .env file")
    settings = MIDILSettings()
    return settings


def get_api_settings() -> MidilApiConfig:
    """Get API settings, raising an error if not configured."""
    settings = get_settings()
    if settings.api is None:
        raise ApiSettingsError(
            "API settings are not configured. Ensure MIDIL__API is set in the .env file."
        )
    return settings.api


def get_event_settings() -> EventConfig:
    """Get event settings, raising an error if not configured."""
    settings = get_settings()
    if settings.event is None:
        raise EventSettingsError(
            "Event settings are not configured. Ensure MIDIL__EVENT is set in the .env file."
        )
    return settings.event


def get_auth_settings(expected: Literal["cognito"]) -> AuthConfig:
    """
    Get and validate authentication settings by type.

    Args:
        expected: The expected authentication type (e.g., "cognito").

    Raises:
        AuthSettingsError: If auth settings are missing or the type doesn't match.

    Example:
        >>> settings = get_auth_settings("cognito")
    """
    settings = get_settings()
    if settings.auth is None:
        raise AuthSettingsError(
            f"Authentication settings for '{expected}' not configured. "
            "Ensure MIDIL__AUTH__TYPE=cognito is set in the .env file."
        )
    if settings.auth.type != expected:
        raise AuthSettingsError(
            f"Expected auth type '{expected}', got '{settings.auth.type}'. "
            "Check MIDIL__AUTH__TYPE in the .env file."
        )
    return settings.auth


def get_consumer_event_settings(name: str) -> ConsumerConfig:
    """
    Get consumer configuration by name.

    Args:
        name: The name of the consumer configuration.

    Raises:
        EventSettingsError: If the consumer is not found.

    Example:
        >>> consumer = get_consumer_event_settings("sqs_consumer")
    """
    consumers = get_event_settings().consumers
    if consumers is None:
        raise EventSettingsError(
            "No consumer configurations found. Ensure MIDIL__EVENT__CONSUMERS is set."
        )
    try:
        return consumers[name]
    except KeyError:
        available = list(consumers.keys())
        raise EventSettingsError(
            f"Consumer '{name}' not found. Available consumers: {available}. "
            "Check MIDIL__EVENT__CONSUMERS in the .env file."
        )


def get_producer_event_settings(name: str) -> ProducerConfig:
    """
    Get producer configuration by name.

    Args:
        name: The name of the producer configuration.

    Raises:
        EventSettingsError: If the producer is not found.

    Example:
        >>> producer = get_producer_event_settings("sqs_producer")
    """
    producers = get_event_settings().producers
    if producers is None:
        raise EventSettingsError(
            "No producer configurations found. Ensure MIDIL__EVENT__PRODUCERS is set."
        )
    try:
        return producers[name]
    except KeyError:
        available = list(producers.keys())
        raise EventSettingsError(
            f"Producer '{name}' not found. Available producers: {available}. "
            "Check MIDIL__EVENT__PRODUCERS in the .env file."
        )


def get_consumers_by_type(type: EventConsumerType) -> Dict[str, ConsumerConfig]:
    """
    Get all consumer configurations of a specific type.

    Args:
        type: The consumer type (e.g., EventConsumerType.SQS).

    Raises:
        EventSettingsError: If no consumers of the specified type are found.

    Example:
        >>> sqs_consumers = get_consumers_by_type(EventConsumerType.SQS)
    """
    consumers = get_event_settings().consumers
    if consumers is None:
        raise EventSettingsError(
            "No consumer configurations found. Ensure MIDIL__EVENT__CONSUMERS is set."
        )
    filtered = {
        name: consumer
        for name, consumer in consumers.items()
        if consumer.type == type.value
    }
    if not filtered:
        raise EventSettingsError(
            f"No consumer configurations with type '{type}'. Available types: "
            f"{[c.type for c in consumers.values()]}. Check MIDIL__EVENT__CONSUMERS."
        )
    return filtered


def get_producers_by_type(type: EventProducerType) -> Dict[str, ProducerConfig]:
    """
    Get all producer configurations of a specific type.

    Args:
        type: The producer type (e.g., EventProducerType.SQS).

    Raises:
        EventSettingsError: If no producers of the specified type are found.

    Example:
        >>> sqs_producers = get_producers_by_type(EventProducerType.SQS)
    """
    producers = get_event_settings().producers
    if producers is None:
        raise EventSettingsError(
            "No producer configurations found. Ensure MIDIL__EVENT__PRODUCERS is set."
        )
    filtered = {
        name: producer
        for name, producer in producers.items()
        if producer.type == type.value
    }
    if not filtered:
        raise EventSettingsError(
            f"No producer configurations with type '{type}'. Available types: "
            f"{[p.type for p in producers.values()]}. Check MIDIL__EVENT__PRODUCERS."
        )
    return filtered


def list_available_consumers() -> Dict[str, str]:
    """
    List all available consumer names and their types for debugging.

    Returns:
        A dictionary mapping consumer names to their types.

    Example:
        >>> consumers = list_available_consumers()
        >>> print(consumers)  # {'sqs_consumer': 'sqs', 'webhook_consumer': 'webhook'}
    """
    consumers = get_event_settings().consumers
    return (
        {name: consumer.type for name, consumer in consumers.items()}
        if consumers
        else {}
    )


def list_available_producers() -> Dict[str, str]:
    """
    List all available producer names and their types for debugging.

    Returns:
        A dictionary mapping producer names to their types.

    Example:
        >>> producers = list_available_producers()
        >>> print(producers)  # {'sqs_producer': 'sqs', 'redis_producer': 'redis'}
    """
    producers = get_event_settings().producers
    return (
        {name: producer.type for name, producer in producers.items()}
        if producers
        else {}
    )
