"""
Tests for midil.jsonapi._mixins.validators
"""
import pytest
from typing import Dict, Any
from pydantic import BaseModel, ValidationError, field_validator

from midil.jsonapi._mixins.validators import (
    ResourceIdentifierValidatorMixin,
    ResourceValidatorMixin,
    ErrorSourceValidatorMixin,
    JSONAPIErrorValidatorMixin,
    DocumentValidatorMixin,
)


class TestResourceIdentifierValidatorMixin:
    """Tests for ResourceIdentifierValidatorMixin."""

    def test_resource_identifier_with_id(self):
        """Test resource identifier validation with id."""

        class TestResourceIdentifier(BaseModel, ResourceIdentifierValidatorMixin):
            type: str
            id: str = None
            lid: str = None

        # Valid with id
        resource = TestResourceIdentifier(type="users", id="123")
        assert resource.id == "123"
        assert resource.lid is None

    def test_resource_identifier_with_lid(self):
        """Test resource identifier validation with lid."""

        class TestResourceIdentifier(BaseModel, ResourceIdentifierValidatorMixin):
            type: str
            id: str = None
            lid: str = None

        # Valid with lid
        resource = TestResourceIdentifier(type="users", lid="local-123")
        assert resource.lid == "local-123"
        assert resource.id is None

    def test_resource_identifier_with_both_id_and_lid(self):
        """Test resource identifier validation with both id and lid."""

        class TestResourceIdentifier(BaseModel, ResourceIdentifierValidatorMixin):
            type: str
            id: str = None
            lid: str = None

        # Valid with both
        resource = TestResourceIdentifier(type="users", id="123", lid="local-123")
        assert resource.id == "123"
        assert resource.lid == "local-123"

    def test_resource_identifier_without_id_or_lid(self):
        """Test resource identifier validation fails without id or lid."""

        class TestResourceIdentifier(BaseModel, ResourceIdentifierValidatorMixin):
            type: str
            id: str = None
            lid: str = None

        # Should fail without id or lid
        with pytest.raises(
            ValidationError, match="Either 'id' or 'lid' must be provided"
        ):
            TestResourceIdentifier(type="users")

    def test_resource_identifier_with_empty_values(self):
        """Test resource identifier validation with empty string values."""

        class TestResourceIdentifier(BaseModel, ResourceIdentifierValidatorMixin):
            type: str
            id: str = None
            lid: str = None

        # Empty strings should be treated as None/falsy
        with pytest.raises(
            ValidationError, match="Either 'id' or 'lid' must be provided"
        ):
            TestResourceIdentifier(type="users", id="", lid="")


class TestResourceValidatorMixin:
    """Tests for ResourceValidatorMixin."""

    def test_resource_with_valid_data(self):
        """Test resource validation with valid data."""

        class TestResource(BaseModel, ResourceValidatorMixin):
            type: str
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        # Valid with id and attributes
        resource = TestResource(type="users", id="123", attributes={"name": "John Doe"})
        assert resource.type == "users"
        assert resource.id == "123"
        assert resource.attributes == {"name": "John Doe"}

    def test_resource_without_type(self):
        """Test resource validation fails without type."""

        class TestResource(BaseModel, ResourceValidatorMixin):
            type: str = None
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        with pytest.raises(ValidationError, match="The 'type' field is required"):
            TestResource(id="123", attributes={"name": "John"})

    def test_resource_without_id_or_lid(self):
        """Test resource validation fails without id or lid."""

        class TestResource(BaseModel, ResourceValidatorMixin):
            type: str
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        with pytest.raises(
            ValidationError, match="At least one of 'id' or 'lid' must be present"
        ):
            TestResource(type="users", attributes={"name": "John"})

    def test_resource_without_attributes_or_relationships(self):
        """Test resource validation allows minimal resources without attributes or relationships."""

        class TestResource(BaseModel, ResourceValidatorMixin):
            type: str
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        # Should now be valid without attributes or relationships
        resource = TestResource(type="users", id="123")
        assert resource.type == "users"
        assert resource.id == "123"

    def test_resource_with_relationships_only(self):
        """Test resource validation with relationships only."""

        class TestResource(BaseModel, ResourceValidatorMixin):
            type: str
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        # Valid with relationships only
        resource = TestResource(
            type="users", id="123", relationships={"posts": {"data": []}}
        )
        assert resource.relationships is not None
        assert resource.attributes is None

    def test_resource_with_both_attributes_and_relationships(self):
        """Test resource validation with both attributes and relationships."""

        class TestResource(BaseModel, ResourceValidatorMixin):
            type: str
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        # Valid with both
        resource = TestResource(
            type="users",
            id="123",
            attributes={"name": "John"},
            relationships={"posts": {"data": []}},
        )
        assert resource.attributes is not None
        assert resource.relationships is not None

    def test_resource_with_lid_instead_of_id(self):
        """Test resource validation with lid instead of id."""

        class TestResource(BaseModel, ResourceValidatorMixin):
            type: str
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        # Valid with lid
        resource = TestResource(
            type="users", lid="local-123", attributes={"name": "John"}
        )
        assert resource.lid == "local-123"
        assert resource.id is None


class TestErrorSourceValidatorMixin:
    """Tests for ErrorSourceValidatorMixin."""

    def test_error_source_valid_pointer(self):
        """Test error source validation with valid JSON pointer."""

        class TestErrorSource(BaseModel, ErrorSourceValidatorMixin):
            pointer: str | None = None
            parameter: str | None = None
            header: str | None = None

        # Valid JSON pointers
        valid_pointers = [
            "/data",
            "/data/attributes/name",
            "/data/0/attributes/email",
            "/included/0/type",
            "/",
        ]

        for pointer in valid_pointers:
            source = TestErrorSource(pointer=pointer)
            assert source.pointer == pointer

    def test_error_source_invalid_pointer(self):
        """Test error source validation with invalid JSON pointer."""

        class TestErrorSource(BaseModel, ErrorSourceValidatorMixin):
            pointer: str | None = None
            parameter: str | None = None
            header: str | None = None

        # Invalid JSON pointers (don't start with /)
        invalid_pointers = ["data", "data/attributes/name", "invalid", "123"]

        for pointer in invalid_pointers:
            with pytest.raises(
                ValidationError, match="JSON pointer must be a string starting with '/'"
            ):
                TestErrorSource(pointer=pointer)

    def test_error_source_none_pointer(self):
        """Test error source validation with None pointer."""

        class TestErrorSource(BaseModel, ErrorSourceValidatorMixin):
            pointer: str | None = None
            parameter: str | None = None
            header: str | None = None

        # None should be valid
        source = TestErrorSource(pointer=None)
        assert source.pointer is None

    def test_error_source_other_fields(self):
        """Test error source with parameter and header fields."""

        class TestErrorSource(BaseModel, ErrorSourceValidatorMixin):
            pointer: str | None = None
            parameter: str | None = None
            header: str | None = None

        # Other fields should not be validated
        source = TestErrorSource(parameter="filter[name]", header="Authorization")
        assert source.parameter == "filter[name]"
        assert source.header == "Authorization"


class TestJSONAPIErrorValidatorMixin:
    """Tests for JSONAPIErrorValidatorMixin."""

    def test_error_with_title(self):
        """Test error validation with title."""

        class TestError(BaseModel, JSONAPIErrorValidatorMixin):
            title: str = None
            detail: str = None
            status: str = None
            code: str = None

        # Valid with title
        error = TestError(title="Validation Error")
        assert error.title == "Validation Error"

    def test_error_with_detail(self):
        """Test error validation with detail."""

        class TestError(BaseModel, JSONAPIErrorValidatorMixin):
            title: str = None
            detail: str = None
            status: str = None
            code: str = None

        # Valid with detail
        error = TestError(detail="Name field is required")
        assert error.detail == "Name field is required"

    def test_error_with_both_title_and_detail(self):
        """Test error validation with both title and detail."""

        class TestError(BaseModel, JSONAPIErrorValidatorMixin):
            title: str = None
            detail: str = None
            status: str = None
            code: str = None

        # Valid with both
        error = TestError(title="Validation Error", detail="Name field is required")
        assert error.title == "Validation Error"
        assert error.detail == "Name field is required"

    def test_error_without_title_or_detail(self):
        """Test error validation fails without title or detail."""

        class TestError(BaseModel, JSONAPIErrorValidatorMixin):
            title: str = None
            detail: str = None
            status: str = None
            code: str = None

        with pytest.raises(
            ValidationError, match="At least one of 'title' or 'detail' must be set"
        ):
            TestError(status="400", code="VALIDATION_ERROR")

    def test_error_with_other_fields_only(self):
        """Test error validation with only status and code."""

        class TestError(BaseModel, JSONAPIErrorValidatorMixin):
            title: str = None
            detail: str = None
            status: str = None
            code: str = None

        # Should fail without title or detail
        with pytest.raises(
            ValidationError, match="At least one of 'title' or 'detail' must be set"
        ):
            TestError(status="500", code="INTERNAL_ERROR")

    def test_error_with_empty_strings(self):
        """Test error validation with empty string values."""

        class TestError(BaseModel, JSONAPIErrorValidatorMixin):
            title: str = None
            detail: str = None
            status: str = None
            code: str = None

        # Empty strings should be treated as falsy
        with pytest.raises(
            ValidationError, match="At least one of 'title' or 'detail' must be set"
        ):
            TestError(title="", detail="")


class TestDocumentValidatorMixin:
    """Tests for DocumentValidatorMixin."""

    def test_document_with_data_only(self):
        """Test document validation with data only."""

        class TestDocument(BaseModel, DocumentValidatorMixin):
            data: dict = None
            errors: list = None
            meta: dict = None

        # Valid with data
        doc = TestDocument(data={"type": "users", "id": "1"})
        assert doc.data is not None
        assert doc.errors is None

    def test_document_with_errors_only(self):
        """Test document validation with errors only."""

        class TestDocument(BaseModel, DocumentValidatorMixin):
            data: Dict[str, Any] | list | None = None
            errors: list | None = None
            meta: Dict[str, Any] | None = None

        # Valid with errors
        doc = TestDocument(errors=[{"title": "Error"}])
        assert doc.errors is not None
        assert doc.data is None

    def test_document_with_meta_only(self):
        """Test document validation with meta only."""

        class TestDocument(BaseModel, DocumentValidatorMixin):
            data: Dict[str, Any] | list | None = None
            errors: list | None = None
            meta: Dict[str, Any] | None = None

        # Valid with meta
        doc = TestDocument(meta={"total": 100})
        assert doc.meta is not None
        assert doc.data is None
        assert doc.errors is None

    def test_document_with_data_and_errors(self):
        """Test document validation fails with both data and errors."""

        class TestDocument(BaseModel, DocumentValidatorMixin):
            data: Dict[str, Any] | list | None = None
            errors: list | None = None
            meta: Dict[str, Any] | None = None

        with pytest.raises(
            ValidationError,
            match="A document MUST NOT contain both 'data' and 'errors'",
        ):
            TestDocument(data={"type": "users", "id": "1"}, errors=[{"title": "Error"}])

    def test_document_without_data_errors_or_meta(self):
        """Test document validation fails without data, errors, or meta."""

        class TestDocument(BaseModel, DocumentValidatorMixin):
            data: Dict[str, Any] | list | None = None
            errors: list | None = None
            meta: Dict[str, Any] | None = None

        with pytest.raises(
            ValidationError,
            match="A document MUST contain at least one of 'data', 'errors', or 'meta'",
        ):
            TestDocument()

    def test_document_with_data_and_meta(self):
        """Test document validation with data and meta."""

        class TestDocument(BaseModel, DocumentValidatorMixin):
            data: Dict[str, Any] | list | None = None
            errors: list | None = None
            meta: Dict[str, Any] | None = None

        # Valid with data and meta
        doc = TestDocument(data={"type": "users", "id": "1"}, meta={"total": 1})
        assert doc.data is not None
        assert doc.meta is not None
        assert doc.errors is None

    def test_document_with_errors_and_meta(self):
        """Test document validation with errors and meta."""

        class TestDocument(BaseModel, DocumentValidatorMixin):
            data: Dict[str, Any] | list | None = None
            errors: list | None = None
            meta: Dict[str, Any] | None = None

        # Valid with errors and meta
        doc = TestDocument(errors=[{"title": "Error"}], meta={"request_id": "123"})
        assert doc.errors is not None
        assert doc.meta is not None
        assert doc.data is None

    def test_document_with_empty_collections(self):
        """Test document validation with empty collections."""

        class TestDocument(BaseModel, DocumentValidatorMixin):
            data: dict | list | None = None
            errors: list | None = None
            meta: dict | None = None

        # Empty list for data should be valid
        doc = TestDocument(data=[])
        assert doc.data == []

        # Empty list for errors should be valid
        doc = TestDocument(errors=[])
        assert doc.errors == []

        # Empty dict for meta should be valid
        doc = TestDocument(meta={})
        assert doc.meta == {}


class TestMixinIntegration:
    """Integration tests for validator mixins."""

    def test_multiple_mixins_on_single_class(self):
        """Test using multiple validator mixins on a single class."""

        class ComplexModel(
            BaseModel, ResourceValidatorMixin, ResourceIdentifierValidatorMixin
        ):
            type: str
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        # Should validate with all mixin rules
        model = ComplexModel(type="users", id="123", attributes={"name": "John"})
        assert model.type == "users"
        assert model.id == "123"

    def test_mixin_inheritance_order(self):
        """Test that mixin inheritance order doesn't cause issues."""

        class ModelA(ResourceIdentifierValidatorMixin, BaseModel):
            type: str
            id: str = None
            lid: str = None

        class ModelB(BaseModel, ResourceIdentifierValidatorMixin):
            type: str
            id: str = None
            lid: str = None

        # Both should work regardless of order
        a = ModelA(type="users", id="1")
        b = ModelB(type="users", id="1")

        assert a.id == "1"
        assert b.id == "1"

    def test_validator_mixin_error_messages(self):
        """Test that validator mixins provide clear error messages."""

        class TestModel(BaseModel, ResourceValidatorMixin):
            type: str = None
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None

        # Test different validation errors
        with pytest.raises(ValidationError) as exc_info:
            TestModel(id="123", attributes={"name": "John"})

        error_messages = str(exc_info.value)
        assert "type" in error_messages or "required" in error_messages

    def test_custom_validation_with_mixins(self):
        """Test that custom validation can coexist with mixins."""

        class CustomModel(BaseModel, ResourceValidatorMixin):
            type: str
            id: str = None
            lid: str = None
            attributes: dict = None
            relationships: dict = None
            custom_field: str = None

            @field_validator("custom_field")
            @classmethod
            def validate_custom_field(cls, v):
                if v and len(v) < 3:
                    raise ValueError("Custom field must be at least 3 characters")
                return v

        # Should validate both mixin and custom rules
        model = CustomModel(
            type="users", id="123", attributes={"name": "John"}, custom_field="valid"
        )
        assert model.custom_field == "valid"

        # Should fail custom validation
        with pytest.raises(ValidationError):
            CustomModel(
                type="users",
                id="123",
                attributes={"name": "John"},
                custom_field="ab",  # Too short
            )
