from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Any, Dict
from midil.midilapi.exceptions import register_jsonapi_exception_handlers
from midil.midilapi.responses import JSONAPIResponse
from midil.midilapi.utils import _update_openapi_jsonapi_media_types


class MidilAPI(FastAPI):
    """
    FastAPI subclass that globally sets JSON:API media types in OpenAPI schema.
    """

    def openapi(self) -> Dict[str, Any]:
        if self.openapi_schema:
            return self.openapi_schema

        openapi_schema = get_openapi(
            title=self.title,
            version=self.version,
            routes=self.routes,
            description=self.description,
        )

        _update_openapi_jsonapi_media_types(openapi_schema)

        self.openapi_schema = openapi_schema
        return self.openapi_schema


__all__ = ["MidilAPI", "register_jsonapi_exception_handlers", "JSONAPIResponse"]
