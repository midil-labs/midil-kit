from pydantic import BaseModel, Field, field_validator, RootModel
from enum import StrEnum
from typing import List, Optional, Annotated


_DEFAULT_PAGE_SIZE = 10
_MAX_PAGE_SIZE = 100
_START_PAGE = 1


class PaginationParams(BaseModel):
    number: Annotated[int, Field(ge=1)] = _START_PAGE
    size: Annotated[int, Field(ge=1, le=100)] = _DEFAULT_PAGE_SIZE


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class SortField(RootModel[str]):
    root: str

    @property
    def value(self) -> str:
        return self.root.lstrip("-")

    @property
    def direction(self) -> SortDirection:
        return SortDirection.DESC if self.root.startswith("-") else SortDirection.ASC


class IncludeField(RootModel[List[str]]):
    root: List[str]

    @property
    def values(self) -> List[str]:
        return self.root


class SortQueryParams(BaseModel):  ## fastapi compatible
    sort: List[SortField]

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
        # Use getattr with default to avoid recursion
        sort_map = (
            object.__getattribute__(self, "_sort_map")
            if hasattr(self, "_sort_map")
            else {}
        )
        return sort_map.get(item)
