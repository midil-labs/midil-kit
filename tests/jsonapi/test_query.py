"""
Tests for midil.jsonapi.query
"""
import pytest
from pydantic import ValidationError

from midil.jsonapi.query import (
    PaginationParams,
    SortDirection,
    SortField,
    IncludeField,
    SortQueryParams,
    _DEFAULT_PAGE_SIZE,
    _MAX_PAGE_SIZE,
)


class TestPaginationParams:
    """Tests for PaginationParams class."""

    def test_pagination_params_defaults(self) -> None:
        """Test PaginationParams with default values."""
        params = PaginationParams()

        assert params.number == 1
        assert params.size == 10

    def test_pagination_params_custom_values(self) -> None:
        """Test PaginationParams with custom values."""
        params = PaginationParams(number=5, size=25)

        assert params.number == 5
        assert params.size == 25

    def test_pagination_params_number_validation(self) -> None:
        """Test that page number must be >= 1."""
        # Valid number
        params = PaginationParams(number=1)
        assert params.number == 1

        # Large number should be valid
        params = PaginationParams(number=1000)
        assert params.number == 1000

        # Invalid number (< 1)
        with pytest.raises(ValidationError):
            PaginationParams(number=0)

        with pytest.raises(ValidationError):
            PaginationParams(number=-1)

    def test_pagination_params_size_validation(self) -> None:
        """Test that page size must be between 1 and 100."""
        # Valid sizes
        params = PaginationParams(size=1)
        assert params.size == 1

        params = PaginationParams(size=50)
        assert params.size == 50

        params = PaginationParams(size=100)
        assert params.size == 100

        # Invalid sizes
        with pytest.raises(ValidationError):
            PaginationParams(size=0)

        with pytest.raises(ValidationError):
            PaginationParams(size=-1)

        with pytest.raises(ValidationError):
            PaginationParams(size=101)

        with pytest.raises(ValidationError):
            PaginationParams(size=1000)

    def test_pagination_params_type_validation(self) -> None:
        """Test type validation for pagination parameters."""
        # String numbers should be converted
        params = PaginationParams(number="5", size="20")  # type: ignore
        assert params.number == 5
        assert params.size == 20

        # Invalid types should raise validation error
        with pytest.raises(ValidationError):
            PaginationParams(number="invalid")  # type: ignore

        with pytest.raises(ValidationError):
            PaginationParams(size="invalid")  # type: ignore


class TestSortDirection:
    """Tests for SortDirection enum."""

    def test_sort_direction_values(self) -> None:
        """Test SortDirection enum values."""
        assert SortDirection.ASC == "asc"
        assert SortDirection.DESC == "desc"

    def test_sort_direction_is_string_enum(self) -> None:
        """Test that SortDirection is a string enum."""
        from enum import StrEnum

        assert issubclass(SortDirection, StrEnum)

    def test_sort_direction_comparison(self) -> None:
        """Test comparing SortDirection values."""
        assert SortDirection.ASC != SortDirection.DESC
        assert SortDirection.ASC == "asc"
        assert SortDirection.DESC == "desc"


class TestSortField:
    """Tests for SortField class."""

    def test_sort_field_ascending(self) -> None:
        """Test SortField for ascending sort."""
        field = SortField("name")

        assert field.value == "name"
        assert field.direction == SortDirection.ASC

    def test_sort_field_descending(self) -> None:
        """Test SortField for descending sort."""
        field = SortField("-name")

        assert field.value == "name"
        assert field.direction == SortDirection.DESC

    def test_sort_field_complex_field_names(self) -> None:
        """Test SortField with complex field names."""
        # Dot notation
        field = SortField("user.profile.name")
        assert field.value == "user.profile.name"
        assert field.direction == SortDirection.ASC

        # Descending dot notation
        field = SortField("-user.profile.created_at")
        assert field.value == "user.profile.created_at"
        assert field.direction == SortDirection.DESC

        # Underscore naming
        field = SortField("created_at")
        assert field.value == "created_at"
        assert field.direction == SortDirection.ASC

    def test_sort_field_multiple_dashes(self) -> None:
        """Test SortField with multiple dashes (only first should indicate direction)."""
        field = SortField("-multi-dash-field")
        assert field.value == "multi-dash-field"
        assert field.direction == SortDirection.DESC

    def test_sort_field_root_model(self) -> None:
        """Test that SortField is a RootModel."""
        from pydantic import RootModel

        assert issubclass(SortField, RootModel)

        field = SortField("test")
        assert hasattr(field, "root")

    def test_sort_field_string_representation(self) -> None:
        """Test string representation of SortField."""
        field = SortField("test_field")
        # Should be able to access the string value
        assert field.value == "test_field"

    def test_sort_field_edge_cases(self) -> None:
        """Test SortField edge cases."""
        # Empty string
        field = SortField("")
        assert field.value == ""
        assert field.direction == SortDirection.ASC

        # Just a dash
        field = SortField("-")
        assert field.value == ""
        assert field.direction == SortDirection.DESC

        # Field starting with multiple dashes
        field = SortField("--field")
        assert field.value == "field"
        assert field.direction == SortDirection.DESC


class TestIncludeField:
    """Tests for IncludeField class."""

    def test_include_field_single_value(self) -> None:
        """Test IncludeField with single relationship."""
        field = IncludeField(["author"])
        assert field.values == ["author"]

    def test_include_field_multiple_values(self) -> None:
        """Test IncludeField with multiple relationships."""
        field = IncludeField(["author", "comments", "tags"])
        assert field.values == ["author", "comments", "tags"]

    def test_include_field_nested_relationships(self) -> None:
        """Test IncludeField with nested relationships."""
        field = IncludeField(["author.profile", "comments.author"])
        assert field.values == ["author.profile", "comments.author"]

    def test_include_field_empty_list(self) -> None:
        """Test IncludeField with empty list."""
        field = IncludeField([])
        assert field.values == []

    def test_include_field_root_model(self) -> None:
        """Test that IncludeField is a RootModel."""
        from pydantic import RootModel

        assert issubclass(IncludeField, RootModel)

        field = IncludeField(["test"])
        assert hasattr(field, "root")

    def test_include_field_complex_paths(self) -> None:
        """Test IncludeField with complex relationship paths."""
        complex_includes = [
            "user.profile.avatar",
            "posts.comments.author",
            "categories.parent.children",
        ]
        field = IncludeField(complex_includes)
        assert field.values == complex_includes


class TestSortQueryParams:
    """Tests for SortQueryParams class."""

    def test_sort_query_params_single_field(self) -> None:
        """Test SortQueryParams with single sort field."""
        params = SortQueryParams(sort=[SortField("name")])

        assert len(params.sort) == 1
        assert params.sort[0].value == "name"
        assert params.sort[0].direction == SortDirection.ASC

    def test_sort_query_params_multiple_fields(self) -> None:
        """Test SortQueryParams with multiple sort fields."""
        sort_fields = [SortField("name"), SortField("-created_at")]
        params = SortQueryParams(sort=sort_fields)

        assert len(params.sort) == 2
        assert params.sort[0].value == "name"
        assert params.sort[0].direction == SortDirection.ASC
        assert params.sort[1].value == "created_at"
        assert params.sort[1].direction == SortDirection.DESC

    def test_sort_query_params_string_parsing(self) -> None:
        """Test SortQueryParams parsing from comma-separated string."""
        params = SortQueryParams(sort="name,-created_at,email")

        assert len(params.sort) == 3
        assert params.sort[0].value == "name"
        assert params.sort[0].direction == SortDirection.ASC
        assert params.sort[1].value == "created_at"
        assert params.sort[1].direction == SortDirection.DESC
        assert params.sort[2].value == "email"
        assert params.sort[2].direction == SortDirection.ASC

    def test_sort_query_params_string_with_spaces(self) -> None:
        """Test SortQueryParams parsing string with spaces."""
        params = SortQueryParams(sort="name, -created_at , email")

        assert len(params.sort) == 3
        assert params.sort[0].value == "name"
        assert params.sort[1].value == "created_at"
        assert params.sort[2].value == "email"

    def test_sort_query_params_empty_string(self) -> None:
        """Test SortQueryParams with empty string."""
        params = SortQueryParams(sort="")
        assert len(params.sort) == 0

    def test_sort_query_params_string_with_empty_values(self) -> None:
        """Test SortQueryParams parsing string with empty values."""
        params = SortQueryParams(sort="name,,,-created_at,")

        # Should filter out empty strings
        assert len(params.sort) == 2
        assert params.sort[0].value == "name"
        assert params.sort[1].value == "created_at"

    def test_sort_query_params_sort_map(self) -> None:
        """Test SortQueryParams internal sort map."""
        params = SortQueryParams(sort="name,-created_at,email")

        # Check internal sort map
        assert "name" in params._sort_map
        assert "created_at" in params._sort_map
        assert "email" in params._sort_map

        # Test that map values are correct
        assert params._sort_map["name"].direction == SortDirection.ASC
        assert params._sort_map["created_at"].direction == SortDirection.DESC
        assert params._sort_map["email"].direction == SortDirection.ASC

    def test_sort_query_params_getattr(self) -> None:
        """Test SortQueryParams __getattr__ method."""
        params = SortQueryParams(sort="name,-created_at,email")

        # Should be able to access fields by name
        name_field = params.name
        assert name_field is not None
        assert name_field.value == "name"
        assert name_field.direction == SortDirection.ASC

        created_at_field = params.created_at
        assert created_at_field is not None
        assert created_at_field.value == "created_at"
        assert created_at_field.direction == SortDirection.DESC

        # Non-existent field should return None
        assert params.non_existent is None

    def test_sort_query_params_complex_field_names(self) -> None:
        """Test SortQueryParams with complex field names."""
        params = SortQueryParams(sort="user.profile.name,-post.created_at")

        # Should handle dot notation in sort map
        assert params._sort_map["user.profile.name"].direction == SortDirection.ASC
        assert params._sort_map["post.created_at"].direction == SortDirection.DESC

    def test_sort_query_params_field_validator_with_list(self) -> None:
        """Test that field validator works correctly with list input."""
        sort_fields = [SortField("name"), SortField("-date")]
        params = SortQueryParams(sort=sort_fields)

        # Should not modify list input
        assert len(params.sort) == 2
        assert isinstance(params.sort[0], SortField)
        assert isinstance(params.sort[1], SortField)

    def test_sort_query_params_fastapi_compatibility(self) -> None:
        """Test that SortQueryParams is FastAPI compatible."""
        # Should be able to use as query parameter
        # This tests the structure and typing
        params = SortQueryParams(sort="name,-created_at")

        # Should have proper attributes for FastAPI
        assert hasattr(params, "sort")
        assert isinstance(params.sort, list)

    def test_sort_query_params_duplicate_fields(self) -> None:
        """Test SortQueryParams behavior with duplicate field names."""
        params = SortQueryParams(sort="name,-name,email")

        # All should be in the sort list
        assert len(params.sort) == 3

        # But sort map should only have the last occurrence
        assert params._sort_map["name"].direction == SortDirection.DESC

    def test_sort_query_params_initialization_order(self) -> None:
        """Test that initialization properly sets up the sort map."""
        params = SortQueryParams(sort="a,-b,c")

        # Verify __init__ was called and sort map was set up
        assert hasattr(params, "_sort_map")
        assert len(params._sort_map) == 3
        assert all(isinstance(sf, SortField) for sf in params._sort_map.values())


class TestConstants:
    """Tests for module constants."""

    def test_default_page_size(self) -> None:
        """Test DEFAULT_PAGE_SIZE constant."""
        assert _DEFAULT_PAGE_SIZE == 10

    def test_max_page_size(self) -> None:
        """Test MAX_PAGE_SIZE constant."""
        assert _MAX_PAGE_SIZE == 100

    def test_constants_match_pagination_defaults(self) -> None:
        """Test that constants match PaginationParams defaults."""
        params = PaginationParams()
        assert params.size == _DEFAULT_PAGE_SIZE
        assert params.size <= _MAX_PAGE_SIZE


class TestIntegration:
    """Integration tests for query parameter classes."""

    def test_typical_query_parameter_usage(self) -> None:
        """Test typical usage of query parameters together."""
        # Simulate FastAPI query parameters
        pagination = PaginationParams(number=2, size=20)
        sorting = SortQueryParams(sort="name,-created_at")
        includes = IncludeField(["author", "comments.author"])

        # Verify all work together
        assert pagination.number == 2
        assert pagination.size == 20

        assert len(sorting.sort) == 2
        assert sorting.name.direction == SortDirection.ASC  # type: ignore
        assert sorting.created_at.direction == SortDirection.DESC  # type: ignore

        assert "author" in includes.values
        assert "comments.author" in includes.values

    def test_edge_case_combinations(self) -> None:
        """Test edge cases when combining different query parameters."""
        # Minimum pagination
        pagination = PaginationParams(number=1, size=1)

        # No sorting
        sorting = SortQueryParams(sort=[])

        # No includes
        includes = IncludeField([])

        # Should all be valid
        assert pagination.number == 1
        assert pagination.size == 1
        assert len(sorting.sort) == 0
        assert len(includes.values) == 0

    def test_maximum_values(self) -> None:
        """Test with maximum allowed values."""
        # Maximum page size
        pagination = PaginationParams(number=999999, size=100)

        # Complex sorting
        sorting = SortQueryParams(
            sort="field1,-field2,field3.nested,-field4.deeply.nested"
        )

        # Complex includes
        includes = IncludeField(["rel1", "rel2.nested", "rel3.deeply.nested.path"])

        # Should all be valid
        assert pagination.size == 100
        assert len(sorting.sort) == 4
        assert len(includes.values) == 3

    def test_validation_error_handling(self) -> None:
        """Test that validation errors are properly raised."""
        # Invalid pagination
        with pytest.raises(ValidationError):
            PaginationParams(size=0)

        # Empty sort fields should be filtered out during parsing
        sorting = SortQueryParams(sort=",,")
        assert len(sorting.sort) == 0  # Should be empty, not error
