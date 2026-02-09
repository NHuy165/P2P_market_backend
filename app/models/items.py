from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Relationship, Field
from .schemas import ItemBase

if TYPE_CHECKING:
    from .users import User
    from .orders import Order

# Item in database
class Item(ItemBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    seller_id: Annotated[int, Field(foreign_key="user.id")]
    
    user: Annotated['User', Relationship(back_populates='items')] # The user this item belongs to
    orders: Annotated[list['Order'], Relationship(back_populates='item')] # The orders associated with this item
    
