from fastapi import FastAPI

from .routes import auth, users, transactions, items

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
        404: {"description": "User not found."},
        409: {"description": "Registration failed due to overlapping name or email."}
        }    
    )

# transactions
app.include_router(
    transactions.router,
    prefix="/wallet",
    tags=["transactions"],
    responses={
        409: {"description": "Negative balance due to purchase or withdrawal."}
        }    
    )

# items
app.include_router(
    items.router,
    prefix="/items",
    tags=["items"],
    responses={
        400: {"description": "Entered both relative and absolute quantity when updating item."},
        404: {"description": "Item not found."},
        409: {"description": "Conflicting values.",
              "examples": {
                  "Item name conflict": {
                      "value": {"detail": "Another one of your items already has this name."}
                  },
                  "Negative item quantity": {
                      "value": {"detail": "Item quantity update would cause quantity to go negative."}
                  },
              }}
        }    
    )