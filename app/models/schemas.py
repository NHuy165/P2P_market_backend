from pydantic import EmailStr
from typing import Annotated
from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import datetime, timezone

# ====================== BASE ====================== #

class OrderStatus(Enum):
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    
class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    SALE = "SALE"
    PURCHASE = "PURCHASE"

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
    
# Transaction base
class TransactionBase(SQLModel):
    amount: Annotated[float, Field(gt=0)]
    
# ====================== INPUT ====================== #

# User input (account creation)
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
    
    status: OrderStatus
    created_at: datetime
    
# ====================== SPECIAL OUTPUT ====================== #
# These inputs are only shown to special accounts

# User profile shown to account owner and admins    
class UserOutputSpecial(UserOutput):
    email: EmailStr
    is_active: bool
    balance: float
    
    items: list[ItemOutput]
    
# Item shown to users with its seller included
class ItemOutputWithSeller(ItemOutput):
    seller: UserOutput
    
# Transaction history shown to account owner and admins
class TranstionOutput(TransactionBase):
    id: int
    type: TransactionType
    user_id: int
    created_at: datetime

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
class OrderUpdate(OrderBase):
    quantity: Annotated[int | None, Field(gt=0)] = None
    price_per_item: Annotated[float | None, Field(gt=0)] = None
    status: OrderStatus | None = None