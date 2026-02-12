from pydantic import EmailStr
from typing import Annotated, TYPE_CHECKING
from sqlmodel import Relationship, Field
from .schemas import UserBase

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
    
    is_active: bool = True
    is_admin: bool = False
    is_banned: bool = False
    is_deleted: bool = False
    
    
    items: Annotated[list["Item"], Relationship(back_populates="user")] # Items in stock
    buy_orders: Annotated[list["Order"], Relationship(back_populates="buyer")] # Associated buy orders
    sell_orders: Annotated[list["Order"], Relationship(back_populates="seller")] # Associated sell orders
    transactions: Annotated[list["Transaction"], Relationship(back_populates="user")] # Associated transactions

    