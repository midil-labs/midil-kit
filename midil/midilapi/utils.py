from typing import Any, Dict, Optional
from midil.jsonapi.document import JSONAPI_CONTENT_TYPE
import copy


def _replace_json_with_jsonapi(
    content: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Replace 'application/json' with Midil's JSON:API media type preserving schema.
    """
    if not isinstance(content, dict):
        return content

    content = copy.deepcopy(content)  # Copy to avoid mutating the original dict
    json_schema = content.pop("application/json", None)
    if json_schema:
        content[JSONAPI_CONTENT_TYPE] = json_schema
    return content


def _update_openapi_jsonapi_media_types(openapi_schema: Dict[str, Any]) -> None:
    """
    Mutates the OpenAPI schema in-place to replace 'application/json' with Midil's JSON:API media type.
    """
    for path_item in openapi_schema.get("paths", {}).values():
        for method_data in path_item.values():
            # Update request bodies
            request_body = method_data.get("requestBody")
            if request_body and "content" in request_body:
                request_body["content"] = _replace_json_with_jsonapi(
                    request_body["content"]
                )

            # Update responses
            responses = method_data.get("responses", {})
            for response in responses.values():
                if "content" in response:
                    response["content"] = _replace_json_with_jsonapi(
                        response["content"]
                    )
