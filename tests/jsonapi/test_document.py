"""
Tests for midil.jsonapi.document
"""
import pytest
from pydantic import BaseModel, ValidationError
from pydantic_core import Url

from midil.jsonapi.document import (
    JSONAPIInfo,
    ErrorSource,
    JSONAPIError,
    LinkObject,
    Links,
    BaseResourceIdentifier,
    ExistingResourceIdentifier,
    ResourceIdentifier,
    Relationship,
    Resource,
    JSONAPIDocument,
    JSONAPIHeader,
    JSONAPIRequestBody,
    JSONAPI_CONTENT_TYPE,
    JSONAPI_ACCEPT,
    JSONAPI_VERSION,
)


class TestConstants:
    """Tests for module constants."""

    def test_constants_values(self):
        """Test that constants have expected values."""
        assert JSONAPI_CONTENT_TYPE == "application/vnd.api+json"
        assert JSONAPI_ACCEPT == "application/vnd.api+json"
        assert JSONAPI_VERSION == "1.1"


class TestJSONAPIInfo:
    """Tests for JSONAPIInfo class."""

    def test_jsonapi_info_defaults(self):
        """Test JSONAPIInfo with default values."""
        info = JSONAPIInfo()

        assert info.version == "1.1"
        assert info.ext is None
        assert info.profile is None
        assert info.meta is None

    def test_jsonapi_info_custom_values(self):
        """Test JSONAPIInfo with custom values."""
        info = JSONAPIInfo(
            version="1.0",
            ext=["https://jsonapi.org/ext/atomic"],
            profile=["https://example.com/profiles/flexible-pagination"],
            meta={"implementation": "midil-kit"},
        )

        assert info.version == "1.0"
        assert info.ext == ["https://jsonapi.org/ext/atomic"]
        assert info.profile == ["https://example.com/profiles/flexible-pagination"]
        assert info.meta == {"implementation": "midil-kit"}


class TestErrorSource:
    """Tests for ErrorSource class."""

    def test_error_source_with_pointer(self):
        """Test ErrorSource with JSON pointer."""
        source = ErrorSource(pointer="/data/attributes/name")

        assert source.pointer == "/data/attributes/name"
        assert source.parameter is None
        assert source.header is None

    def test_error_source_with_parameter(self):
        """Test ErrorSource with query parameter."""
        source = ErrorSource(parameter="include")

        assert source.parameter == "include"
        assert source.pointer is None
        assert source.header is None

    def test_error_source_with_header(self):
        """Test ErrorSource with header field."""
        source = ErrorSource(header="Authorization")

        assert source.header == "Authorization"
        assert source.pointer is None
        assert source.parameter is None

    def test_error_source_validation(self):
        """Test ErrorSource validation through mixin."""
        # Valid pointer
        source = ErrorSource(pointer="/data/attributes/email")
        assert source.pointer == "/data/attributes/email"

        # Invalid pointer should raise validation error
        with pytest.raises(ValidationError):
            ErrorSource(pointer="invalid-pointer")


class TestJSONAPIError:
    """Tests for JSONAPIError class."""

    def test_jsonapi_error_minimal(self):
        """Test JSONAPIError with minimal required fields."""
        error = JSONAPIError(title="Validation Error")

        assert error.title == "Validation Error"
        assert error.detail is None
        assert error.status is None

    def test_jsonapi_error_full(self):
        """Test JSONAPIError with all fields."""
        source = ErrorSource(pointer="/data/attributes/email")
        error = JSONAPIError(
            id="error-123",
            status="422",
            code="VALIDATION_ERROR",
            title="Validation Failed",
            detail="Email field is required",
            source=source,
            meta={"timestamp": "2023-01-01T00:00:00Z"},
        )

        assert error.id == "error-123"
        assert error.status == "422"
        assert error.code == "VALIDATION_ERROR"
        assert error.title == "Validation Failed"
        assert error.detail == "Email field is required"
        assert error.source.pointer == "/data/attributes/email"
        assert error.meta["timestamp"] == "2023-01-01T00:00:00Z"

    def test_jsonapi_error_validation(self):
        """Test JSONAPIError validation requirements."""
        # Should fail without title or detail
        with pytest.raises(ValidationError):
            JSONAPIError(status="500", code="INTERNAL_ERROR")

    def test_jsonapi_error_serialization(self):
        """Test JSONAPIError serialization."""
        error = JSONAPIError(title="Not Found", detail="User with id 123 not found")

        serialized = error.to_jsonapi()
        assert serialized["title"] == "Not Found"
        assert serialized["detail"] == "User with id 123 not found"


class TestLinkObject:
    """Tests for LinkObject class."""

    def test_link_object_minimal(self):
        """Test LinkObject with minimal required fields."""
        link = LinkObject(href=Url("https://api.example.com/users"))

        assert str(link.href) == "https://api.example.com/users"
        assert link.rel is None
        assert link.title is None

    def test_link_object_full(self):
        """Test LinkObject with all fields."""
        link = LinkObject(
            href=Url("https://api.example.com/users"),
            rel="related",
            title="Users Collection",
            type="application/vnd.api+json",
            hreflang=["en", "es"],
            meta={"count": 100},
        )

        assert str(link.href) == "https://api.example.com/users"
        assert link.rel == "related"
        assert link.title == "Users Collection"
        assert link.type == "application/vnd.api+json"
        assert link.hreflang == ["en", "es"]
        assert link.meta["count"] == 100

    def test_link_object_single_hreflang(self):
        """Test LinkObject with single hreflang value."""
        link = LinkObject(href=Url("https://api.example.com/users"), hreflang="en")

        assert link.hreflang == "en"


class TestLinks:
    """Tests for Links class."""

    def test_links_minimal(self):
        """Test Links with minimal required fields."""
        links = Links(self="https://api.example.com/users")

        assert links.self == "https://api.example.com/users"
        assert links.related is None
        assert links.first is None

    def test_links_with_link_objects(self):
        """Test Links with LinkObject instances."""
        self_link = LinkObject(href=Url("https://api.example.com/users"))
        links = Links(self=self_link)

        assert isinstance(links.self, LinkObject)
        assert str(links.self.href) == "https://api.example.com/users"

    def test_links_pagination(self):
        """Test Links with pagination links."""
        links = Links(
            self="https://api.example.com/users?page=2",
            first="https://api.example.com/users?page=1",
            prev="https://api.example.com/users?page=1",
            next="https://api.example.com/users?page=3",
            last="https://api.example.com/users?page=10",
        )

        assert links.first == "https://api.example.com/users?page=1"
        assert links.prev == "https://api.example.com/users?page=1"
        assert links.next == "https://api.example.com/users?page=3"
        assert links.last == "https://api.example.com/users?page=10"

    def test_links_extra_fields_forbidden(self):
        """Test that Links forbids extra fields."""
        with pytest.raises(ValidationError):
            Links(
                self="https://api.example.com/users",
                custom_link="https://api.example.com/custom",  # type: ignore
            )


class TestResourceIdentifier:
    """Tests for ResourceIdentifier classes."""

    def test_base_resource_identifier(self):
        """Test BaseResourceIdentifier."""
        resource = BaseResourceIdentifier(type="users")

        assert resource.type == "users"
        assert resource.meta is None

    def test_base_resource_identifier_with_meta(self):
        """Test BaseResourceIdentifier with meta."""
        resource = BaseResourceIdentifier(
            type="users", meta={"created_at": "2023-01-01T00:00:00Z"}
        )

        assert resource.meta["created_at"] == "2023-01-01T00:00:00Z"

    def test_base_resource_identifier_type_validation(self):
        """Test type field validation pattern."""
        # Valid types
        valid_types = ["users", "user-profiles", "user_profiles", "API_KEYS"]
        for type_name in valid_types:
            resource = BaseResourceIdentifier(type=type_name)
            assert resource.type == type_name

        # Invalid types
        invalid_types = ["123users", "-users", "_users"]
        for type_name in invalid_types:
            with pytest.raises(ValidationError):
                BaseResourceIdentifier(type=type_name)

    def test_existing_resource_identifier(self):
        """Test ExistingResourceIdentifier."""
        resource = ExistingResourceIdentifier(type="users", id="123")

        assert resource.type == "users"
        assert resource.id == "123"
        assert resource.lid is None

    def test_existing_resource_identifier_with_lid(self):
        """Test ExistingResourceIdentifier with lid."""
        resource = ExistingResourceIdentifier(type="users", id="123", lid="local-456")

        assert resource.id == "123"
        assert resource.lid == "local-456"

    def test_existing_resource_identifier_id_validation(self):
        """Test id field validation pattern."""
        # Valid IDs
        valid_ids = ["123", "user-123", "user_123", "ABC123"]
        for id_value in valid_ids:
            resource = ExistingResourceIdentifier(type="users", id=id_value)
            assert resource.id == id_value

    def test_resource_identifier_validation(self):
        """Test ResourceIdentifier validation."""
        # Valid with id
        resource = ResourceIdentifier(type="users", id="123")
        assert resource.type == "users"
        assert resource.id == "123"

        # Valid with lid
        resource = ResourceIdentifier(type="users", lid="local-123")
        assert resource.lid == "local-123"

        # Should fail without id or lid
        with pytest.raises(ValidationError):
            ResourceIdentifier(type="users")


class TestRelationship:
    """Tests for Relationship class."""

    def test_relationship_single_resource(self):
        """Test Relationship with single resource identifier."""
        resource_id = ResourceIdentifier(type="profiles", id="456")
        relationship = Relationship(data=resource_id)

        assert relationship.data.type == "profiles"
        assert relationship.data.id == "456"

    def test_relationship_multiple_resources(self):
        """Test Relationship with multiple resource identifiers."""
        resource_ids = [
            ResourceIdentifier(type="posts", id="1"),
            ResourceIdentifier(type="posts", id="2"),
        ]
        relationship = Relationship(data=resource_ids)

        assert len(relationship.data) == 2
        assert relationship.data[0].type == "posts"
        assert relationship.data[1].id == "2"

    def test_relationship_null_data(self):
        """Test Relationship with null data."""
        relationship = Relationship(data=None)

        assert relationship.data is None

    def test_relationship_with_links_and_meta(self):
        """Test Relationship with links and meta."""
        links = Links(self="https://api.example.com/users/123/relationships/posts")
        relationship = Relationship(data=None, links=links, meta={"count": 5})

        assert (
            relationship.links.self
            == "https://api.example.com/users/123/relationships/posts"
        )
        assert relationship.meta["count"] == 5


class TestResource:
    """Tests for Resource class."""

    def test_resource_minimal(self):
        """Test Resource with minimal required fields."""
        resource = Resource(type="users", id="123")

        assert resource.type == "users"
        assert resource.id == "123"
        assert resource.attributes is None

    def test_resource_with_attributes(self):
        """Test Resource with attributes."""

        class UserAttributes(BaseModel):
            name: str
            email: str

        attributes = UserAttributes(name="John Doe", email="john@example.com")
        resource = Resource(type="users", id="123", attributes=attributes)

        assert resource.attributes.name == "John Doe"
        assert resource.attributes.email == "john@example.com"

    def test_resource_with_relationships(self):
        """Test Resource with relationships."""
        posts_relationship = Relationship(
            data=[ResourceIdentifier(type="posts", id="1")]
        )
        resource = Resource(
            type="users", id="123", relationships={"posts": posts_relationship}
        )

        assert "posts" in resource.relationships
        assert resource.relationships["posts"].data[0].type == "posts"

    def test_resource_validation(self):
        """Test Resource validation through mixins."""
        # Should fail without id or lid
        with pytest.raises(ValidationError):
            Resource(type="users")

    def test_resource_extra_fields_forbidden(self):
        """Test that Resource forbids extra fields."""
        with pytest.raises(ValidationError):
            Resource(type="users", id="123", custom_field="not allowed")

    def test_resource_serialization(self):
        """Test Resource serialization."""

        class UserAttributes(BaseModel):
            name: str

        resource = Resource(
            type="users", id="123", attributes=UserAttributes(name="John Doe")
        )

        serialized = resource.to_jsonapi()
        assert serialized["type"] == "users"
        assert serialized["id"] == "123"
        assert serialized["attributes"]["name"] == "John Doe"


class TestJSONAPIDocument:
    """Tests for JSONAPIDocument class."""

    def test_document_with_single_resource(self):
        """Test JSONAPIDocument with single resource."""

        class UserAttributes(BaseModel):
            name: str

        resource = Resource(
            type="users", id="123", attributes=UserAttributes(name="John Doe")
        )
        document = JSONAPIDocument(data=resource)

        assert document.data.type == "users"
        assert document.data.id == "123"

    def test_document_with_resource_list(self):
        """Test JSONAPIDocument with list of resources."""
        resources = [Resource(type="users", id="1"), Resource(type="users", id="2")]
        document = JSONAPIDocument(data=resources)

        assert len(document.data) == 2
        assert document.data[0].id == "1"
        assert document.data[1].id == "2"

    def test_document_with_errors(self):
        """Test JSONAPIDocument with errors."""
        errors = [
            JSONAPIError(title="Validation Error"),
            JSONAPIError(title="Not Found"),
        ]
        document = JSONAPIDocument(errors=errors)

        assert len(document.errors) == 2
        assert document.errors[0].title == "Validation Error"
        assert document.data is None

    def test_document_validation(self):
        """Test JSONAPIDocument validation rules."""
        # Should fail with both data and errors
        with pytest.raises(ValidationError):
            JSONAPIDocument(
                data=Resource(type="users", id="1"),
                errors=[JSONAPIError(title="Error")],
            )

        # Should fail with none of data, errors, or meta
        with pytest.raises(ValidationError):
            JSONAPIDocument()

    def test_document_with_meta_only(self):
        """Test JSONAPIDocument with meta only."""
        document = JSONAPIDocument(meta={"total": 100})

        assert document.meta["total"] == 100
        assert document.data is None
        assert document.errors is None

    def test_document_with_all_components(self):
        """Test JSONAPIDocument with all optional components."""
        resource = Resource(type="users", id="123")
        included = [Resource(type="profiles", id="456")]
        links = Links(self="https://api.example.com/users")
        jsonapi = JSONAPIInfo(version="1.1")

        document = JSONAPIDocument(
            data=resource,
            meta={"total": 1},
            jsonapi=jsonapi,
            links=links,
            included=included,
        )

        assert document.data.id == "123"
        assert document.meta["total"] == 1
        assert document.jsonapi.version == "1.1"
        assert document.links.self == "https://api.example.com/users"
        assert len(document.included) == 1

    def test_document_default_jsonapi_info(self):
        """Test that JSONAPIDocument has default JSON:API info."""
        document = JSONAPIDocument(meta={})

        assert document.jsonapi is not None
        assert document.jsonapi.version == "1.1"

    def test_document_serialization(self):
        """Test JSONAPIDocument serialization."""
        resource = Resource(type="users", id="123")
        document = JSONAPIDocument(data=resource)

        serialized = document.to_jsonapi()
        assert serialized["data"]["type"] == "users"
        assert serialized["data"]["id"] == "123"
        assert serialized["jsonapi"]["version"] == "1.1"


class TestJSONAPIHeader:
    """Tests for JSONAPIHeader class."""

    def test_jsonapi_header_defaults(self):
        """Test JSONAPIHeader with default values."""
        header = JSONAPIHeader()

        assert header.version == "1.1"
        assert header.accept == "application/vnd.api+json"
        assert header.content_type == "application/vnd.api+json"

    def test_jsonapi_header_aliases(self):
        """Test JSONAPIHeader field aliases."""
        header = JSONAPIHeader(
            **{"jsonapi-version": "1.0", "content-type": "application/json"}
        )

        assert header.version == "1.0"
        assert header.content_type == "application/json"

    def test_jsonapi_header_model_dump_with_aliases(self):
        """Test JSONAPIHeader serialization with aliases."""
        header = JSONAPIHeader()
        dumped = header.model_dump(by_alias=True)

        assert "jsonapi-version" in dumped
        assert "content-type" in dumped
        assert dumped["jsonapi-version"] == "1.1"


class TestJSONAPIRequestBody:
    """Tests for JSONAPIRequestBody class."""

    def test_request_body_single_resource(self):
        """Test JSONAPIRequestBody with single resource."""

        class UserAttributes(BaseModel):
            name: str

        resource = Resource(
            type="users", id="123", attributes=UserAttributes(name="John Doe")
        )
        body = JSONAPIRequestBody(data=resource)

        assert body.data.type == "users"
        assert body.data.id == "123"

    def test_request_body_resource_list(self):
        """Test JSONAPIRequestBody with resource list."""
        resources = [Resource(type="users", id="1"), Resource(type="users", id="2")]
        body = JSONAPIRequestBody(data=resources)

        assert len(body.data) == 2
        assert body.data[0].id == "1"

    def test_request_body_with_meta(self):
        """Test JSONAPIRequestBody with meta."""
        resource = Resource(type="users", id="123")
        body = JSONAPIRequestBody(data=resource, meta={"client_version": "1.0"})

        assert body.meta["client_version"] == "1.0"

    def test_request_body_extra_fields_forbidden(self):
        """Test that JSONAPIRequestBody forbids extra fields."""
        resource = Resource(type="users", id="123")

        with pytest.raises(ValidationError):
            JSONAPIRequestBody(data=resource, extra_field="not allowed")


class TestIntegration:
    """Integration tests for document components."""

    def test_complete_document_workflow(self) -> None:
        """Test complete document creation and serialization workflow."""

        # Create attributes
        class UserAttributes(BaseModel):
            name: str
            email: str

        # Create relationships
        profile_ref = ResourceIdentifier(type="profiles", id="456")
        posts_refs = [
            ResourceIdentifier(type="posts", id="1"),
            ResourceIdentifier(type="posts", id="2"),
        ]

        # Create resource
        resource: Resource[UserAttributes] = Resource(
            type="users",
            id="123",
            attributes=UserAttributes(name="John Doe", email="john@example.com"),
            relationships={
                "profile": Relationship(data=profile_ref),
                "posts": Relationship(data=posts_refs),
            },
        )

        # Create included resources
        class ProfileAttributes(BaseModel):
            bio: str

        included_profile: Resource[ProfileAttributes] = Resource(
            type="profiles",
            id="456",
            attributes=ProfileAttributes(bio="Software developer"),
        )

        # Create document
        document: JSONAPIDocument[UserAttributes] = JSONAPIDocument(
            data=resource,
            included=[included_profile],  # type: ignore
            meta={"request_id": "req-123"},
            links=Links(self="https://api.example.com/users/123"),
        )
        # Serialize and verify
        serialized = document.to_jsonapi()

        assert serialized["data"]["type"] == "users"
        assert serialized["data"]["attributes"]["name"] == "John Doe"
        assert len(serialized["data"]["relationships"]["posts"]["data"]) == 2
        assert len(serialized["included"]) == 1
        assert serialized["meta"]["request_id"] == "req-123"
        assert serialized["links"]["self"] == "https://api.example.com/users/123"

    def test_error_document_workflow(self):
        """Test error document creation and serialization."""
        # Create errors
        errors = [
            JSONAPIError(
                id="err-1",
                status="422",
                code="VALIDATION_ERROR",
                title="Validation Failed",
                detail="Name field is required",
                source=ErrorSource(pointer="/data/attributes/name"),
            ),
            JSONAPIError(
                id="err-2",
                status="422",
                code="VALIDATION_ERROR",
                title="Validation Failed",
                detail="Email format is invalid",
                source=ErrorSource(pointer="/data/attributes/email"),
            ),
        ]

        class UserAttributes(BaseModel):
            name: str
            email: str

        # Create error document
        document: BaseModel = JSONAPIDocument(
            errors=errors, meta={"request_id": "req-456"}
        )

        # Serialize and verify
        serialized = document.model_dump()

        assert len(serialized["errors"]) == 2
        assert serialized["errors"][0]["code"] == "VALIDATION_ERROR"
        assert serialized["errors"][1]["source"]["pointer"] == "/data/attributes/email"
        assert serialized["meta"]["request_id"] == "req-456"
        assert "data" not in serialized

    def test_type_safety_with_generics(self):
        """Test type safety with generic Resource and Document types."""

        class UserAttributes(BaseModel):
            name: str
            email: str

        # Resource should work with specific attribute types
        resource: Resource[UserAttributes] = Resource(
            type="users",
            id="123",
            attributes=UserAttributes(name="John", email="john@example.com"),
        )

        # Document should work with specific resource types
        document: JSONAPIDocument[UserAttributes] = JSONAPIDocument(data=resource)

        assert document.data.attributes.name == "John"
        assert document.data.attributes.email == "john@example.com"
