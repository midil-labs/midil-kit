from typing import Any, Dict, List, Optional, TypeVar, Union, TypeAlias, Generic
from pydantic import BaseModel, Field, ConfigDict
from pydantic_core import Url

from midil.jsonapi._mixins.serializers import (
    DocumentSerializerMixin,
    ErrorSerializerMixin,
    ResourceSerializerMixin,
)
from midil.jsonapi._mixins.validators import (
    DocumentValidatorMixin,
    ErrorSourceValidatorMixin,
    JSONAPIErrorValidatorMixin,
    ResourceIdentifierValidatorMixin,
    ResourceValidatorMixin,
)

# Type Aliases
MetaObject: TypeAlias = Optional[Dict[str, Any]]
LinkValue: TypeAlias = Union[str, "LinkObject"]
RelationshipData: TypeAlias = Union[
    "ResourceIdentifier", List["ResourceIdentifier"], None
]
ErrorList: TypeAlias = List["JSONAPIError"]

#
JSONAPI_CONTENT_TYPE = "application/vnd.api+json"
JSONAPI_ACCEPT = "application/vnd.api+json"
JSONAPI_VERSION = "1.1"


class JSONAPIInfo(BaseModel):
    version: str = Field(default=JSONAPI_VERSION)
    ext: Optional[List[str]] = None
    profile: Optional[List[str]] = None
    meta: MetaObject = None


class ErrorSource(BaseModel, ErrorSourceValidatorMixin):
    pointer: Optional[str] = None
    parameter: Optional[str] = None
    header: Optional[str] = None


class JSONAPIError(BaseModel, ErrorSerializerMixin, JSONAPIErrorValidatorMixin):
    id: Optional[str] = None
    links: Optional[Dict[str, LinkValue]] = None
    status: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None
    detail: Optional[str] = None
    source: Optional[ErrorSource] = None
    meta: MetaObject = None


class LinkObject(BaseModel):
    href: Url
    rel: Optional[str] = None
    describedby: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None
    hreflang: Optional[Union[str, List[str]]] = None
    meta: MetaObject = None


class Links(BaseModel):
    self: LinkValue
    related: Optional[LinkValue] = None
    first: Optional[LinkValue] = None
    last: Optional[LinkValue] = None
    prev: Optional[LinkValue] = None
    next: Optional[LinkValue] = None

    model_config = ConfigDict(extra="forbid")


class BaseResourceIdentifier(BaseModel):
    type: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$")
    meta: Optional[Dict[str, Any]] = None


class ExistingResourceIdentifier(BaseResourceIdentifier):
    id: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")
    lid: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")


class ResourceIdentifier(ExistingResourceIdentifier, ResourceIdentifierValidatorMixin):
    pass


class Relationship(BaseModel):
    data: RelationshipData
    links: Optional[Links] = None
    meta: MetaObject = None


AttributesT = TypeVar("AttributesT", bound=BaseModel)


class Resource(
    ResourceIdentifier,
    ResourceSerializerMixin,
    ResourceValidatorMixin,
    Generic[AttributesT],
):
    attributes: Optional[AttributesT] = None
    relationships: Optional[Dict[str, Relationship]] = None
    links: Optional[Links] = None
    meta: MetaObject = None

    model_config = ConfigDict(extra="forbid")


ResourceT = TypeVar(
    "ResourceT", bound=Union[Resource[BaseModel], List[Resource[BaseModel]]]
)


class JSONAPIDocument(
    BaseModel,
    DocumentSerializerMixin,
    DocumentValidatorMixin,
    Generic[AttributesT],
):
    data: Optional[Union[Resource[AttributesT], List[Resource[AttributesT]]]] = None
    errors: Optional[ErrorList] = None
    meta: MetaObject = None
    jsonapi: Optional[JSONAPIInfo] = Field(default_factory=JSONAPIInfo)
    links: Optional[Links] = None
    included: Optional[List[Resource[BaseModel]]] = None


class JSONAPIHeader(BaseModel):
    version: str = Field(default=JSONAPI_VERSION, alias="jsonapi-version")
    accept: str = Field(default=JSONAPI_ACCEPT)
    content_type: str = Field(default=JSONAPI_CONTENT_TYPE, alias="content-type")


class JSONAPIRequestBody(BaseModel, Generic[AttributesT]):
    data: Union[Resource[AttributesT], List[Resource[AttributesT]]]
    meta: MetaObject = None

    model_config = ConfigDict(extra="forbid")
