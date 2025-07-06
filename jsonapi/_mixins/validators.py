import re
from typing import Any, Dict, Optional, Self

from pydantic import field_validator, model_validator


def _validate_string(value: str, field: str, pattern: str, example: str) -> str:
    if not re.match(pattern, value):
        raise ValueError(f"{field} must match pattern: {example}")
    return value


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
        return _validate_string(
            resource_type,
            "Resource type",
            r"^[a-z][a-z0-9_-]*$",
            "lowercase, hyphens, underscores",
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
        if not (
            getattr(self, "pointer", None)
            or getattr(self, "parameter", None)
            or getattr(self, "header", None)
        ):
            raise ValueError(
                "At least one of 'pointer', 'parameter', or 'header' must be set"
            )
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
        if not (
            href.startswith("http://")
            or href.startswith("https://")
            or href.startswith("/")
        ):
            raise ValueError("Link href must be a valid URL or relative path")
        return href


class QueryParamsValidatorMixin:
    @model_validator(mode="before")
    @classmethod
    def parse_query_params(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        parsed = values.copy()
        for key in ["include", "sort"]:
            if key in parsed and isinstance(parsed[key], str):
                parsed[key] = [v.strip() for v in parsed[key].split(",") if v.strip()]

        if "fields" in parsed and isinstance(parsed["fields"], dict):
            parsed["fields"] = {
                k: [v.strip() for v in v_str.split(",")]
                if isinstance(v_str, str)
                else v_str
                for k, v_str in parsed["fields"].items()
            }
        return parsed

    @model_validator(mode="after")
    def validate_query_structure(self) -> "Self":
        sort = getattr(self, "sort", None)
        fields = getattr(self, "fields", None)
        if sort:
            for field in sort:
                if not field.lstrip("-").replace("_", "").isalnum():
                    raise ValueError(f"Invalid sort field: {field}")

        if fields:
            for resource, fields_list in fields.items():
                if not all(isinstance(f, str) and f.strip() for f in fields_list):
                    raise ValueError(
                        f"All field names for {resource} must be non-empty strings"
                    )

        return self
