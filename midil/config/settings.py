from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    EnvSettingsSource,
)
from typing import Annotated, Literal, Optional
from pydantic import Field

LogLevelType = Literal["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"]


class ApplicationSettings(BaseSettings):
    log_level: Annotated[
        LogLevelType,
        Field(
            default="INFO",
            description="The logging level for the application. One of: ERROR, WARNING, INFO, DEBUG, CRITICAL.",
        ),
    ]
    enable_http_logging: Annotated[
        bool,
        Field(
            default=True,
            description="Whether to enable HTTP request/response logging.",
        ),
    ]
    port: Annotated[
        int,
        Field(
            default=8000,
            description="The port on which the application will run.",
        ),
    ]

    class Config:
        env_prefix = "APPLICATION__"
        env_file = ".env"
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings: InitSettingsSource,
            env_settings: EnvSettingsSource,
            *_,
            **__,
        ):
            """Customizes the order of settings sources. Environment variables take precedence over init settings."""
            return env_settings, init_settings


class CognitoSettings(BaseSettings):
    user_pool_id: Annotated[
        str,
        Field(
            ...,
            description="The Cognito User Pool ID.",
        ),
    ]
    client_id: Annotated[
        str,
        Field(
            ...,
            description="The Cognito App Client ID.",
        ),
    ]
    client_secret: Annotated[
        Optional[str],
        Field(
            default=None,
            description="The Cognito App Client Secret (optional).",
        ),
    ]
    region: Annotated[
        str,
        Field(
            ...,
            description="The AWS region for Cognito.",
        ),
    ]

    class Config:
        env_prefix = "COGNITO__"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"


class DatabaseSettings(BaseSettings):
    uri: Annotated[
        str,
        Field(
            ...,
            description="Database URI or connection string",
        ),
    ]

    class Config:
        env_prefix = "MIDIL_DATABASE__"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
