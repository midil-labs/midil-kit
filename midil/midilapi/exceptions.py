from typing import TYPE_CHECKING, Protocol, Any, Dict, Optional, Type, Tuple

from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi import Request, status

from midil.jsonapi.document import ErrorObject, ErrorDocument, ErrorSource
from midil.midilapi.responses import JSONAPIResponse
from loguru import logger

if TYPE_CHECKING:
    from midil.midilapi import MidilAPI


class ExceptionHandler(Protocol):
    """Protocol interface for exception handlers."""

    async def handle(self, request: Request, exc: Exception) -> JSONAPIResponse:
        ...


class ErrorSourceBuilder:
    """Helper for converting exception error locations to JSON:API ErrorSource."""

    @staticmethod
    def build(loc: Tuple[Any, ...]) -> ErrorSource:
        if not loc:
            return ErrorSource()

        first = loc[0]

        if first == "body":
            # JSON Pointer per RFC6901 with proper escaping
            pointer = "".join(
                f"/{ErrorSourceBuilder._escape_json_pointer(str(p))}" for p in loc[1:]
            )
            return ErrorSource(pointer=pointer or "/")
        elif first == "query":
            param = loc[1] if len(loc) > 1 else None
            return ErrorSource(parameter=str(param) if param else None)
        elif first == "header":
            header = loc[1] if len(loc) > 1 else None
            return ErrorSource(header=str(header) if header else None)
        else:
            # Fallback to pointer for unknown locations
            pointer = "".join(
                f"/{ErrorSourceBuilder._escape_json_pointer(str(p))}" for p in loc
            )
            return ErrorSource(pointer=pointer)

    @staticmethod
    def _escape_json_pointer(part: str) -> str:
        # Per RFC6901, ~ -> ~0 and / -> ~1
        return part.replace("~", "~0").replace("/", "~1")


class HTTPExceptionHandler:
    """Handles HTTPException converting to JSON:API errors."""

    async def handle(self, request: Request, exc: HTTPException) -> JSONAPIResponse:
        error = ErrorObject(
            status=str(exc.status_code),
            title=exc.detail if isinstance(exc.detail, str) else exc.__class__.__name__,
            detail=str(exc.detail),
        )
        return JSONAPIResponse(
            status_code=exc.status_code,
            document=ErrorDocument(errors=[error]),
        )


class ValidationExceptionHandler:
    """Handles FastAPI RequestValidationError as JSON:API validation errors."""

    def __init__(self, error_source_builder: ErrorSourceBuilder):
        self._error_source_builder = error_source_builder

    async def handle(
        self, request: Request, exc: RequestValidationError
    ) -> JSONAPIResponse:
        errors = []
        for err in exc.errors():
            loc = err.get("loc", ())
            errors.append(
                ErrorObject(
                    status=str(status.HTTP_422_UNPROCESSABLE_ENTITY),
                    title="Validation Error",
                    detail=err.get("msg", "Invalid input"),
                    source=self._error_source_builder.build(loc),
                    code=err.get("type"),
                )
            )
        return JSONAPIResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            document=ErrorDocument(errors=errors),
        )


class GenericExceptionHandler:
    """Handles any uncaught Exception as 500 Internal Server Error."""

    async def handle(self, request: Request, exc: Exception) -> JSONAPIResponse:
        logger.error("Unhandled exception occurred", exc_info=exc)
        error = ErrorObject(
            status=str(status.HTTP_500_INTERNAL_SERVER_ERROR),
            title="Internal Server Error",
            detail="An unexpected error occurred. Please try again later.",
        )
        return JSONAPIResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            document=ErrorDocument(errors=[error]),
        )


class ExceptionHandlerRegistry:
    """Registry and dispatcher for exception handlers with MRO lookup."""

    def __init__(self):
        self._handlers: Dict[Type[Exception], ExceptionHandler] = {}

    def register(self, exc_type: Type[Exception], handler: ExceptionHandler) -> None:
        self._handlers[exc_type] = handler

    def get_handler(self, exc_type: Type[Exception]) -> Optional[ExceptionHandler]:
        # Walk MRO to find the most specific handler
        for base in exc_type.__mro__:
            handler = self._handlers.get(base)
            if handler is not None:
                return handler
        return None


class JSONAPIExceptionHandlerRegistrar:
    """Single registrar instance to dispatch exceptions to registered handlers."""

    def __init__(self, app: "MidilAPI"):
        self.app = app
        self.registry = ExceptionHandlerRegistry()
        self.error_source_builder = ErrorSourceBuilder()

        # Instantiate and register handlers
        self._http_handler = HTTPExceptionHandler()
        self._validation_handler = ValidationExceptionHandler(self.error_source_builder)
        self._generic_handler = GenericExceptionHandler()

        self._register_handlers()

    def _register_handlers(self) -> None:
        self.registry.register(HTTPException, self._http_handler)  # type: ignore
        self.registry.register(RequestValidationError, self._validation_handler)  # type: ignore
        self.registry.register(Exception, self._generic_handler)

    async def __call__(self, request: Request, exc: Exception) -> JSONAPIResponse:
        handler = self.registry.get_handler(type(exc)) or self._generic_handler
        return await handler.handle(request, exc)


def register_jsonapi_exception_handlers(app: "MidilAPI") -> None:
    registrar = JSONAPIExceptionHandlerRegistrar(app)
    # Register registrar for all exception types it manages
    app.add_exception_handler(HTTPException, registrar)
    app.add_exception_handler(RequestValidationError, registrar)
    app.add_exception_handler(Exception, registrar)
