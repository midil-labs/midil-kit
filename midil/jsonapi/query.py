from enum import StrEnum
from typing import List, Optional, Annotated
from typing_extensions import Doc

from pydantic import BaseModel, Field, field_validator

from dataclasses import dataclass


@dataclass(frozen=True)
class Constants:
    DEFAULT_PAGE_SIZE: Annotated[int, Doc("The number of items per page.")] = 20
    MAX_PAGE_SIZE: Annotated[int, Doc("The maximum number of items per page.")] = 100
    DEFAULT_PAGE_NUMBER: Annotated[int, Doc("The default page number.")] = 1
    MAX_INCLUDE_DEPTH: Annotated[
        int, Doc("The maximum depth of included relationships.")
    ] = 3


class PaginationParams(BaseModel):
    number: Annotated[
        int,
        Field(ge=1, alias="page[number]"),
        Doc(
            """
            The page number.
            """
        ),
    ] = Constants.DEFAULT_PAGE_NUMBER
    size: Annotated[
        int,
        Field(ge=1, le=Constants.MAX_PAGE_SIZE, alias="page[size]"),
        Doc(
            """
            The number of items per page.
            """
        ),
    ] = Constants.DEFAULT_PAGE_SIZE

    class Config:
        frozen = True
        populate_by_name = True  # Allows using aliases like page[number]


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


class SortField(BaseModel):
    field: Annotated[
        str,
        Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_.]*$"),
        Doc("The name of the field to sort by."),
    ]
    direction: Annotated[
        SortDirection,
        Doc("The direction of the sort: 'asc' for ascending, 'desc' for descending."),
    ]

    @classmethod
    def from_raw(cls, raw: str) -> "SortField":
        return cls(
            field=raw.lstrip("-"),
            direction=SortDirection.DESC if raw.startswith("-") else SortDirection.ASC,
        )

    class Config:
        frozen = True


class Sort(BaseModel):
    fields: List[SortField]

    @classmethod
    def from_string(cls, string: str) -> "Sort":
        """Parse 'name,-created_at,author.name' format"""
        if not string:
            return cls(fields=[])

        fields = [
            SortField.from_raw(field.strip())
            for field in string.split(",")
            if field.strip()
        ]
        return cls(fields=fields)

    class Config:
        frozen = True


class Include(BaseModel):
    relationships: Annotated[
        List[str],
        Field(min_length=1),
        Doc("The relationships to include. Use dot notation for nested relationships."),
    ]

    @field_validator("relationships")
    @classmethod
    def validate_depth(cls, v):
        max_depth = Constants.MAX_INCLUDE_DEPTH
        for rel in v:
            if rel.count(".") + 1 > max_depth:
                raise ValueError(
                    f"Relationship '{rel}' exceeds maximum depth of {max_depth}"
                )
        return v

    class Config:
        frozen = True


class QueryParams(BaseModel):
    page: Optional[PaginationParams] = None
    sort: Optional[Sort] = None
    include: Optional[Include] = None

    class Config:
        frozen = True
