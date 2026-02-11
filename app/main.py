from fastapi import FastAPI

from .routers import auth, users, transactions

app = FastAPI()

# auth
app.include_router(
    auth.router,
    prefix="",
    tags=["auth"],
    responses={
        409: {"description": "Invalid login credentials"},
        }    
    )

# users
app.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    responses={
        409: {"description": "Registration failed due to overlapping name or email."}
        }    
    )

# transactions
app.include_router(
    transactions.router,
    prefix="/wallet",
    tags=["users"],
    responses={
        }    
    )