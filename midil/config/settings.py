from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field, Json, SecretStr, model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
)


LogLevelType = Literal["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"]


class CognitoAuthConfig(BaseModel):
    type: Literal["cognito"] = "cognito"
    user_pool_id: str = Field(..., description="Cognito User Pool ID")
    client_id: str = Field(..., description="Cognito App Client ID")
    client_secret: Optional[SecretStr] = Field(
        None, description="Cognito App Client Secret (optional)"
    )
    region: str = Field(..., description="AWS region for Cognito")


AuthConfig = Annotated[Union[CognitoAuthConfig], Field(discriminator="type")]


class AuthSettings(BaseSettings):
    # Accept either a structured object (via flat envs) or JSON blob
    config: Annotated[
        Union[AuthConfig, Json[AuthConfig]],
        Field(..., description="Auth provider configuration."),
    ]

    model_config = SettingsConfigDict(
        env_prefix="MIDIL__AUTH__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    @model_validator(mode="after")
    def validate_discriminated(self) -> "AuthSettings":
        """
        Ensure 'config' resolves to a concrete AuthConfig with a valid 'type'.
        Union+discriminator already enforces structure; this makes errors explicit.
        """
        cfg = self.config
        # If config was provided as JSON, pydantic already parsed it into a model
        if isinstance(cfg, dict):
            # Defensive (shouldn't happen due to typing), but keep message crisp
            raise ValueError("Auth 'config' must be a valid object; got plain dict.")
        # Add any cross-field constraints in future providers here.
        return self


class ServiceSettings(BaseSettings):
    database_uri: Annotated[
        str, Field(..., description="Database URI or connection string.")
    ]
    log_level: Annotated[
        LogLevelType,
        Field(
            default="INFO",
            description="Logging level: ERROR, WARNING, INFO, DEBUG, CRITICAL.",
        ),
    ]
    enable_http_logging: Annotated[
        bool, Field(default=True, description="Enable HTTP request/response logging.")
    ]
    port: Annotated[
        int, Field(default=8000, description="Port on which the application will run.")
    ]

    model_config = SettingsConfigDict(
        env_prefix="MIDIL__SERVICE__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    @classmethod
    def settings_customise_sources(  # env > init > .env > secrets
        cls,
        settings_cls,
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings,
        file_secret_settings,
    ):
        return env_settings, init_settings, dotenv_settings, file_secret_settings


class PollingListenerConfig(BaseModel):
    type: Literal["polling"] = "polling"
    max_messages: int = Field(
        default=10, ge=1, description="Max number of messages per batch."
    )
    wait_time: int = Field(
        default=20, ge=0, description="Wait time for messages (seconds)."
    )
    poll_interval: float = Field(
        default=1.0, gt=0, description="Polling interval (seconds)."
    )
    visibility_timeout: int = Field(
        default=60, ge=0, description="Visibility timeout (seconds)."
    )
    concurrency: int = Field(
        default=10, ge=1, description="Concurrency level for the event listener."
    )
    default_failure_policy: Literal["abort", "continue", "compensate"] = Field(
        default="abort"
    )
    default_timeout_seconds: int = Field(
        default=5, ge=0, le=30, description="Default timeout (seconds)."
    )
    default_retry_policy: Literal["no_retry", "exponential_backoff"] = Field(
        default="no_retry"
    )

    @model_validator(mode="after")
    def validate_polling(self) -> "PollingListenerConfig":
        if (
            self.visibility_timeout
            and self.wait_time
            and self.visibility_timeout <= self.wait_time
        ):
            # Common SQS-like best practice: visibility timeout should exceed long-poll wait time
            raise ValueError(
                "visibility_timeout should be greater than wait_time for polling listeners."
            )
        return self


# Discriminated union for future listener types
EventListenerConfig = Annotated[
    Union[PollingListenerConfig], Field(discriminator="type")
]


class EventListenerSettings(BaseSettings):
    # Accept either structured object (via flat envs) or JSON blob
    config: Annotated[
        Union[EventListenerConfig, Json[EventListenerConfig]],
        Field(..., description="Event listener configuration."),
    ]

    model_config = SettingsConfigDict(
        env_prefix="MIDIL__EVENT__LISTENER__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    @model_validator(mode="after")
    def validate_listener(self) -> "EventListenerSettings":
        cfg = self.config
        if isinstance(cfg, dict):
            # Defensive guard (shouldn't happen because typing parses Json -> model)
            raise ValueError(
                "Event listener 'config' must be a valid object; got plain dict."
            )
        # Add cross-type rules here when new listener types are added.
        return self


class Settings(BaseSettings):
    auth: AuthSettings = AuthSettings()  # type: ignore
    service: ServiceSettings = ServiceSettings()  # type: ignore
    event_listener: EventListenerSettings = EventListenerSettings()  # type: ignore

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def auth_type(self) -> str:
        return self.auth.config.type  # e.g., "cognito"

    @property
    def listener_type(self) -> str:
        return self.event_listener.config.type  # e.g., "polling"
