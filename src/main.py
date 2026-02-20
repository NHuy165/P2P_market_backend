from fastapi import APIRouter, Depends, FastAPI
from typing import Any

from .routes.auth.core import verify_admin
from .routes import auth, items, orders, transactions, users
from .database import create_db_and_tables

app = FastAPI(
    responses={
        409: {"description": "Invalid login credentials."}
    }
)


admin_router = APIRouter()

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
    dependencies=[Depends(verify_admin)],
    responses={
        403: {"description": "User does not have admin privileges."}
    }
    )