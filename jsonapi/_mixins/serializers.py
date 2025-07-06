# validation_mixins.py

from typing import Any, Dict, List, Optional

from pydantic import model_serializer


class ResourceSerializerMixin:
    @model_serializer(mode="plain")
    def to_jsonapi(self, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        base = {
            "type": getattr(self, "type", None),
            "id": getattr(self, "id", None),
            "lid": getattr(self, "lid", None),
        }
        meta = getattr(self, "meta", None)
        if meta:
            base["meta"] = meta
        links = getattr(self, "links", None)
        if links:
            base["links"] = dict(links.model_dump(exclude_none=True))
        attributes = getattr(self, "attributes", None)
        if attributes:
            if fields:
                base["attributes"] = dict(
                    attributes.model_dump(include=set(fields), exclude_none=True)
                )
            else:
                base["attributes"] = dict(attributes.model_dump(exclude_none=True))
        relationships = getattr(self, "relationships", None)
        if relationships:
            base["relationships"] = {
                k: dict(v.model_dump(exclude_none=True))
                for k, v in relationships.items()
            }
        return {k: v for k, v in base.items() if v is not None}


class ErrorSerializerMixin:
    @model_serializer(mode="plain")
    def to_jsonapi(self) -> Dict[str, Any]:
        return dict(getattr(self, "model_dump")(exclude_none=True))


class DocumentSerializerMixin:
    @model_serializer(mode="plain")
    def to_jsonapi(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        data = getattr(self, "data", None)
        if data:
            if isinstance(data, list):
                result["data"] = [d.to_jsonapi() for d in data]
            else:
                result["data"] = data.to_jsonapi()
        errors = getattr(self, "errors", None)
        if errors:
            result["errors"] = [e.to_jsonapi() for e in errors]
        meta = getattr(self, "meta", None)
        if meta:
            result["meta"] = meta
        jsonapi = getattr(self, "jsonapi", None)
        if jsonapi:
            result["jsonapi"] = jsonapi.model_dump(exclude_none=True)
        links = getattr(self, "links", None)
        if links:
            result["links"] = links.model_dump(exclude_none=True)
        included = getattr(self, "included", None)
        if included:
            result["included"] = [i.to_jsonapi() for i in included]
        return result
