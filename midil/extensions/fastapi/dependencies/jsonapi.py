from typing import List, Optional
from fastapi import Query
from midil.jsonapi.query import Sort, SortField, Include


def parse_sort(sort: Optional[List[str]] = Query(None, alias="sort")) -> Optional[Sort]:
    if sort:
        return Sort(fields=[SortField.from_raw(s) for s in sort])
    return None


def parse_include(
    include: Optional[List[str]] = Query(None, alias="include")
) -> Optional[Include]:
    if include:
        return Include(relationships=include)
    return None
