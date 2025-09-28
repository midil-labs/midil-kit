from typing import Literal
from midil.logger.utils import resolve_hostname
from midil.utils.models import SnakeCaseModel
from pydantic import Field
import uuid

LogLevelType = Literal["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"]


class LoggerConfig(SnakeCaseModel):
    log_level: LogLevelType = Field(default="INFO")
    enable_http_logging: bool = Field(default=False)
    hostname: str = Field(default=resolve_hostname())
    instance_id: str = Field(default=str(uuid.uuid4()))
