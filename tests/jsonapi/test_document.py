import pytest
from pydantic import ValidationError
from midil.jsonapi.document import (
    ErrorObject,
    ErrorSource,
    ErrorDocument,
    JSONAPIDocument,
    ResourceObject,
    Links,
)
from pydantic import BaseModel


class UserAttributes(BaseModel):
    name: str
    email: str


def test_error_source_valid():
    src = ErrorSource(
        pointer="/data/attributes/name", parameter="name", header="X-Custom"
    )
    assert src.pointer == "/data/attributes/name"
    assert src.parameter == "name"
    assert src.header == "X-Custom"


def test_error_source_invalid_pointer():
    with pytest.raises(ValidationError):
        ErrorSource(pointer="invalid/pointer")


def test_error_object_full():
    err = ErrorObject(
        id="err1",
        status="400",
        code="invalid_request",
        title="Invalid request",
        detail="Missing required field.",
        source=ErrorSource(pointer="/data/attributes/name"),
    )
    err_dict = err.model_dump()
    assert err_dict["status"] == "400"
    assert err_dict["source"]["pointer"] == "/data/attributes/name"


def test_error_document():
    err = ErrorObject(
        id="err1",
        status="422",
        title="Unprocessable Entity",
    )
    doc = ErrorDocument(errors=[err])
    assert len(doc.errors) == 1
    assert getattr(doc.jsonapi, "version") == "1.1"
    assert doc.errors[0].status == "422"


def test_resource_object_serialization():
    user = ResourceObject[UserAttributes](
        id="1",
        type="users",
        attributes=UserAttributes(name="Jane", email="jane@example.com"),
    )
    user_dict = user.model_dump()
    assert user_dict["type"] == "users"
    assert user_dict["attributes"]["name"] == "Jane"


def test_jsonapi_document_with_single_resource():
    user = ResourceObject[UserAttributes](
        id="1",
        type="users",
        attributes=UserAttributes(name="Jane", email="jane@example.com"),
    )
    doc = JSONAPIDocument[UserAttributes](data=user)
    assert getattr(doc.data, "id") == "1"
    assert getattr(getattr(doc.data, "attributes"), "name") == "Jane"


def test_jsonapi_document_with_multiple_resources():
    users = [
        ResourceObject[UserAttributes](
            id="1",
            type="users",
            attributes=UserAttributes(name="Jane", email="jane@example.com"),
        ),
        ResourceObject[UserAttributes](
            id="2",
            type="users",
            attributes=UserAttributes(name="John", email="john@example.com"),
        ),
    ]
    doc = JSONAPIDocument[UserAttributes](data=users)
    assert isinstance(doc.data, list)
    assert getattr(getattr(doc.data[1], "attributes"), "name") == "John"


def test_links_object():
    links = Links(
        self="https://api.example.com/users/1", next="https://api.example.com/users/2"
    )
    assert links.self == "https://api.example.com/users/1"
    assert links.next == "https://api.example.com/users/2"


def test_included_object():
    class ArticleAttributes(BaseModel):
        title: str
        body: str

    user = ResourceObject[UserAttributes](
        type="users",
        id="1",
        attributes=UserAttributes(name="Jane", email="jane@example.com"),
    )
    article = ResourceObject[ArticleAttributes](
        type="articles",
        id="10",
        attributes=ArticleAttributes(title="Test Article", body="Content"),
    )
    from typing import cast

    doc = JSONAPIDocument[UserAttributes](
        data=user,
        included=[cast(ResourceObject[BaseModel], article)],
    )

    # Check that the included object is present and correct
    assert doc.included is not None
    assert len(doc.included) == 1
    included_obj = doc.included[0]
    assert included_obj.type == "articles"
    assert included_obj.id == "10"
    assert hasattr(included_obj.attributes, "title")
    assert getattr(included_obj.attributes, "title") == "Test Article"
    assert getattr(included_obj.attributes, "body") == "Content"
