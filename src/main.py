from fastapi import APIRouter, Depends, FastAPI
from typing import Any

from .models_schemas.exceptions import ExceptionCustom, Responses
from .core.dependencies import verify_admin
from .routes import auth, items, orders, transactions, users
from .core.database import create_db_and_tables
from .core.exceptions_handling import custom_exceptions_handler

# Main app
# Can't add generic error responses here since some functions do not need users to log in.
app = FastAPI()

# For adding admin routers, and these all use the verify_admin dependency.
admin_router = APIRouter(
    dependencies=[Depends(verify_admin)],
    responses={
        401: Responses.RESPONSE_401_UNAUTHORIZED,
        403: Responses.RESPONSE_403_FORBIDDEN,
    }
)

app.add_exception_handler(ExceptionCustom, custom_exceptions_handler) # type: ignore

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    


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

items_errors : dict[int | str, dict[str, Any]] | None = {
    400: {"description": "Entered both relative and absolute quantity."},
    404: {"description": "Couldn't find item."},
    409: {"description": "Overlapping name, negative stock or balance."}
    }    

app.include_router(
    items.core.router,
    prefix="/items",
    tags=["items"],
    responses=items_errors
    )

# ----- Orders ----- #
orders_errors : dict[int | str, dict[str, Any]] | None = {
    400: {"description": "Entered both relative and absolute quantity."},
    404: {"description": "Couldn't find user, item or order with the specified information."},
    409: {"description": "Buying own items. Negative stock or balance upon ordering. Order update timeout. Order update invalid due to status no longer being pending."}
    }     
app.include_router(
    orders.core.router,
    prefix="/orders",
    tags=["orders"],
    responses=orders_errors
    )

# ----- Transactions ----- #
transactions_errors : dict[int | str, dict[str, Any]] | None = {
    404: {"description": "User not found."},
    409: {"description": "Negative balance due to purchase or withdrawal."}
    }    

app.include_router(
    transactions.core.router,
    prefix="/transactions",
    tags=["transactions"],
    responses=transactions_errors
    )

# ----- Admin ----- #

app.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"],
    )