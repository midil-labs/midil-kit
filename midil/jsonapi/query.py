from pydantic import BaseModel, Field, field_validator, RootModel
from enum import StrEnum
from typing import List, Dict, Optional, Annotated


_DEFAULT_PAGE_SIZE = 10
_MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    number: Annotated[int, Field(ge=1)] = 1
    size: Annotated[int, Field(ge=1, le=100)] = 10


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class SortField(RootModel[str]):
    __root__: str

    @property
    def value(self) -> str:
        return self.__root__.lstrip("-")

    @property
    def direction(self) -> SortDirection:
        return (
            SortDirection.DESC if self.__root__.startswith("-") else SortDirection.ASC
        )


class IncludeField(RootModel[List[str]]):
    __root__: List[str]

    @property
    def values(self) -> List[str]:
        return self.__root__


class SortQueryParams(BaseModel):  ## fastapi compatible
    sort: List[SortField]
    _sort_map: Dict[str, SortField] = {}

    @field_validator("sort", mode="before")
    @classmethod
    def split_sort_string(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    def __init__(self, **data):
        super().__init__(**data)
        self._sort_map = {sf.value: sf for sf in self.sort}

    def __getattr__(self, item: str) -> Optional[SortField]:
        return self._sort_map.get(item)
