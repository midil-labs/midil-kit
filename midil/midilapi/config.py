from pydantic import BaseModel
from typing import Annotated, Literal
from pydantic import Field

LogLevelType = Literal["ERROR", "WARNING", "INFO", "DEBUG", "CRITICAL"]


class MidilApiConfig(BaseModel, extra="allow"):
    database_uri: Annotated[
        str, Field(..., description="Database URI or connection string.")
    ]
    enable_http_logging: Annotated[
        bool, Field(default=True, description="Enable HTTP request/response logging.")
    ]
    port: Annotated[
        int, Field(default=8000, description="Port on which the application will run.")
    ]

    log_level: Annotated[
        LogLevelType,
        Field(
            default="INFO",
            description="Logging level: ERROR, WARNING, INFO, DEBUG, CRITICAL.",
        ),
    ]
