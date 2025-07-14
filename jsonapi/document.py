from typing import Any, Dict, List, Optional, TypeVar, Union, TypeAlias, Generic
from enum import StrEnum
from dataclasses import dataclass
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
)
import re
from pydantic import model_validator


MetaObject: TypeAlias = Optional[Dict[str, Any]]
LinkValue: TypeAlias = Union[str, "LinkObject"]
RelationshipData: TypeAlias = Union[
    "ResourceIdentifier", List["ResourceIdentifier"], None
]
ErrorList: TypeAlias = List["JSONAPIError"]

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


class LinkObject(BaseModel, LinkValidatorMixin):
    href: str
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


class ResourceIdentifier(BaseModel, ResourceIdentifierValidatorMixin):
    type: str
    id: Optional[str] = None
    lid: Optional[str] = None
    meta: MetaObject = None


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


ResourceT: TypeAlias = Union[Resource[AttributesT], List[Resource[AttributesT]]]


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


class JSONAPIRequestBody(Generic[AttributesT]):
    data: Union[Resource[AttributesT], List[Resource[AttributesT]]]
    meta: MetaObject = None

    model_config = ConfigDict(extra="forbid")


class FilterOperator(StrEnum):
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    IN = "in"
    NOT_IN = "not_in"

    @property
    def symbol(self) -> Optional[str]:
        """Returns symbolic representation of the operator (e.g., '=', '>=', 'IN')."""
        return {
            FilterOperator.EQ: "=",
            FilterOperator.NE: "!=",
            FilterOperator.LT: "<",
            FilterOperator.LE: "<=",
            FilterOperator.GT: ">",
            FilterOperator.GE: ">=",
            FilterOperator.IN: "IN",
            FilterOperator.NOT_IN: "NOT IN",
        }.get(self)


@dataclass
class FilterCondition:
    field: str
    operator: FilterOperator
    value: Union[str, List[str]]

    def __post_init__(self):
        if self.operator in [
            FilterOperator.IN,
            FilterOperator.NOT_IN,
        ] and not isinstance(self.value, list):
            self.value = [self.value] if self.value else []


_DEFAULT_PAGE_SIZE = 100
_DEFAULT_PAGE_NUMBER = 1


def _sanitize_query_param(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\[\]\.-]", "", value.strip())


class JSONAPIQueryParams(BaseModel):
    include: Optional[List[str]] = None
    sort: Optional[Dict[str, str]] = None  # field -> "asc"/"desc"
    filters: Optional[Dict[str, Dict[str, FilterCondition]]] = None
    fields: Optional[Dict[str, List[str]]] = None
    pagination: Optional[Dict[str, Union[int, str]]] = None
    extra_params: Optional[Dict[str, Union[str, int]]] = None

    @model_validator(mode="before")
    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {
            "include": [],
            "sort": {},
            "filters": {},
            "fields": {},
            "pagination": {},
            "extra_params": {},
        }

        for key, value in raw.items():
            key = _sanitize_query_param(key)

            if key == "include":
                parsed["include"] = cls._parse_list(value)
            elif key == "sort":
                parsed["sort"] = cls._parse_sort(value)
            elif key.startswith("fields["):
                resource_type = key[7:-1]
                parsed["fields"][resource_type] = cls._parse_list(value)
            elif key.startswith("filter["):
                field, operator = cls._extract_filter_parts(key)
                operator = operator or "eq"
                filter_obj = FilterCondition(
                    field=field,
                    operator=FilterOperator(operator),
                    value=cls._parse_filter_value(operator, value),
                )
                parsed["filters"].setdefault(field, {})[operator] = filter_obj
            elif key.startswith("page["):
                param = key[5:-1]
                parsed["pagination"][param] = cls._parse_page_param(param, value)
            else:
                parsed["extra_params"][key] = value

        return parsed

    @staticmethod
    def _parse_list(value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value or []

    @staticmethod
    def _parse_sort(value: Union[str, List[str]]) -> Dict[str, str]:
        result = {}
        if isinstance(value, str):
            items = [v.strip() for v in value.split(",")]
        else:
            items = value or []

        for item in items:
            direction = "desc" if item.startswith("-") else "asc"
            field = item[1:] if item.startswith("-") else item
            result[field] = direction
        return result

    @staticmethod
    def _extract_filter_parts(key: str) -> tuple[str, Optional[str]]:
        import re

        m = re.match(r"filter\[([^\]]+)\](?:\[([^\]]+)\])?", key)
        if not m:
            raise ValueError(f"Invalid filter key: {key}")
        return m.group(1), m.group(2)

    @staticmethod
    def _parse_filter_value(
        operator: str, value: Union[str, List[str]]
    ) -> Union[str, List[str]]:
        if operator in [FilterOperator.IN, FilterOperator.NOT_IN]:
            return [v.strip() for v in str(value).split(",") if v.strip()]
        return str(value).strip()

    @staticmethod
    def _parse_page_param(param: str, value: str) -> Union[int, str]:
        if param in {"number", "size", "limit", "offset"}:
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Pagination parameter '{param}' must be an integer")
        return str(value)
