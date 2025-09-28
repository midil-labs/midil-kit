from midil.utils.models import SnakeCaseModel
from pydantic import Field


class ServerConfig(SnakeCaseModel):
    host: str = Field(
        default="0.0.0.0", description="Host on which the application will run."
    )
    port: int = Field(
        default=8000, description="Port on which the application will run."
    )


class MidilApiConfig(SnakeCaseModel, extra="allow"):
    server: ServerConfig = Field(
        default=ServerConfig(), description="Server configuration."
    )
