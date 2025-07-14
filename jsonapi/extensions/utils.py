from typing import Optional, Set, Dict, List
from jsonapi._mixins.validators import FilterOperator
from jsonapi.document import JSONAPIQueryParams
from jsonapi.document import JSONAPIError, ErrorSource


class JSONAPIQueryValidator:
    """Validator for JSON:API query parameters with configurable rules."""

    def __init__(
        self,
        allowed_fields: Optional[Set[str]] = None,
        allowed_relationships: Optional[Set[str]] = None,
        allowed_sort_fields: Optional[Set[str]] = None,
        allowed_filter_fields: Optional[Set[str]] = None,
        allowed_filter_operators: Optional[Dict[str, Set[FilterOperator]]] = None,
        max_page_size: Optional[int] = None,
        max_includes: Optional[int] = None,
    ):
        self.allowed_fields = allowed_fields or set()
        self.allowed_relationships = allowed_relationships or set()
        self.allowed_sort_fields = allowed_sort_fields or set()
        self.allowed_filter_fields = allowed_filter_fields or set()
        self.allowed_filter_operators = allowed_filter_operators or {}
        self.max_page_size = max_page_size
        self.max_includes = max_includes

    def validate(self, params: JSONAPIQueryParams) -> List[JSONAPIError]:
        errors: List[JSONAPIError] = []

        # Validate sparse fields
        if params.fields and self.allowed_fields:
            for resource_type in params.fields:
                for field in params.fields[resource_type]:
                    if field not in self.allowed_fields:
                        errors.append(
                            JSONAPIError(
                                title="Invalid Field",
                                detail=f"Field '{field}' is not allowed for resource type '{resource_type}'",
                                status="400",
                                source=ErrorSource(
                                    parameter=f"fields[{resource_type}]"
                                ),
                            )
                        )

        # Validate includes
        if params.include and self.allowed_relationships:
            if self.max_includes and len(params.include) > self.max_includes:
                errors.append(
                    JSONAPIError(
                        title="Too Many Includes",
                        detail=f"Too many includes: maximum {self.max_includes} allowed",
                        status="400",
                        source=ErrorSource(parameter="include"),
                    )
                )

            for relationship in params.include:
                root = relationship.split(".")[0]
                if root not in self.allowed_relationships:
                    errors.append(
                        JSONAPIError(
                            title="Invalid Relationship",
                            detail=f"Relationship '{relationship}' is not allowed for inclusion",
                            status="400",
                            source=ErrorSource(parameter="include"),
                        )
                    )

        # Validate sort
        if params.sort and self.allowed_sort_fields:
            for field in params.sort.keys():
                if field not in self.allowed_sort_fields:
                    errors.append(
                        JSONAPIError(
                            title="Invalid Sort Field",
                            detail=f"Sort field '{field}' is not allowed",
                            status="400",
                            source=ErrorSource(parameter="sort"),
                        )
                    )

        # Validate filters
        if params.filters:
            for field in params.filters:
                for operator_str, condition in params.filters[field].items():
                    print(f"Operator: {operator_str}")
                    operator = FilterOperator(operator_str)

                    if (
                        self.allowed_filter_fields
                        and field not in self.allowed_filter_fields
                    ):
                        errors.append(
                            JSONAPIError(
                                title="Invalid Filter Field",
                                detail=f"Filter field '{field}' is not allowed",
                                status="400",
                                source=ErrorSource(parameter=f"filter[{field}]"),
                            )
                        )

                    if field in self.allowed_filter_operators:
                        allowed_ops = self.allowed_filter_operators[field]
                        if operator not in allowed_ops:
                            errors.append(
                                JSONAPIError(
                                    title="Invalid Filter Operator",
                                    detail=f"Filter operator '{operator.value}' is not allowed for field '{field}'",
                                    status="400",
                                    source=ErrorSource(
                                        parameter=f"filter[{field}][{operator.value}]"
                                    ),
                                )
                            )

        # Validate pagination
        if params.pagination and self.max_page_size:
            size = params.pagination.get("size")
            limit = params.pagination.get("limit")

            if size and int(size) > self.max_page_size:
                errors.append(
                    JSONAPIError(
                        title="Invalid Page Size",
                        detail=f"Page size cannot exceed {self.max_page_size}",
                        status="400",
                        source=ErrorSource(parameter="page[size]"),
                    )
                )

            if limit and int(limit) > self.max_page_size:
                errors.append(
                    JSONAPIError(
                        title="Invalid Limit",
                        detail=f"Limit cannot exceed {self.max_page_size}",
                        status="400",
                        source=ErrorSource(parameter="page[limit]"),
                    )
                )

        return errors
