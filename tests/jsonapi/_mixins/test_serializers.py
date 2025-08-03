import pytest
from typing import Optional, Dict, Any
from pydantic import BaseModel
from midil.jsonapi._mixins.serializers import (
    ResourceSerializerMixin,
    ErrorSerializerMixin,
    DocumentSerializerMixin,
)


class MockAttributes(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None


class MockLinks(BaseModel):
    self: str
    related: Optional[str] = None


class MockRelationship(BaseModel):
    data: Dict[str, str]


class MockResource(BaseModel, ResourceSerializerMixin):
    type: str
    id: Optional[str] = None
    lid: Optional[str] = None
    attributes: Optional[MockAttributes] = None
    relationships: Optional[Dict[str, MockRelationship]] = None
    links: Optional[MockLinks] = None
    meta: Optional[Dict[str, Any]] = None


class MockError(BaseModel, ErrorSerializerMixin):
    id: Optional[str] = None
    status: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    source: Optional[Dict[str, str]] = None
    meta: Optional[Dict[str, str]] = None
    links: Optional[Dict[str, str]] = None


class MockDocument(BaseModel, DocumentSerializerMixin):
    data: Optional[Any] = None
    errors: Optional[Any] = None
    meta: Optional[Dict[str, str]] = None
    jsonapi: Optional[Dict[str, str]] = None
    links: Optional[Dict[str, str]] = None
    included: Optional[list] = None


# --- TESTS ---


def test_resource_to_jsonapi_full():
    resource = MockResource(
        type="person",
        id="123",
        attributes=MockAttributes(name="Alice", age=30),
        relationships={
            "friends": MockRelationship(data={"type": "person", "id": "456"})
        },
        links=MockLinks(self="/person/123"),
        meta={"role": "admin"},
    )
    result = resource.to_jsonapi()
    assert result["type"] == "person"
    assert result["id"] == "123"
    assert result["attributes"] == {"name": "Alice", "age": 30}
    assert "relationships" in result
    assert "links" in result
    assert "meta" in result


def test_resource_to_jsonapi_sparse_fields():
    resource = MockResource(
        type="person",
        id="123",
        attributes=MockAttributes(name="Alice", age=30),
        relationships={
            "friends": MockRelationship(data={"type": "person", "id": "456"}),
            "family": MockRelationship(data={"type": "person", "id": "789"}),
        },
    )
    result = resource.to_jsonapi(fields=["name", "friends"])
    assert result["attributes"] == {"name": "Alice"}
    assert "friends" in result["relationships"]
    assert "family" not in result["relationships"]


def test_error_to_jsonapi():
    err = MockError(
        id="err-001",
        status="400",
        title="Bad Request",
        detail="Missing fields",
        source={"pointer": "/data/attributes/name"},
        meta={"info": "extra"},
    )
    result = err.to_jsonapi()
    assert result["id"] == "err-001"
    assert result["status"] == "400"
    assert result["title"] == "Bad Request"
    assert "meta" in result
    assert result["source"]["pointer"] == "/data/attributes/name"


def test_document_with_single_resource():
    resource = MockResource(
        type="person",
        id="123",
        attributes=MockAttributes(name="Alice"),
    )
    doc = MockDocument(data=resource)
    result = doc.to_jsonapi()
    assert "data" in result
    assert result["data"]["type"] == "person"
    assert result["data"]["id"] == "123"


def test_document_with_multiple_resources_and_included():
    included = [
        MockResource(type="city", id="1", attributes=MockAttributes(name="Accra"))
    ]
    doc = MockDocument(
        data=[
            MockResource(type="person", id="1", attributes=MockAttributes(name="John")),
            MockResource(type="person", id="2", attributes=MockAttributes(name="Jane")),
        ],
        included=included,
        meta={"version": "1.1"},
    )
    result = doc.to_jsonapi()
    assert len(result["data"]) == 2
    assert result["included"][0]["type"] == "city"
    assert result["meta"]["version"] == "1.1"


def test_document_with_errors():
    error = MockError(id="err-101", status="403", title="Forbidden")
    doc = MockDocument(errors=[error])
    result = doc.to_jsonapi()
    assert "errors" in result
    assert result["errors"][0]["id"] == "err-101"


def test_resource_missing_model_dump_in_attributes():
    class BadAttributes:
        name = "bad"

    with pytest.raises(ValueError):
        resource = MockResource(
            type="bad",
            id="bad-id",
            attributes=BadAttributes(),  # Not a Pydantic model
        )
        resource.to_jsonapi()
