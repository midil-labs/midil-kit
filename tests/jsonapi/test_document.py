import pytest
from pydantic import ValidationError
from pydantic import AnyUrl

from midil.jsonapi.document import (
    JSONAPIInfo,
    ErrorSource,
    JSONAPIError,
    LinkObject,
    Links,
    ResourceIdentifier,
    Relationship,
    JSONAPIDocument,
    JSONAPIErrorDocument,
    JSONAPIHeader,
    JSONAPIRequestBody,
    Resource,
)

# Sample Pydantic model for attributes
from pydantic import BaseModel


class ArticleAttributes(BaseModel):
    title: str
    content: str


def test_jsonapi_info_defaults() -> None:
    info = JSONAPIInfo()
    assert info.version == "1.1"
    assert info.meta is None


def test_error_source_fields() -> None:
    src = ErrorSource(pointer="/data/attributes/title", parameter="title")
    assert src.pointer == "/data/attributes/title"
    assert src.parameter == "title"
    assert src.header is None


def test_jsonapi_error_creation() -> None:
    err = JSONAPIError(
        id="err1",
        status="400",
        code="INVALID_TITLE",
        title="Invalid Title",
        detail="Title must not be empty",
        source=ErrorSource(pointer="/data/attributes/title"),
    )
    assert err.id == "err1"
    assert err.status == "400"
    assert err.source.pointer == "/data/attributes/title"  # type: ignore


def test_link_object_with_url() -> None:
    link = LinkObject(href="https://api.example.com/posts/1", title="Post")  # type: ignore
    assert isinstance(link.href, AnyUrl)
    assert link.title == "Post"


def test_links_model_strict_keys() -> None:
    links = Links(self="https://api.example.com/posts")
    assert links.self == "https://api.example.com/posts"
    with pytest.raises(ValidationError):
        Links(self="https://api.example.com", unknown="x")  # type: ignore # extra field


def test_resource_identifier_valid() -> None:
    rid = ResourceIdentifier(type="article", id="a1", lid="l1")
    assert rid.type == "article"
    assert rid.id == "a1"


def test_resource_identifier_invalid_type() -> None:
    with pytest.raises(ValidationError):
        ResourceIdentifier(type="123Invalid", id="a1")


def test_relationship_with_data() -> None:
    rid = ResourceIdentifier(type="author", id="auth1")
    rel = Relationship(data=rid)
    assert rel.data == rid


def test_jsonapi_document_with_single_resource() -> None:
    res = Resource[ArticleAttributes](
        type="article",
        id="1",
        attributes=ArticleAttributes(title="Hello", content="World"),
    )
    doc = JSONAPIDocument[ArticleAttributes](data=res)
    assert doc.data.attributes.title == "Hello"  # type: ignore
    assert doc.jsonapi.version == "1.1"  # type: ignore


def test_jsonapi_document_with_list_of_resources() -> None:
    res1 = Resource[ArticleAttributes](
        type="article",
        id="1",
        attributes=ArticleAttributes(title="One", content="Content"),
    )
    res2 = Resource[ArticleAttributes](
        type="article",
        id="2",
        attributes=ArticleAttributes(title="Two", content="Content"),
    )
    doc = JSONAPIDocument[ArticleAttributes](data=[res1, res2])
    assert isinstance(doc.data, list)
    assert doc.data[0].id == "1"


def test_jsonapi_error_document_structure() -> None:
    err = JSONAPIError(
        status="400",
        code="REQUIRED_FIELD",
        title="Missing field",
        detail="The field 'title' is required",
    )
    doc = JSONAPIErrorDocument(errors=[err])
    assert len(doc.errors) == 1
    assert doc.errors[0].title == "Missing field"


def test_jsonapi_header_defaults() -> None:
    header = JSONAPIHeader()
    assert header.version == "1.1"
    assert header.accept == "application/vnd.api+json"
    assert header.content_type == "application/vnd.api+json"


def test_jsonapi_request_body_single_resource() -> None:
    res = Resource[ArticleAttributes](
        type="article",
        id="abc123",
        attributes=ArticleAttributes(title="Post", content="Data"),
    )
    body = JSONAPIRequestBody[ArticleAttributes](data=res)
    assert body.data.attributes.title == "Post"  # type: ignore
    assert body.meta is None
