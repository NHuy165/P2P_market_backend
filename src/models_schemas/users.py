from pydantic import EmailStr, BaseModel
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from enum import Enum

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

class UserStatus(Enum):
    ACTIVE = "ACTIVE"
    BANNED = "BANNED"
    DELETED = "DELETED"
    
from .items import ItemOutput

# User profile shown to account owner and admins    
class UserOutputPrivate(UserOutput):
    email: EmailStr
    balance: float
    
    is_active: bool
    status: UserStatus
    
    items: list[ItemOutput]
    
# ----- SEARCH, SORT AND FILTER ----- #

class UserGet(BaseModel):
    """
    Since User doesn't have complex sorting and filtering, we cram everything into 1 model.
    """
    id: int | None = None
    username: str | None = None
    email: EmailStr | None = None
    
    include_admin: bool = False
    include_active: bool = True
    include_banned: bool = False
    include_deleted: bool = False

# ----- UPDATE ----- #

class UserUpdate(UserBase):
    username: Annotated[str | None, Field(regex=r"^[a-zA-Z0-9_]+$")] = None
    email: EmailStr | None = None
    description: str | None = None

    # is_deleted: bool | None = None (user deletion is done via a separate request)
    
class PasswordUpdate(BaseModel):
    old_password: Annotated[str, Field(min_length=1)] # No need to be too strict here, since we verify it anyways
    new_password: Annotated[str, Field(min_length=8)]
    
# ----- DATABASE ----- #

if TYPE_CHECKING:
    from .items import Item
    from .orders import Order
    from .transactions import Transaction
    
# User in database    
class User(UserBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    
    email: EmailStr
    hashed_password: Annotated[str, Field(min_length=8)]
    balance: float = 0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    is_admin: bool = False
    status: UserStatus = UserStatus.ACTIVE
    
    items: list["Item"] = Relationship(back_populates="seller") # Items in stock
    buy_orders: list["Order"] = Relationship(back_populates="buyer") # Associated buy orders
    sell_orders: list["Order"] = Relationship(back_populates="seller") # Associated sell orders
    transactions: list["Transaction"] = Relationship(back_populates="user") # Associated transactions

    