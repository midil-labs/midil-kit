from __future__ import annotations

from typing import Annotated, Union, TypeAlias, Optional

from pydantic import Field, Json
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from midil.auth.config import AuthConfig
from midil.midilapi.config import MidilApiConfig
from midil.event.config import EventConfig


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
    api: ApiField
    auth: AuthField
    event: Optional[EventField] = None


if __name__ == "__main__":
    settings = APISettings()
    print(settings.model_dump_json())
