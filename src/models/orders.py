from pydantic import EmailStr, BaseModel
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from datetime import datetime, timezone

# ----- BASE ----- #

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    
class OrderBase(SQLModel):
    quantity: Annotated[int, Field(gt=0)]
    price_per_item: Annotated[float, Field(gt=0)] # Prevents price changes
    
# ----- INPUT ----- #
    
class OrderInput(OrderBase):
    item_id: int
    
# ----- OUTPUT PUBLIC ----- #
    
# ----- OUTPUT PRIVATE ----- #
    
from .items import ItemOutput
from .users import UserOutput

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
    
# ----- SORT AND FILTER ----- #

# ----- FILTER ----- #

# ----- UPDATE ----- #

# Buyer, seller and item cannot be changed.
class OrderUpdate(OrderBase):
    quantity: Annotated[int | None, Field(gt=0)] = None
    price_per_item: Annotated[float | None, Field(gt=0)] = None
    status: OrderStatus | None = None
    
# ----- DATABASE ----- #

if TYPE_CHECKING:
    from .items import Item
    from .users import User
    
class Order(OrderBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    
    item_id: Annotated[int | None, Field(foreign_key="item.id")] = None
    buyer_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    seller_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    status: OrderStatus

    item: Annotated['Item', Relationship(back_populates="orders")] # The item associated with this order
    buyer: Annotated['User', Relationship(back_populates="buy_orders", 
                                          sa_relationship_kwargs={"foreign_keys": "Order.buyer_id"})] # The buyer associated with this order
    seller: Annotated['User', Relationship(back_populates="sell_orders",
                                           sa_relationship_kwargs={"foreign_keys": "Order.seller_id"})] # The seller associated with this order
    
    
    