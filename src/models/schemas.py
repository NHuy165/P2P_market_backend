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

class UserBase(SQLModel):
    username: Annotated[str, Field(regex=r"^[a-zA-Z0-9_]+$", unique=True)]
    
class ItemBase(SQLModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[float, Field(gt=0)]
    description: str | None = None
    stock_quantity: Annotated[int, Field(ge=0)] = 0 
    
class OrderBase(SQLModel):
    quantity: Annotated[int, Field(gt=0)]
    price_per_item: Annotated[float, Field(gt=0)] # Prevents price changes
    
class TransactionBase(SQLModel):
    amount: Annotated[float, Field(gt=0)]
    
# ====================== INPUT ====================== #

# Account creation
class UserInput(UserBase):
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]

# Item creation
class ItemInput(ItemBase):
    is_active: bool = False

class OrderInput(OrderBase):
    item_id: int
    
class TransactionInput(TransactionBase):
    pass
    
# ====================== OUTPUT ====================== #
# These outputs are shown to everypne

# User profile shown to normal users
class UserOutput(UserBase):
    id: int

# Item shown to normal users
class ItemOutput(ItemBase):
    id: int
    seller_id: int
    seller: UserOutput
    
# ====================== SPECIAL OUTPUT ====================== #
# These outputs are only shown to special accounts

# User profile shown to account owner and admins    
class UserOutputSpecial(UserOutput):
    email: EmailStr
    is_active: bool
    is_admin: bool
    is_banned: bool
    is_deleted: bool
    balance: float
    
    items: list[ItemOutput]
    
# Item shown to account owner and admins
class ItemOutputSpecial(ItemOutput):
    is_active: bool
    is_banned: bool
    is_deleted: bool
    
# Orders are only shown to account owner and admins
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
    
# Transaction history are only shown to account owner and admins
class TransactionOutput(TransactionBase):
    id: int
    type: TransactionType
    user_id: int
    created_at: datetime

# ====================== UPDATE ====================== #

class UserUpdate(UserBase):
    username: Annotated[str | None, Field(regex=r"^[a-zA-Z0-9_]+$")] = None
    email: EmailStr | None = None
    password: Annotated[str | None, Field(min_length=8)] = None
    
    is_active: bool | None = None
    # is_deleted: bool | None = None (user deletion is done via a separate request)
    
class UserUpdateAdmin(UserUpdate):
    is_admin: bool | None = None
    is_banned: bool | None = None
    
class ItemUpdate(ItemBase):
    name: Annotated[str | None, Field(min_length=1)] = None
    price: Annotated[float | None, Field(gt=0)] = None
    description: str | None = None
    stock_quantity: Annotated[int | None, Field(ge=0)] = None
    stock_quantity_relative: int | None = None
    
    is_active: bool | None = None
    # is_deleted: bool | None = None (item deletion is done via a separate request)
    
class ItemUpdateAdmin(ItemUpdate):
    is_banned: bool | None = None
    
# Buyer, seller and item cannot be changed.
class OrderUpdate(OrderBase):
    quantity: Annotated[int | None, Field(gt=0)] = None
    price_per_item: Annotated[float | None, Field(gt=0)] = None
    status: OrderStatus | None = None