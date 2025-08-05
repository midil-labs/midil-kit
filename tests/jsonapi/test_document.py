import pytest
from pydantic import ValidationError, BaseModel
from pydantic import AnyUrl

from midil.jsonapi.document import (
    JSONAPIInfo,
    ErrorSource,
    JSONAPIError,
    LinkObject,
    Links,
    Relationship,
    ResourceIdentifier,
    Resource,
    JSONAPIDocument,
    JSONAPIErrorDocument,
    JSONAPIPostResource,
    JSONAPIPatchResource,
    JSONAPIHeader,
)


class ArticleAttributes(BaseModel):
    title: str
    body: str


def test_jsonapi_info_defaults():
    info = JSONAPIInfo()
    assert info.version == "1.1"
    assert info.meta is None


def test_error_source_valid():
    src = ErrorSource(pointer="/data/attributes/title")
    assert src.pointer == "/data/attributes/title"


def test_jsonapi_error_minimal():
    err = JSONAPIError(status="404", title="Not Found", detail="Not Found")
    assert err.status == "404"
    assert err.title == "Not Found"
    assert err.meta is None


def test_jsonapi_error_invalid_status():
    with pytest.raises(ValidationError):
        JSONAPIError(
            status="9999", title="Invalid", detail="Invalid"
        )  # Not a valid HTTP status


def test_link_object_full():
    link = LinkObject(
        href="https://example.com/articles/1",
        rel="self",
        describedby="https://docs.com",
        title="An article",
        type="text/html",
        hreflang=["en", "fr"],
    )
    assert str(link.href) == "https://example.com/articles/1"
    assert isinstance(link.hreflang, list)


def test_links_object():
    links = Links(
        self=AnyUrl("https://example.com/articles"),
        next=AnyUrl("https://example.com/articles?page=2"),
    )
    assert str(links.self) == "https://example.com/articles"


def test_relationship_with_data():
    rel = Relationship(data=ResourceIdentifier(type="articles", id="123"))
    assert isinstance(rel.data, ResourceIdentifier)
    assert rel.data.id == "123"


def test_resource_identifier_pattern_valid():
    rid = ResourceIdentifier(type="articles", id="abc_123")
    assert rid.id == "abc_123"


def test_resource_object():
    res = Resource[ArticleAttributes](
        type="articles",
        id="a1",
        attributes=ArticleAttributes(title="Hi", body="Body text"),
    )
    assert getattr(res.attributes, "title", None) == "Hi"


def test_jsonapi_document_single_resource():
    doc = JSONAPIDocument[ArticleAttributes](
        data=Resource[ArticleAttributes](
            type="articles",
            id="a1",
            attributes=ArticleAttributes(title="Hi", body="Body text"),
        )
    )
    assert getattr(doc.data, "type", None) == "articles"
    assert getattr(doc.jsonapi, "version", None) == "1.1"


def test_jsonapi_document_multiple_resources():
    doc = JSONAPIDocument[ArticleAttributes](
        data=[
            Resource[ArticleAttributes](
                type="articles",
                id="a1",
                attributes=ArticleAttributes(title="Hi", body="Body text"),
            ),
            Resource[ArticleAttributes](
                type="articles",
                id="a2",
                attributes=ArticleAttributes(title="Second", body="More text"),
            ),
        ]
    )
    assert isinstance(doc.data, list)
    assert len(doc.data) == 2


def test_jsonapi_error_document():
    err_doc = JSONAPIErrorDocument(
        errors=[JSONAPIError(status="404", title="Not Found", detail="Not Found")]
    )
    assert err_doc.errors[0].status == "404"
    assert getattr(err_doc.jsonapi, "version", None) == "1.1"
    assert err_doc.errors[0].detail == "Not Found"


def test_jsonapi_post_resource_lid():
    post_res = JSONAPIPostResource[ArticleAttributes](
        type="articles",
        lid="temp123",
        attributes=ArticleAttributes(title="Hello", body="World"),
    )
    assert post_res.lid == "temp123"


def test_jsonapi_patch_resource():
    patch_res = JSONAPIPatchResource[ArticleAttributes](
        type="articles",
        id="123",
        lid="temp123",
        attributes=ArticleAttributes(title="Updated", body="New Body"),
    )
    assert patch_res.id == "123"
    assert patch_res.lid == "temp123"


def test_jsonapi_header_defaults():
    header = JSONAPIHeader()
    assert header.version == "1.1"
    assert header.content_type == "application/vnd.api+json"
    assert header.accept == "application/vnd.api+json"
