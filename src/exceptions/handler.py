from fastapi import Request
from fastapi.responses import JSONResponse

from .core import ExceptionCustom, ExceptionResponse

def custom_exceptions_handler(request: Request, e: ExceptionCustom):
    response = ExceptionResponse(
        exception_type=e.exception_type,
        message=e.message
    )
    return JSONResponse(
        status_code=e.status_code,
        content=response.model_dump(),
        headers=e.headers
    )
    