from contextlib import asynccontextmanager

import uvicorn
from fastapi import APIRouter, Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.database import create_db_and_tables, dispose
from src.core.dependencies import verify_admin
from src.exceptions.core import ExceptionCustom, Responses
from src.exceptions.handler import (
    custom_exceptions_handler,
    generic_handler,
    starlette_exceptions_handler,
    validation_exceptions_handler,
)
from src.routes import auth, items, orders, transactions, users

# Main app
# Can't add generic error responses here since some functions do not need users to log in.


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_db_and_tables()

    # App runs
    yield

    # Shutdown
    await dispose()


app = FastAPI(lifespan=lifespan)

# For adding admin routers, and these all use the verify_admin dependency.
admin_router = APIRouter(
    dependencies=[Depends(verify_admin)],
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    },
)

# Adding exception handlers
app.add_exception_handler(RequestValidationError, validation_exceptions_handler)  # type: ignore
app.add_exception_handler(StarletteHTTPException, starlette_exceptions_handler)  # type: ignore
app.add_exception_handler(ExceptionCustom, custom_exceptions_handler)  # type: ignore
app.add_exception_handler(Exception, generic_handler)


# ----- Auth ----- #

app.include_router(
    auth.core.router,
    prefix="",
    tags=["auth"],
)

# ----- Users ----- #

app.include_router(
    users.core.router,
    prefix="/users",
    tags=["users"],
)

admin_router.include_router(
    users.admin.router,
    prefix="/users",
    tags=["users"],
)

# ----- Items ----- #

app.include_router(
    items.core.router,
    prefix="/items",
    tags=["items"],
)

admin_router.include_router(
    items.admin.router,
    prefix="/items",
    tags=["items"],
)

# ----- Orders ----- #

app.include_router(
    orders.core.router,
    prefix="/orders",
    tags=["orders"],
)

admin_router.include_router(
    orders.admin.router,
    prefix="/items",
    tags=["items"],
)

# ----- Transactions ----- #

app.include_router(
    transactions.core.router,
    prefix="/transactions",
    tags=["transactions"],
)

admin_router.include_router(
    transactions.admin.router,
    prefix="/items",
    tags=["items"],
)

# ----- Admin ----- #

app.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
