from __future__ import annotations

from typing import Annotated, Union, TypeAlias, Optional, Literal

from pydantic import Field, Json
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from midil.auth.config import AuthConfig
from midil.midilapi.config import MidilApiConfig
from midil.event.config import EventConfig
from midil.event.config import ConsumerConfig, ProducerConfig

AuthField: TypeAlias = Annotated[
    Union[AuthConfig, Json[AuthConfig]],
    Field(..., description="Auth provider configuration"),
]

ApiField: TypeAlias = Annotated[
    Union[MidilApiConfig, Json[MidilApiConfig]],
    Field(..., description="API configuration"),
]


EventField: TypeAlias = Annotated[
    Union[EventConfig, Json[EventConfig]],
    Field(..., description="Event configuration"),
]


class _BaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MIDIL__",
        env_file=".env",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AuthSettings(_BaseSettings):
    auth: AuthField


class EventSettings(_BaseSettings):
    event: EventField


class APISettings(_BaseSettings):
    api: ApiField


class MIDILSettings(_BaseSettings):
    api: Optional[ApiField] = None
    auth: Optional[AuthField] = None
    event: Optional[EventField] = None


class SettingsError(Exception):
    """Custom exception for settings errors."""


class AuthSettingsError(SettingsError):
    """Custom exception for authentication settings errors."""


class EventSettingsError(SettingsError):
    """Custom exception for event settings errors."""


def get_auth_settings(type: Literal["cognito"]) -> AuthConfig:
    midil_settings = MIDILSettings()
    auth_settings = midil_settings.auth
    if auth_settings is None:
        raise AuthSettingsError(
            "Cognito authentication settings are not configured. "
            "Please ensure your configuration specifies 'type: cognito'."
        )
    if type == "cognito":
        if auth_settings.type != "cognito":
            raise AuthSettingsError(
                "CognitoAuthMiddleware requires Cognito authentication settings. "
                "Please ensure your configuration specifies 'type: cognito'."
            )
        return auth_settings


def get_consumer_event_settings(type: Literal["sqs", "webhook"]) -> ConsumerConfig:
    midil_settings = MIDILSettings()
    event_settings = midil_settings.event
    if event_settings is None:
        raise EventSettingsError(
            "Event settings are not configured. "
            "Please ensure your configuration specifies 'type: sqs' or 'type: webhook'."
        )

    if event_settings.consumer is None:
        raise EventSettingsError(
            "Event settings are not configured. "
            "Please ensure your configuration specifies 'type: sqs' or 'type: webhook'."
        )
    consumer_config: ConsumerConfig = event_settings.consumer
    if type == "sqs" and consumer_config.type != "sqs":
        raise EventSettingsError(
            "SQSEventConsumer requires SQS event settings. "
            "Please ensure your configuration specifies 'type: sqs'."
        )
    elif type == "webhook" and consumer_config.type != "webhook":
        raise EventSettingsError(
            "WebhookEventConsumer requires Webhook event settings. "
            "Please ensure your configuration specifies 'type: webhook'."
        )
    return consumer_config


def get_producer_event_settings(type: Literal["sqs", "redis"]) -> ProducerConfig:
    midil_settings = MIDILSettings()
    event_settings = midil_settings.event
    if event_settings is None:
        raise EventSettingsError(
            "Event settings are not configured. "
            "Please ensure your configuration specifies 'type: sqs' or 'type: redis'."
        )
    if event_settings.producer is None:
        raise EventSettingsError(
            "Event settings are not configured. "
            "Please ensure your configuration specifies 'type: sqs' or 'type: redis'."
        )
    producer_config: ProducerConfig = event_settings.producer
    if type == "sqs" and producer_config.type != "sqs":
        raise EventSettingsError(
            "SQSProducerEventConfig requires SQS event settings. "
            "Please ensure your configuration specifies 'type: sqs'."
        )
    elif type == "redis" and producer_config.type != "redis":
        raise EventSettingsError(
            "RedisProducerEventConfig requires Redis event settings. "
            "Please ensure your configuration specifies 'type: redis'."
        )
    return producer_config
