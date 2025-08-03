from typing import Optional, Self

from pydantic import field_validator, model_validator


class ResourceIdentifierValidatorMixin:
    @model_validator(mode="after")
    def validate_resource_identifier(self) -> "Self":
        if not getattr(self, "id", None) and not getattr(self, "lid", None):
            raise ValueError(
                "Either 'id' or 'lid' must be provided in a resource identifier"
            )
        return self


class ResourceValidatorMixin:
    @model_validator(mode="after")
    def validate_resource(self) -> "Self":
        if not getattr(self, "type", None):
            raise ValueError("The 'type' field is required in a resource")
        if not getattr(self, "id", None) and not getattr(self, "lid", None):
            raise ValueError(
                "At least one of 'id' or 'lid' must be present in a resource"
            )
        return self


class ErrorSourceValidatorMixin:
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
