from typing import Any, Dict, List, Optional
from pydantic import model_serializer


class ResourceSerializerMixin:
    @model_serializer(mode="plain")
    def to_jsonapi(self, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "type": getattr(self, "type", None),
        }

        # Core fields
        for field in ("id", "lid", "meta"):
            value = getattr(self, field, None)
            if value is not None:
                result[field] = value

        # Links
        links = getattr(self, "links", None)
        if links:
            result["links"] = (
                links.model_dump(exclude_none=True)
                if hasattr(links, "model_dump")
                else dict(links)
            )

        # Attributes (with sparse fieldset support)
        attributes = getattr(self, "attributes", None)
        if attributes:
            result["attributes"] = (
                attributes.model_dump(include=set(fields), exclude_none=True)
                if fields and hasattr(attributes, "model_dump")
                else attributes.model_dump(exclude_none=True)
                if hasattr(attributes, "model_dump")
                else dict(attributes)
            )

        # Relationships
        relationships = getattr(self, "relationships", None)
        if relationships:
            pruned = {}
            for key, rel in relationships.items():
                if fields and key not in fields:
                    continue
                pruned[key] = (
                    rel.model_dump(exclude_none=True)
                    if hasattr(rel, "model_dump")
                    else rel
                )
            if pruned:
                result["relationships"] = pruned

        return {k: v for k, v in result.items() if v is not None}


class ErrorSerializerMixin:
    @model_serializer(mode="plain")
    def to_jsonapi(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        for field in [
            "id",
            "links",
            "status",
            "code",
            "title",
            "detail",
            "source",
            "meta",
        ]:
            val = getattr(self, field, None)
            if val is not None:
                result[field] = val

        return result


class DocumentSerializerMixin:
    @model_serializer(mode="plain")
    def to_jsonapi(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        # data
        data = getattr(self, "data", None)
        if data:
            result["data"] = (
                [d.to_jsonapi() for d in data]
                if isinstance(data, list)
                else data.to_jsonapi()
            )

        # errors
        errors = getattr(self, "errors", None)
        if errors:
            result["errors"] = [
                e.to_jsonapi() if hasattr(e, "to_jsonapi") else e for e in errors
            ]

        # meta, jsonapi, links
        for field in ["meta", "jsonapi", "links"]:
            val = getattr(self, field, None)
            if val:
                result[field] = (
                    val.model_dump(exclude_none=True)
                    if hasattr(val, "model_dump")
                    else val
                )

        # included
        included = getattr(self, "included", None)
        if included:
            result["included"] = [i.to_jsonapi() for i in included]

        return result


class QueryParamsSerializerMixin:
    def to_query_string(self) -> str:
        """Convert query parameters to query string format."""
        parts: List[str] = []

        # fields[resource]=a,b,c
        fields = getattr(self, "fields", None)
        if fields:
            for resource, field_list in fields.items():
                parts.append(f"fields[{resource}]={','.join(field_list)}")

        # include=a,b
        include = getattr(self, "include", None)
        if include:
            parts.append(f"include={','.join(include)}")

        # sort=-name,email
        sort = getattr(self, "sort", None)
        if sort:
            sort_strs = []
            for item in sort:
                direction = item.get("direction", "asc")
                field = item["field"]
                sort_strs.append(f"-{field}" if direction == "desc" else field)
            parts.append(f"sort={','.join(sort_strs)}")

        # filters
        filters = getattr(self, "filters", None)
        if filters:
            for f in filters:
                field, op, value = f["field"], f["operator"], f["value"]
                if op == "eq":
                    parts.append(f"filter[{field}]={value}")
                else:
                    value_str = (
                        ",".join(value) if isinstance(value, list) else str(value)
                    )
                    parts.append(f"filter[{field}][{op}]={value_str}")

        # pagination
        pagination = getattr(self, "pagination", None)
        if pagination:
            for key, val in pagination.items():
                parts.append(f"page[{key}]={val}")

        # extras
        extra = getattr(self, "extra_params", None)
        if extra:
            for k, v in extra.items():
                parts.append(f"{k}={v}")

        return "&".join(parts)
