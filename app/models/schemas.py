from pydantic import EmailStr
from typing import Annotated
from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import datetime, timezone

# ====================== BASE ====================== #

class Status(Enum):
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"

# User base
class UserBase(SQLModel):
    username: Annotated[str, Field(regex=r"^[a-zA-Z0-9_]+$")]
    
# Item base
class ItemBase(SQLModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[float, Field(gt=0)]
    description: str | None = None
    stock_quantity: Annotated[int, Field(ge=0)] = 0 
    
# Order base
class OrderBase(SQLModel):
    quantity: Annotated[int, Field(gt=0)]
    price_per_item: Annotated[float, Field(gt=0)] # Prevents price changes
    
# ====================== INPUT ====================== #

# User input by user (account creation and login)
class UserInput(UserBase):
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]

# Item input by user
class ItemInput(ItemBase):
    pass

class OrderInput(OrderBase):
    item_id: int
    
# ====================== OUTPUT ====================== #

# User profile shown to normal users
class UserOutput(UserBase):
    id: int

# Item shown to users
class ItemOutput(ItemBase):
    id: int
    seller_id: int

# Orders are always shown to the public
class OrderOutput(OrderBase):
    id: int
    
    item_id: int
    buyer_id: int
    seller_id: int
    
    item: ItemOutput
    buyer: UserOutput
    seller: UserOutput
    
    status: Status
    created_at: datetime
    
# ====================== SPECIAL OUTPUT ====================== #

# User profile shown to account owner and admins    
class UserOutputSpecial(UserOutput):
    email: EmailStr
    is_active: bool
    balance: float
    
    items: list[ItemOutput]
    
# Item shown to users with its seller included
class ItemOutputWithUser(ItemOutput):
    user: UserOutput

# ====================== UPDATE ====================== #

# User update schema
class UserUpdate(UserBase):
    username: Annotated[str | None, Field(regex=r"^[a-zA-Z0-9_]+$")] = None
    email: EmailStr | None = None
    password: Annotated[str | None, Field(min_length=8)] = None
    
# Item update schema
class ItemUpdate(ItemBase):
    name: Annotated[str | None, Field(min_length=1)] = None
    price: Annotated[float | None, Field(gt=0)] = None
    description: str | None = None
    stock_quantity: Annotated[int | None, Field(ge=0)] = None
    stock_quantity_relative: int | None = None
    
# Order update schema. Buyer, seller and item cannot be changed.
class Order(OrderBase):
    quantity: Annotated[int | None, Field(gt=0)] = None
    price_per_item: Annotated[float | None, Field(gt=0)] = None
    
    status: Status | None = None
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone.utc))]