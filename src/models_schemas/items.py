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

class ItemStatus(Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    DELETED = "DELETED"
    
class ItemStatusRestricted(Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    
# Item creation
class ItemInput(ItemBase):
    status: ItemStatusRestricted
    
# ----- OUTPUT PUBLIC ----- #
    
# This model is only used by other classes' models to display relationships.
# The actual item shown to the public is the class below.
class ItemOutputNoRelationship(ItemBase):
    id: int
    seller_id: int
    
    created_at: datetime
    
# Item shown to normal users    
from .users import UserOutput

class ItemOutput(ItemOutputNoRelationship):
    seller: UserOutput
    
# ----- OUTPUT PRIVATE ----- #

# Item shown to account owner and admins
from .orders import OrderOutputNoType
class ItemOutputPrivate(ItemOutput):
    status: ItemStatus
    deleted_at: datetime | None = None
    
    orders: list[OrderOutputNoType]
    
# ----- SEARCH ----- #

class ItemSearch(BaseModel):
    id: int | None = None
    name: str | None = None
    seller_id: int | None = None 

# ----- SORT AND FILTER ----- #

class ItemAttrSortPrivate(str, Enum):
    item_id = "id"
    
    item_name = "name"
    item_price = "price"
    item_stock_quantity = "stock_quantity"
    item_created_at = "created_at"

    item_status = "status"
    
class ItemAttrSortPublic(str, Enum):
    item_id = "id"
    item_name = "name"
    
    item_price = "price"
    item_stock_quantity = "stock_quantity"
    item_created_at = "created_at"
    
    item_seller_id = "seller_id"
    
class ItemSortFilterBase(BaseModel):
    price_lower: float | None = None
    price_upper: float | None = None
    
    stock_quantity_lower: float | None = None
    stock_quantity_higher: float | None = None
    
    created_at_lower: datetime | None = None
    created_at_higher: datetime | None = None
    
    sorted_ascending: bool = True
    
class ItemSortFilterPublic(ItemSortFilterBase):
    sorted_by: ItemAttrSortPublic | None = None    
    
class ItemSortFilterPrivate(ItemSortFilterBase):
    sorted_by: ItemAttrSortPrivate | None = None
    
    include_active: bool = True
    include_suspended: bool = False
    include_banned: bool = False
    
# ----- UPDATE ----- #

class ItemUpdate(ItemBase):
    name: Annotated[str | None, Field(min_length=1)] = None
    price: Annotated[float | None, Field(gt=0)] = None
    description: str | None = None
    stock_quantity: Annotated[int | None, Field(ge=0)] = None
    stock_quantity_relative: int | None = None
    
    status: ItemStatusRestricted | None = None
    # is_deleted: bool | None = None (item deletion is done via a separate request)

# ----- DATABASE ----- #
    
if TYPE_CHECKING:
    from .users import User
    from .orders import Order

# Item in database
class Item(ItemBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    seller_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None
    
    status: ItemStatus
    
    seller: "User" = Relationship(back_populates='items') # The user this item belongs to
    orders: list["Order"] = Relationship(back_populates='item') # The orders associated with this item
    