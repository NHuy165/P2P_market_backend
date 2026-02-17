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
    
# ----- INPUT ----- #
    
class OrderInput(OrderBase):
    item_id: int
    
# ----- OUTPUT PUBLIC ----- #

# Orders are only shown to account owner and admins

# ----- OUTPUT PRIVATE ----- #
    
from .items import ItemOutput
from .users import UserOutput

class OrderOutputNoRelationship(OrderBase):
    id: int
    
    price_per_item = float
    
    item_id: int
    buyer_id: int
    seller_id: int
    
    status: OrderStatus
    created_at: datetime


class OrderOutput(OrderOutputNoRelationship):  
    item: ItemOutput
    buyer: UserOutput
    seller: UserOutput
    
class OrderOutputWithType(OrderOutput):
    order_type: str
    
# ----- SORT AND FILTER ----- #

class OrderAttrSort(str, Enum):
    order_id = "id"
    order_item_id = "item_id"
    order_buyer_id = "buyer_id"
    order_seller_id = "seller_id"
    
    order_quantity = "quantity"
    
    order_created_at = "created_at"
    order_price_per_item = "price_per_item"
    order_status = "status"
    

class OrderSortFilter(BaseModel):
    id: int | None = None
    item_id: int | None = None
    buyer_id: int | None = None
    seller_id: int | None = None
    
    status: OrderStatus | None = None
    
    quantity_lower: int | None = None
    quantity_higher: int | None = None
    
    created_at_lower: datetime | None = None
    created_at_higher: datetime | None = None
    
    price_per_item_lower: float | None = None
    price_per_item_higher: float | None = None
    
    sell_buy: bool | None = None # True for sell orders only, False for buy orders only, None for both
    
    sorted_by: OrderAttrSort | None = None
    sorted_ascending: bool = True

# ----- FILTER ----- #

# ----- UPDATE ----- #

class OrderUpdate(OrderBase):
    quantity: Annotated[int | None, Field(gt=0)] = None
    quantity_relative: int | None = None
    
# ----- DATABASE ----- #

if TYPE_CHECKING:
    from .items import Item
    from .users import User
    from .transactions import Transaction
    
class Order(OrderBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    
    item_id: Annotated[int | None, Field(foreign_key="item.id")] = None
    buyer_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    seller_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    price_per_item: Annotated[float, Field(gt=0)] # Prevents price changes
    status: OrderStatus = OrderStatus.PENDING

    item: Annotated['Item', Relationship(back_populates="orders")]
    buyer: Annotated['User', Relationship(back_populates="buy_orders", 
                                          sa_relationship_kwargs={"foreign_keys": "Order.buyer_id"})]
    seller: Annotated['User', Relationship(back_populates="sell_orders",
                                           sa_relationship_kwargs={"foreign_keys": "Order.seller_id"})]
    transaction: Annotated['Transaction', Relationship(back_populates="order")]
    
    
    