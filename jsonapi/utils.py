from typing import Any, Dict, List, Optional, Union

from jsonapi.document import (
    JSONAPIDocument,
    JSONAPIError,
    Links,
    MetaObject,
    Resource,
    ResourceIdentifier,
)


def create_error_document(
    errors: Union[JSONAPIError, List[JSONAPIError]],
) -> JSONAPIDocument:
    """Create an error document from one or more JSONAPIError objects."""
    if isinstance(errors, JSONAPIError):
        errors = [errors]
    return JSONAPIDocument(errors=errors)


def create_success_document(
    resource: Union[Resource, List[Resource], Dict[str, Any]],
    included: Optional[List[Resource]] = None,
    meta: MetaObject = None,
    links: Optional[Links] = None,
) -> JSONAPIDocument:
    """Create a success document from a resource or resource data."""
    # If resource is a dict, we need to convert it to a Resource object
    if isinstance(resource, dict):
        # This is a simplified conversion - in a real implementation,
        # you might want more sophisticated dict-to-Resource conversion
        from jsonapi.document import Resource

        resource = Resource(**resource)

    return JSONAPIDocument(data=resource, included=included, meta=meta, links=links)


def create_resource_identifier(
    resource_type: str,
    resource_id: Optional[str] = None,
    local_id: Optional[str] = None,
    meta: MetaObject = None,
) -> ResourceIdentifier:
    return ResourceIdentifier(
        type=resource_type, id=resource_id, lid=local_id, meta=meta
    )
