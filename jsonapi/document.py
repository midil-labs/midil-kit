from typing import Any, Dict, List, Optional, TypeVar, Union

from pydantic import BaseModel, ConfigDict, Field

from jsonapi._mixins.serializers import (
    DocumentSerializerMixin,
    ErrorSerializerMixin,
    ResourceSerializerMixin,
)
from jsonapi._mixins.validators import (
    DocumentValidatorMixin,
    ErrorSourceValidatorMixin,
    JSONAPIErrorValidatorMixin,
    LinkValidatorMixin,
    ResourceIdentifierValidatorMixin,
    ResourceValidatorMixin,
    QueryParamsValidatorMixin,
)

# Type aliases
ResourceType = TypeVar("ResourceType", bound="Resource")
RelationshipType = TypeVar("RelationshipType", bound="Relationship")
ResourceData = Union["Resource[Any]", List["Resource[Any]"], None]
ErrorList = List["JSONAPIError"]
LinkValue = Union[str, "LinkObject"]
RelationshipData = Union["ResourceIdentifier", List["ResourceIdentifier"], None]


# Constants
JSONAPI_CONTENT_TYPE: str = "application/vnd.api+json"
JSONAPI_ACCEPT: str = "application/vnd.api+json"


# Generic meta object
MetaObject = Optional[Dict[str, Any]]


# JSON:API Info and Error models
class JSONAPIInfo(BaseModel):
    version: str = Field(default="1.1", description="JSON:API specification version")
    ext: Optional[List[str]] = Field(
        default=None, alias="ext", description="Extension members"
    )
    profile: Optional[List[str]] = Field(
        default=None, alias="profile", description="Profile members"
    )
    meta: MetaObject = Field(
        default=None,
        alias="meta",
        description="Metadata about the JSON:API specification",
    )


class ErrorSource(BaseModel, ErrorSourceValidatorMixin):
    pointer: Optional[str] = Field(
        default=None, alias="pointer", description="The pointer to the error"
    )
    parameter: Optional[str] = Field(
        default=None, alias="parameter", description="The parameter of the error"
    )
    header: Optional[str] = Field(
        default=None, alias="header", description="The header of the error"
    )


class JSONAPIError(BaseModel, ErrorSerializerMixin, JSONAPIErrorValidatorMixin):
    id: Optional[str] = Field(
        default=None, alias="id", description="The unique identifier of the error"
    )
    links: Optional[Dict[str, Union[str, "LinkObject"]]] = Field(
        default=None, alias="links", description="Links related to the error"
    )
    status: Optional[str] = Field(
        default=None, alias="status", description="The HTTP status code of the error"
    )
    code: Optional[str] = Field(
        default=None, alias="code", description="The error code"
    )
    title: Optional[str] = Field(
        default=None, alias="title", description="The title of the error"
    )
    detail: Optional[str] = Field(
        default=None, alias="detail", description="The detail of the error"
    )
    source: Optional[ErrorSource] = Field(
        default=None, alias="source", description="The source of the error"
    )
    meta: MetaObject = Field(
        default=None, alias="meta", description="Metadata about the error"
    )


# Link models
class LinkObject(BaseModel, LinkValidatorMixin):
    href: str
    rel: Optional[str] = Field(
        default=None, alias="rel", description="The relationship of the link"
    )
    describedby: Optional[str] = Field(
        default=None, alias="describedby", description="The describedby of the link"
    )
    title: Optional[str] = Field(
        default=None, alias="title", description="The title of the link"
    )
    type: Optional[str] = Field(
        default=None, alias="type", description="The type of the link"
    )
    hreflang: Optional[Union[str, List[str]]] = Field(
        default=None, alias="hreflang", description="The hreflang of the link"
    )
    meta: MetaObject = Field(
        default=None, alias="meta", description="Metadata about the link"
    )


class Links(BaseModel):
    self: LinkValue = Field(..., alias="self", description="The self link")
    related: Optional[LinkValue] = Field(
        default=None, alias="related", description="The related link"
    )
    first: Optional[LinkValue] = Field(
        default=None, alias="first", description="The first link"
    )
    last: Optional[LinkValue] = Field(
        default=None, alias="last", description="The last link"
    )
    prev: Optional[LinkValue] = Field(
        default=None, alias="prev", description="The previous link"
    )
    next: Optional[LinkValue] = Field(
        default=None, alias="next", description="The next link"
    )

    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, use_enum_values=True
    )


# Resource models
class ResourceIdentifier(BaseModel, ResourceIdentifierValidatorMixin):
    type: str
    id: Optional[str] = Field(
        default=None, alias="id", description="The unique identifier of the resource"
    )
    lid: Optional[str] = Field(
        default=None, alias="lid", description="The local identifier of the resource"
    )
    meta: Optional[MetaObject] = Field(
        default=None, alias="meta", description="Metadata about the resource"
    )


class Relationship(BaseModel):
    data: RelationshipData = Field(
        ..., alias="data", description="The relationship data of the resource"
    )
    links: Optional[Links] = Field(
        default=None, alias="links", description="Links related to the relationship"
    )
    meta: MetaObject = Field(
        default=None, alias="meta", description="Metadata about the relationship"
    )


class Resource[AttributesType: BaseModel](
    ResourceIdentifier, ResourceSerializerMixin, ResourceValidatorMixin
):
    attributes: Optional[AttributesType] = Field(
        default=None, alias="attributes", description="The attributes of the resource"
    )
    relationships: Optional[Dict[str, Relationship]] = Field(
        default=None,
        alias="relationships",
        description="The relationships of the resource",
    )
    links: Optional[Links] = Field(
        default=None, alias="links", description="Links related to the resource"
    )
    meta: MetaObject = Field(
        default=None, alias="meta", description="Metadata about the resource"
    )

    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, use_enum_values=True
    )


# Document models
class JSONAPIDocument[T: BaseModel](
    BaseModel, DocumentSerializerMixin, DocumentValidatorMixin
):
    data: Optional[Union[Resource[T], List[Resource[T]]]] = Field(
        default=None, alias="data", description="The primary data of the document"
    )
    errors: Optional[ErrorList] = Field(
        default=None, alias="errors", description="An array of error objects"
    )
    meta: MetaObject = Field(
        default=None,
        alias="meta",
        description="Metadata about the resource that the document describes",
    )
    jsonapi: Optional[JSONAPIInfo] = Field(
        default_factory=lambda: JSONAPIInfo(),
        alias="jsonapi",
        description="Information about the JSON:API specification",
    )
    links: Optional[Links] = Field(
        default=None, alias="links", description="Links related to the primary data"
    )
    included: Optional[List[Resource[BaseModel]]] = Field(
        default=None,
        alias="included",
        description="An array of resource objects that are related to the primary data and/or each other",
    )


class JSONAPIHeader(BaseModel):
    version: str = Field(
        default="1.1",
        alias="jsonapi-version",
        description="The version of the JSON:API specification",
    )
    accept: str = Field(
        default=JSONAPI_ACCEPT,
        alias="accept",
        description="The media type of the body of the resource",
    )
    content_type: str = Field(
        default=JSONAPI_CONTENT_TYPE,
        alias="content-type",
        description="The media type of the body of the resource",
    )


class JSONAPIRequestBody[T: BaseModel](BaseModel):
    data: Union[Resource[T], List[Resource[T]]]
    meta: Optional[MetaObject] = Field(
        default=None,
        alias="meta",
        description="Metadata about the resource that the document describes",
    )
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class JSONAPIQueryParams(BaseModel, QueryParamsValidatorMixin):
    include: Optional[List[str]] = Field(
        default=None, description="List of related resources to include"
    )
    sort: Optional[List[str]] = Field(
        default=None,
        description="List of fields to sort by. Use `-` for descending",
    )
    filter: Optional[Dict[str, str]] = Field(
        default=None, description="Filtering map in format filter[field]=value"
    )
    fields: Optional[Dict[str, str]] = Field(
        default=None, description="Sparse fieldsets: fields[type]=field1,field2"
    )
    page: Optional[Dict[str, int]] = Field(
        default=None, description="Pagination parameters like page[number], page[size]"
    )
