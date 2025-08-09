from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi import Request, status
from midil.jsonapi.document import ErrorObject, ErrorDocument
from midil.midilapi.responses import JSONAPIResponse
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from midil.midilapi import MidilAPI


def register_jsonapi_exception_handlers(app: "MidilAPI") -> None:
    @app.exception_handler(HTTPException)
    async def _jsonapi_exc_handler(_: Request, exc: HTTPException):
        return JSONAPIResponse(
            status_code=exc.status_code,
            document=ErrorDocument(
                errors=[
                    ErrorObject(
                        status=str(exc.status_code),
                        title="HTTP Error",
                        detail=str(exc.detail),
                    )
                ]
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_: Request, exc: RequestValidationError):
        return JSONAPIResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            document=ErrorDocument(
                errors=[
                    ErrorObject(
                        status=str(status.HTTP_422_UNPROCESSABLE_ENTITY),
                        title="Validation Error",
                        detail=str(exc),
                    )
                ]
            ),
        )

    @app.exception_handler(Exception)
    async def _generic_exception_handler(_: Request, exc: Exception):
        return JSONAPIResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            document=ErrorDocument(
                errors=[
                    ErrorObject(
                        status=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
                        title="Internal Server Error",
                        detail=str(exc),
                    )
                ]
            ),
        )
