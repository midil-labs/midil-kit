from __future__ import annotations  # noqa: F401

from typing import (
    Any,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    TypeAlias,
    Generic,
)
from pydantic import BaseModel, Field, AnyUrl

from midil.jsonapi._mixins.serializers import (
    DocumentSerializerMixin,
    ErrorSerializerMixin,
    ResourceSerializerMixin,
)
from midil.jsonapi._mixins.validators import (
    ErrorSourceValidatorMixin,
    JSONAPIErrorValidatorMixin,
)
from midil.jsonapi.config import (
    ForbidExtraFieldsModel,
    AllowExtraFieldsModel,
    IgnoreExtraFieldsModel,
)

# Type Aliases
MetaObject: TypeAlias = Optional[Dict[str, Any]]
LinkValue: TypeAlias = Union[AnyUrl, "LinkObject"]
RelationshipData: TypeAlias = Union[
    "ResourceIdentifier", List["ResourceIdentifier"], None
]
ErrorList: TypeAlias = List["JSONAPIError"]

AttributesT = TypeVar("AttributesT", bound=BaseModel)

#
JSONAPI_CONTENT_TYPE = "application/vnd.api+json"
JSONAPI_ACCEPT = "application/vnd.api+json"
JSONAPI_VERSION = "1.1"


# DRY helpers for common fields
class _MetaMixin(BaseModel):
    """Mixin for including a 'meta' member as per JSON:API specification."""

    meta: MetaObject = None


class _LinksMixin(BaseModel):
    """Mixin for including a 'links' member as per JSON:API specification."""

    links: Optional["Links"] = None


class _RelationshipsMixin(BaseModel):
    """Mixin for including a 'relationships' member as per JSON:API specification."""

    relationships: Optional[Dict[str, "Relationship"]] = None


class _LidMixin(BaseModel):
    """Mixin for including a 'lid' (local id) member as per JSON:API 1.1 specification."""

    lid: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")


class JSONAPIInfo(AllowExtraFieldsModel, _MetaMixin):
    """
    Represents the 'jsonapi' object describing the server's implementation.

    Fields:
        version: The version of the JSON:API specification implemented.
        ext: An array of URIs for supported extensions.
        profile: An array of URIs for supported profiles.
        meta: Non-standard meta-information.
    """

    version: str = Field(default=JSONAPI_VERSION)
    ext: Optional[List[str]] = None
    profile: Optional[List[str]] = None


class ErrorSource(ForbidExtraFieldsModel, ErrorSourceValidatorMixin):
    """
    Represents the 'source' object in a JSON:API error.

    Fields:
        pointer: A JSON Pointer to the associated entity in the request document.
        parameter: A string indicating which URI query parameter caused the error.
        header: A string indicating which header caused the error.
    """

    pointer: Optional[str] = None
    parameter: Optional[str] = None
    header: Optional[str] = None


class JSONAPIError(
    AllowExtraFieldsModel, ErrorSerializerMixin, JSONAPIErrorValidatorMixin, _MetaMixin
):
    """
    Represents an error object as per JSON:API specification.

    Fields:
        id: A unique identifier for this particular occurrence of the problem.
        links: Links relevant to the error.
        status: The HTTP status code applicable to this problem, as a string.
        code: An application-specific error code.
        title: A short, human-readable summary of the problem.
        detail: A human-readable explanation specific to this occurrence of the problem.
        source: An object containing references to the source of the error.
        meta: Non-standard meta-information.
    """

    status: str = Field(..., pattern=r"^[1-5][0-9]{2}$")
    title: str
    detail: str
    id: Optional[str] = None
    source: Optional[ErrorSource] = None
    code: Optional[str] = None
    links: Optional[Dict[str, LinkValue]] = None


class LinkObject(ForbidExtraFieldsModel, _MetaMixin):
    """
    Represents a link object as per JSON:API specification.

    Fields:
        href: The link's URL.
        rel: The link relation type.
        describedby: A link to further documentation.
        title: A human-readable title for the link.
        type: The media type of the link's target.
        hreflang: The language(s) of the linked resource.
        meta: Non-standard meta-information.
    """

    href: AnyUrl
    rel: Optional[str] = None
    describedby: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    hreflang: Optional[Union[str, List[str]]] = None


class Links(ForbidExtraFieldsModel):
    """
    Represents a set of links as per JSON:API specification.

    Fields:
        self: The link that generated the current response document.
        related: A related resource link.
        first: The first page of data.
        last: The last page of data.
        prev: The previous page of data.
        next: The next page of data.
    """

    self: LinkValue
    related: Optional[LinkValue] = None
    first: Optional[LinkValue] = None
    last: Optional[LinkValue] = None
    prev: Optional[LinkValue] = None
    next: Optional[LinkValue] = None


class Relationship(ForbidExtraFieldsModel, _LinksMixin, _MetaMixin):
    """
    Represents a relationship object as per JSON:API specification.

    Fields:
        data: Resource linkage (to-one or to-many).
        links: Links related to the relationship.
        meta: Non-standard meta-information.
    """

    data: RelationshipData


class ResourceType(ForbidExtraFieldsModel, _MetaMixin):
    """
    Represents the 'type' member of a resource object.

    Fields:
        type: The resource type.
        meta: Non-standard meta-information.
    """

    type: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")


class ResourceIdentifier(ResourceType):
    """
    Represents a resource identifier object as per JSON:API specification.

    Fields:
        type: The resource type.
        id: The resource identifier.
        meta: Non-standard meta-information.
    """

    id: str = Field(..., pattern=r"^[a-zA-Z0-9_-]+$")


class _ResourceBase(
    ResourceType,
    ResourceSerializerMixin,
    _LinksMixin,
    _MetaMixin,
    _RelationshipsMixin,
    Generic[AttributesT],
):
    """
    Base class for resource objects, parameterized by attributes.

    Fields:
        type: The resource type.
        attributes: The resource's attributes.
        links: Links related to the resource.
        meta: Non-standard meta-information.
        relationships: Relationships to other resources.
    """

    attributes: Optional[AttributesT] = None


class Resource(
    ResourceIdentifier,
    _ResourceBase[AttributesT],
    Generic[AttributesT],
):
    """
    Represents a full resource object as per JSON:API specification.

    Inherits:
        type, id, attributes, links, meta, relationships.
    """

    ...


class JSONAPIDocument(
    IgnoreExtraFieldsModel,
    DocumentSerializerMixin,
    Generic[AttributesT],
):
    """
    Represents a top-level JSON:API document.

    Fields:
        data: The primary data (resource object(s) or null).
        meta: Non-standard meta-information.
        jsonapi: Information about the JSON:API implementation.
        links: Links related to the primary data.
        included: Included related resource objects.
    """

    __parameters__ = (AttributesT,)  # type: ignore

    data: Optional[Union[Resource[AttributesT], List[Resource[AttributesT]]]] = None
    meta: Optional[MetaObject] = None
    jsonapi: Optional[JSONAPIInfo] = Field(default_factory=JSONAPIInfo)
    links: Optional[Links] = None
    included: Optional[List[Resource[BaseModel]]] = None


class JSONAPIErrorDocument(ForbidExtraFieldsModel):
    """
    Represents a top-level JSON:API error document.

    Fields:
        errors: A list of error objects.
        meta: Non-standard meta-information.
        jsonapi: Information about the JSON:API implementation.
        links: Links related to the error(s).
    """

    errors: List[JSONAPIError] = Field(..., min_length=1)
    meta: Optional[MetaObject] = None
    jsonapi: Optional[JSONAPIInfo] = Field(default_factory=JSONAPIInfo)
    links: Optional[Links] = None


class JSONAPIHeader(AllowExtraFieldsModel):
    """
    Represents HTTP headers for JSON:API requests and responses.

    Fields:
        version: The JSON:API version (as 'jsonapi-version' header).
        accept: The Accept header value.
        content_type: The Content-Type header value.
    """

    version: str = Field(default=JSONAPI_VERSION, alias="jsonapi-version")
    accept: str = Field(default=JSONAPI_ACCEPT)
    content_type: str = Field(default=JSONAPI_CONTENT_TYPE, alias="content-type")


class JSONAPIPostResource(
    _ResourceBase[AttributesT],
    ResourceSerializerMixin,
    _LidMixin,
):
    """
    Represents a resource object for POST requests (resource creation).

    Inherits:
        type, attributes, links, meta, relationships, lid.
    """

    pass


class JSONAPIPatchResource(
    Resource[AttributesT],
    ResourceIdentifier,
    _LidMixin,
):
    """
    Represents a resource object for PATCH requests (resource update).

    Inherits:
        type, id, attributes, links, meta, relationships, lid.
    """

    pass
