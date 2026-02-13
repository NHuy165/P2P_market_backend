from pydantic import EmailStr, BaseModel
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone

# ----- BASE ----- #

class UserBase(SQLModel):
    username: Annotated[str, Field(regex=r"^[a-zA-Z0-9_]+$", unique=True)]
    description: str | None = None
    
# ----- INPUT ----- #
    
# Account creation
class UserInput(UserBase):
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]
    
# ----- OUTPUT PUBLIC ----- #
    
# User profile shown to normal users
class UserOutput(UserBase):
    id: int
    created_at: datetime
    
# ----- OUTPUT PRIVATE ----- #
    
from .items import ItemOutput

# User profile shown to account owner and admins    
class UserOutputPrivate(UserOutput):
    email: EmailStr
    
    is_active: bool
    is_admin: bool
    is_banned: bool
    is_deleted: bool
    
    balance: float
    
    items: list[ItemOutput]
    
# ----- SORT AND FILTER ----- #

# ----- FILTER ----- #

# ----- UPDATE ----- #

class UserUpdate(UserBase):
    username: Annotated[str | None, Field(regex=r"^[a-zA-Z0-9_]+$")] = None
    email: EmailStr | None = None
    password: Annotated[str | None, Field(min_length=8)] = None
    description: str | None = None
    
    is_active: bool | None = None
    # is_deleted: bool | None = None (user deletion is done via a separate request)
    
class UserUpdateAdmin(UserUpdate):
    is_admin: bool | None = None
    is_banned: bool | None = None
    
# ----- DATABASE ----- #

if TYPE_CHECKING:
    from .items import Item
    from .orders import Order
    from .transactions import Transaction
    
# User in database    
class User(UserBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    
    hashed_password: Annotated[str, Field(min_length=8)]
    email: EmailStr
    balance: float = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    is_active: bool = True
    is_admin: bool = False
    is_banned: bool = False
    is_deleted: bool = False
    
    
    items: Annotated[list["Item"], Relationship(back_populates="seller")] # Items in stock
    buy_orders: Annotated[list["Order"], Relationship(back_populates="buyer")] # Associated buy orders
    sell_orders: Annotated[list["Order"], Relationship(back_populates="seller")] # Associated sell orders
    transactions: Annotated[list["Transaction"], Relationship(back_populates="user")] # Associated transactions

    