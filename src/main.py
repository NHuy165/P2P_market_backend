from fastapi import FastAPI

from .routes import auth, users, transactions, items, orders

app = FastAPI()

# auth
app.include_router(
    auth.router,
    prefix="",
    tags=["auth"],
    responses={
        409: {"description": "Invalid login credentials."},
        }    
    )

# users
app.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    responses={
        401: {"description": "Incorrect password."},
        404: {"description": "Couldn't find user."},
        409: {"description": "Registration failed due to overlapping name or email."}
        }    
    )

# items
app.include_router(
    items.router,
    prefix="/items",
    tags=["items"],
    responses={
        400: {"description": "Entered both relative and absolute quantity."},
        404: {"description": "Couldn't find item."},
        409: {"description": "Overlapping name, negative stock or balance."}
        }    
    )

# orders
app.include_router(
    orders.router,
    prefix="/orders",
    tags=["orders"],
    responses={
        400: {"description": "Entered both relative and absolute quantity."},
        404: {"description": "Couldn't find user, item or order with the specified information."},
        409: {"description": "Buying own items. Negative stock or balance upon ordering. Order update timeout. Order update invalid due to status no longer being pending."}
        }    
    )

# transactions
app.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"],
    responses={
        404: {"description": "User not found."},
        409: {"description": "Negative balance due to purchase or withdrawal."}
        }    
    )