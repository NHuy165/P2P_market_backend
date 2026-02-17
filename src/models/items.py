from pydantic import BaseModel
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from enum import Enum

# ----- BASE ----- #

class ItemBase(SQLModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[float, Field(gt=0)]
    description: str | None = None
    stock_quantity: Annotated[int, Field(ge=0)] = 0 
    
# ----- INPUT ----- #
    
# Item creation
class ItemInput(ItemBase):
    is_active: bool = False
    
# ----- OUTPUT PUBLIC ----- #
    
# This model is only used by other classes' models to display relationships.
# The actual item shown to the public is the class below.
class ItemOutputNoRelationship(ItemBase):
    id: int
    created_at: datetime
    seller_id: int

# Item shown to normal users    
from .users import UserOutput

class ItemOutput(ItemOutputNoRelationship):
    seller: UserOutput
    
# ----- OUTPUT PRIVATE ----- #

from .orders import OrderOutput
# Item shown to account owner and admins
class ItemOutputPrivate(ItemOutput):
    is_active: bool
    is_banned: bool
    is_deleted: bool
    
    orders: list[OrderOutput]
    
# ----- SEARCH ----- #

class ItemSearch(BaseModel):
    seller_id: int | None = None 
    item_id: int | None = None
    item_name: str | None = None
    
    include_banned: bool = False
    include_deleted: bool = False
    include_inactive: bool = False

# ----- SORT AND FILTER ----- #

class ItemAttrSortPrivate(str, Enum):
    item_name = "name"
    item_price = "price"
    item_stock_quantity = "stock_quantity"
    item_id = "id"
    item_created_at = "created_at"

    item_is_active = "is_active"
    item_is_deleted = "is_deleted"
    item_is_banned = "is_banned"
    
class ItemAttrSortPublic(str, Enum):
    item_name = "name"
    item_price = "price"
    item_stock_quantity = "stock_quantity"
    item_id = "id"
    item_created_at = "created_at"
    
    item_seller_id = "seller_id"
    
class ItemSortFilterBase(BaseModel):
    name: str | None = None
    id: int | None = None
    
    price_lower: float | None = None
    price_upper: float | None = None
    
    stock_quantity_lower: float | None = None
    stock_quantity_higher: float | None = None
    
    created_at_lower: datetime | None = None
    created_at_higher: datetime | None = None
    
    sorted_ascending: bool = True
    
class ItemSortFilterPublic(ItemSortFilterBase):
    sorted_by: ItemAttrSortPublic | None = None    
    
    seller_id: int | None = None
    seller_name: str | None = None
    
class ItemSortFilterPrivate(ItemSortFilterBase):
    sorted_by: ItemAttrSortPrivate | None = None
    
    is_active: bool | None = None
    is_deleted: bool | None = None
    is_banned: bool | None = None 
    
# ----- UPDATE ----- #

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
    
# ----- DATABASE ----- #
    
if TYPE_CHECKING:
    from .users import User
    from .orders import Order

# Item in database
class Item(ItemBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    seller_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    is_active: bool = False
    is_deleted: bool = False
    is_banned: bool = False
    
    seller: Annotated['User', Relationship(back_populates='items')] # The user this item belongs to
    orders: Annotated[list['Order'], Relationship(back_populates='item')] # The orders associated with this item
    