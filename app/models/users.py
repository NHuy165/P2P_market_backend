from pydantic import EmailStr
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Relationship, Field
from .schemas import UserBase

if TYPE_CHECKING:
    from .items import Item
    from .orders import Order
    
# User in database    
class User(UserBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    hashed_password: Annotated[str, Field(min_length=8)]
    
    email: EmailStr
    is_active: bool = True
    is_owner: bool = False
    balance: float = 0
    
    items: Annotated[list["Item"], Relationship(back_populates="user")] # Items in stock
    buy_orders: Annotated[list["Order"], Relationship(back_populates="buyer")] # Associated buy orders
    sell_orders: Annotated[list["Order"], Relationship(back_populates="seller")] # Associated sell orders

    