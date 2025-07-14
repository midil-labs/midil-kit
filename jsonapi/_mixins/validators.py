import re
from typing import Any, Dict, Optional, Self, List
from enum import Enum
from urllib.parse import urlparse

from pydantic import field_validator, model_validator


def _validate_string(value: str, field: str, pattern: str, example: str) -> str:
    if not re.match(pattern, value):
        raise ValueError(f"{field} must match pattern: {example}")
    return value


def _validate_url(url: str) -> str:
    """Validate URL format more comprehensively."""
    if not url:
        raise ValueError("URL cannot be empty")

    # Check for valid URL schemes
    if url.startswith(("http://", "https://")):
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValueError("Invalid URL: missing hostname")
            return url
        except Exception:
            raise ValueError("Invalid URL format")

    # Check for relative paths
    if url.startswith("/"):
        # Basic validation for relative paths
        if not re.match(r"^/[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;=%]*$", url):
            raise ValueError("Invalid relative path format")
        return url

    # Allow relative URLs without leading slash
    if re.match(r"^[a-zA-Z0-9\-._~:/?#[\]@!$&\'()*+,;=%]+$", url):
        return url

    raise ValueError("Invalid URL format")


class ResourceIdentifierValidatorMixin:
    @model_validator(mode="after")
    def validate_resource_identifier(self) -> "Self":
        if not getattr(self, "id", None) and not getattr(self, "lid", None):
            raise ValueError(
                "Either 'id' or 'lid' must be provided in a resource identifier"
            )
        return self

    @field_validator("id", "lid")
    def validate_id_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _validate_string(
            value, "ID field", r"^[a-zA-Z0-9_-]+$", "alphanumeric, hyphens, underscores"
        )

    @field_validator("type")
    def validate_resource_type(cls, resource_type: str) -> str:
        """Validate resource type allowing uppercase letters for better compliance."""
        return _validate_string(
            resource_type,
            "Resource type",
            r"^[a-zA-Z][a-zA-Z0-9_-]*$",  # Allow uppercase letters
            "alphanumeric, hyphens, underscores (uppercase allowed)",
        )


class ResourceValidatorMixin:
    @model_validator(mode="after")
    def validate_resource(self) -> "Self":
        if not getattr(self, "type", None):
            raise ValueError("The 'type' field is required in a resource")
        if not getattr(self, "id", None) and not getattr(self, "lid", None):
            raise ValueError(
                "At least one of 'id' or 'lid' must be present in a resource"
            )
        if not getattr(self, "attributes", None) and not getattr(
            self, "relationships", None
        ):
            raise ValueError(
                "At least one of 'attributes' or 'relationships' must be present"
            )
        return self


class ErrorSourceValidatorMixin:
    @model_validator(mode="after")
    def validate_source(self) -> "Self":
        # Make source validation optional as per JSON:API spec
        # The spec allows empty source objects
        return self

    @field_validator("pointer")
    def validate_json_pointer(cls, pointer: Optional[str]) -> Optional[str]:
        if pointer is None:
            return None
        if not isinstance(pointer, str) or not pointer.startswith("/"):
            raise ValueError("JSON pointer must be a string starting with '/'")
        return pointer


class JSONAPIErrorValidatorMixin:
    @model_validator(mode="after")
    def validate_error(self) -> "Self":
        if not (getattr(self, "title", None) or getattr(self, "detail", None)):
            raise ValueError(
                "At least one of 'title' or 'detail' must be set in an error object"
            )
        return self


class DocumentValidatorMixin:
    @model_validator(mode="after")
    def validate_document(self) -> "Self":
        if (
            getattr(self, "data", None) is not None
            and getattr(self, "errors", None) is not None
        ):
            raise ValueError("A document MUST NOT contain both 'data' and 'errors'")
        if (
            getattr(self, "data", None) is None
            and getattr(self, "errors", None) is None
            and getattr(self, "meta", None) is None
        ):
            raise ValueError(
                "A document MUST contain at least one of 'data', 'errors', or 'meta'"
            )
        return self


class LinkValidatorMixin:
    @model_validator(mode="after")
    def validate_link(self) -> "Self":
        if not getattr(self, "href", None):
            raise ValueError("The 'href' field is required in a link object")
        return self

    @field_validator("href")
    def validate_link_href(cls, href: str) -> Optional[str]:
        """Improved link href validation."""
        return _validate_url(href)


class FilterOperator(str, Enum):
    """Enumeration for filter operators."""

    EQ = "eq"  # equals
    NE = "ne"  # not equals
    LT = "lt"  # less than
    LE = "le"  # less than or equal
    GT = "gt"  # greater than
    GE = "ge"  # greater than or equal
    LIKE = "like"  # contains
    IN = "in"  # in list
    NOT_IN = "not_in"  # not in list


def _validate_field_name(field_name: str) -> str:
    """Validate field name format."""
    if not re.match(
        r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*$", field_name
    ):
        raise ValueError(f"Invalid field name: {field_name}")
    return field_name


def _validate_relationship_path(path: str) -> str:
    """Validate relationship path format."""
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*$", path):
        raise ValueError(f"Invalid relationship path: {path}")
    return path


def _sanitize_query_param(value: str) -> str:
    """Sanitize query parameter to prevent injection attacks."""
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', "", value)
    # Limit length to prevent resource exhaustion
    if len(sanitized) > 1000:
        raise ValueError("Query parameter too long")
    return sanitized


class QueryParamsValidatorMixin:
    """Mixin for validating JSON:API query parameters."""

    @field_validator("include")
    @classmethod
    def validate_include(cls, include: Optional[List[str]]) -> Optional[List[str]]:
        """Validate include relationships."""
        if include is None:
            return None

        validated = []
        for relationship in include:
            validated.append(_validate_relationship_path(relationship))
        return validated

    @field_validator("sort")
    @classmethod
    def validate_sort(
        cls, sort: Optional[List[Dict[str, str]]]
    ) -> Optional[List[Dict[str, str]]]:
        """Validate sort fields."""
        if sort is None:
            return None

        validated = []
        for sort_item in sort:
            field = sort_item.get("field", "")
            direction = sort_item.get("direction", "asc")

            _validate_field_name(field)
            if direction not in ["asc", "desc"]:
                raise ValueError(f"Invalid sort direction: {direction}")

            validated.append({"field": field, "direction": direction})
        return validated

    @field_validator("fields")
    @classmethod
    def validate_fields(
        cls, fields: Optional[Dict[str, List[str]]]
    ) -> Optional[Dict[str, List[str]]]:
        """Validate sparse fieldsets."""
        if fields is None:
            return None

        validated = {}
        for resource_type, field_list in fields.items():
            if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", resource_type):
                raise ValueError(f"Invalid resource type: {resource_type}")

            validated_fields = []
            for field in field_list:
                validated_fields.append(_validate_field_name(field))
            validated[resource_type] = validated_fields

        return validated

    @field_validator("filters")
    @classmethod
    def validate_filters(
        cls, filters: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        """Validate filter conditions."""
        if filters is None:
            return None

        validated = []
        for filter_item in filters:
            field = filter_item.get("field", "")
            operator = filter_item.get("operator", "eq")
            value = filter_item.get("value")

            _validate_field_name(field)
            if operator not in [op.value for op in FilterOperator]:
                raise ValueError(f"Invalid filter operator: {operator}")

            if operator in ["in", "not_in"] and not isinstance(value, list):
                raise ValueError(f"Filter operator {operator} requires list value")

            validated.append({"field": field, "operator": operator, "value": value})

        return validated

    @model_validator(mode="after")
    def validate_pagination_consistency(self) -> Self:
        """Validate pagination parameter consistency."""
        pagination = getattr(self, "pagination", None)
        if not pagination:
            return self

        has_page_based = "number" in pagination or "size" in pagination
        has_offset_based = "offset" in pagination or "limit" in pagination
        has_cursor_based = "cursor" in pagination

        pagination_types = sum([has_page_based, has_offset_based, has_cursor_based])
        if pagination_types > 1:
            raise ValueError(
                "Cannot mix different pagination strategies (page-based, offset-based, cursor-based)"
            )

        # Validate individual parameters
        for param, value in pagination.items():
            if param in ["number", "size", "limit"] and value < 1:
                raise ValueError(f"Pagination parameter {param} must be >= 1")
            elif param == "offset" and value < 0:
                raise ValueError("Pagination offset must be >= 0")

        return self
