from pydantic import BaseModel
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

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
    
# ----- OUTPUT ----- #
    
# Item shown to normal users
class ItemOutput(ItemBase):
    id: int
    seller_id: int
    
from .users import UserOutput
    
class ItemOutputWithSeller(ItemOutput):
    seller: UserOutput
    
# ----- OUTPUT SPECIAL ----- #
    
# Item shown to account owner and admins
class ItemOutputSpecial(ItemOutputWithSeller):
    is_active: bool
    is_banned: bool
    is_deleted: bool
    
# ----- SEARCH ----- #

class ItemSearch(BaseModel):
    user_id: int | None = None 
    item_id: int | None = None
    item_name: str | None = None
    
    include_banned: bool = False
    include_deleted: bool = False
    include_inactive: bool = False


# ----- FILTER ----- #

class ItemFilterBase(BaseModel):
    name: str | None = None
    
    price_lower: float | None = None
    price_upper: float | None = None
    
    stock_quantity_lower: float | None = None
    stock_quantity_higher: float | None = None
    
class ItemFilterPublic(ItemFilterBase):
    seller_id: int | None = None
    seller_name: str | None = None
    
class ItemFilterSpecial(ItemFilterBase):
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
    
    is_active: bool = False
    is_deleted: bool = False
    is_banned: bool = False
    
    seller: Annotated['User', Relationship(back_populates='items')] # The user this item belongs to
    orders: Annotated[list['Order'], Relationship(back_populates='item')] # The orders associated with this item
    