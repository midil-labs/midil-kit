from typing import Optional, Set, Dict, Any
from fastapi import Request, HTTPException, status
from jsonapi.document import (
    JSONAPIQueryParams,
    JSONAPIDocument,
    JSONAPI_CONTENT_TYPE,
)
from jsonapi.utils import validate_content_type
from jsonapi._mixins.validators import FilterOperator
from jsonapi.extensions.utils import JSONAPIQueryValidator


class JSONAPIQueryDependency:
    """FastAPI dependency for JSON:API query parameters."""

    def __init__(self, validator: Optional[JSONAPIQueryValidator] = None):
        self.validator = validator

    def __call__(self, request: Request) -> JSONAPIQueryParams:
        """FastAPI dependency callable."""
        query_params = dict(request.query_params)
        params = JSONAPIQueryParams.model_validate(query_params)

        if self.validator:
            errors = self.validator.validate(params)
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=JSONAPIDocument[Any](errors=errors).model_dump(),
                )

        return params


def validate_jsonapi_content_type(request: Request) -> None:
    """Validate that the request has the correct JSON:API content type."""
    content_type = request.headers.get("content-type", "")
    if not validate_content_type(content_type):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "errors": [
                    {
                        "title": "Unsupported Media Type",
                        "detail": f"Content-Type must be '{JSONAPI_CONTENT_TYPE}'",
                        "status": "415",
                    }
                ]
            },
        )


def validate_jsonapi_accept_header(request: Request) -> None:
    """Validate that the request accepts JSON:API content type."""
    accept = request.headers.get("accept", "")
    if accept and JSONAPI_CONTENT_TYPE not in accept:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail={
                "errors": [
                    {
                        "title": "Not Acceptable",
                        "detail": f"Accept header must include '{JSONAPI_CONTENT_TYPE}'",
                        "status": "406",
                    }
                ]
            },
        )


def create_jsonapi_headers_dependency(
    request: Request,
) -> None:
    """Validate the JSON:API headers for FastAPI."""
    validate_jsonapi_content_type(request)
    validate_jsonapi_accept_header(request)


def create_jsonapi_querydependency(
    allowed_fields: Optional[Set[str]] = None,
    allowed_relationships: Optional[Set[str]] = None,
    allowed_sort_fields: Optional[Set[str]] = None,
    allowed_filter_fields: Optional[Set[str]] = None,
    allowed_filter_operators: Optional[Dict[str, Set[FilterOperator]]] = None,
    max_page_size: Optional[int] = None,
    max_includes: Optional[int] = None,
) -> JSONAPIQueryDependency:
    """Create a configured JSON:API query dependency for FastAPI."""
    validator = JSONAPIQueryValidator(
        allowed_fields=allowed_fields,
        allowed_relationships=allowed_relationships,
        allowed_sort_fields=allowed_sort_fields,
        allowed_filter_fields=allowed_filter_fields,
        allowed_filter_operators=allowed_filter_operators,
        max_page_size=max_page_size,
        max_includes=max_includes,
    )
    return JSONAPIQueryDependency(validator)
