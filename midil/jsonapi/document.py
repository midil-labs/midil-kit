from typing import Any, Dict, List, Optional, TypeVar, Union, TypeAlias
from pydantic import BaseModel, Field, ConfigDict, AnyUrl

from midil.jsonapi._mixins.serializers import (
    DocumentSerializerMixin,
    ErrorSerializerMixin,
    ResourceSerializerMixin,
)
from midil.jsonapi._mixins.validators import (
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
    href: AnyUrl
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


class ExistingResourceIdentifier(
    BaseResourceIdentifier, ResourceIdentifierValidatorMixin
):
    id: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")
    lid: Optional[str] = Field(default=None, pattern=r"^[a-zA-Z0-9_-]+$")


class ResourceIdentifier(ExistingResourceIdentifier):
    pass


class Relationship(BaseModel):
    data: RelationshipData
    links: Optional[Links] = None
    meta: MetaObject = None


class Resource[AttributesT: BaseModel](
    ResourceIdentifier,
    ResourceSerializerMixin,
    ResourceValidatorMixin,
):
    attributes: Optional[AttributesT] = None
    relationships: Optional[Dict[str, Relationship]] = None
    links: Optional[Links] = None
    meta: MetaObject = None

    model_config = ConfigDict(extra="forbid")


ResourceT = TypeVar(
    "ResourceT", bound=Union[Resource[BaseModel], List[Resource[BaseModel]]]
)


class JSONAPIDocument[AttributesT: BaseModel](
    BaseModel,
    DocumentSerializerMixin,
):
    data: Optional[Union[Resource[AttributesT], List[Resource[AttributesT]]]] = None
    meta: Optional[MetaObject] = None
    jsonapi: Optional[JSONAPIInfo] = Field(default_factory=JSONAPIInfo)
    links: Optional[Links] = None
    included: Optional[List[Resource[BaseModel]]] = None


class JSONAPIErrorDocument(BaseModel):
    errors: List[JSONAPIError]
    meta: Optional[MetaObject] = None
    jsonapi: Optional[JSONAPIInfo] = Field(default_factory=JSONAPIInfo)
    links: Optional[Links] = None


class JSONAPIHeader(BaseModel):
    version: str = Field(default=JSONAPI_VERSION, alias="jsonapi-version")
    accept: str = Field(default=JSONAPI_ACCEPT)
    content_type: str = Field(default=JSONAPI_CONTENT_TYPE, alias="content-type")


class JSONAPIRequestBody[AttributesT: BaseModel](BaseModel):
    data: Union[Resource[AttributesT], List[Resource[AttributesT]]]
    meta: MetaObject = None

    model_config = ConfigDict(extra="forbid")
