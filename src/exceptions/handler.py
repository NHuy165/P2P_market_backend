from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core import ExceptionCustom, ExceptionResponse, ExceptionType


async def custom_exceptions_handler(request: Request, e: ExceptionCustom):
    response = ExceptionResponse(exception_type=e.exception_type, message=e.message)
    return JSONResponse(
        status_code=e.status_code, content=response.model_dump(), headers=e.headers
    )


async def starlette_exceptions_handler(request: Request, e: StarletteHTTPException):
    if e.status_code == 404:
        exception_type = ExceptionType.NOT_FOUND
    elif e.status_code == 405:
        exception_type = ExceptionType.METHOD

    # This isn't supposed to happen
    else:
        exception_type = ExceptionType.REQUEST

    response = ExceptionResponse(exception_type=exception_type, message=str(e.detail))
    return JSONResponse(
        status_code=e.status_code, content=response.model_dump(), headers=e.headers
    )


# Deliberate conversion of 422 to 400 here.
async def validation_exceptions_handler(request: Request, e: RequestValidationError):
    response = ExceptionResponse(
        exception_type=ExceptionType.REQUEST, message="Request validation failed."
    )
    return JSONResponse(status_code=400, content=response.model_dump())


async def generic_handler(request: Request, e: Exception):
    response = ExceptionResponse(
        exception_type=ExceptionType.REQUEST, message="Internal server error."
    )
    return JSONResponse(status_code=500, content=response.model_dump())
