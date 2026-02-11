from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .schemas import OrderBase, OrderStatus
from datetime import datetime, timezone

if TYPE_CHECKING:
    from .items import Item
    from .users import User
    
class Order(OrderBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    
    item_id: Annotated[int | None, Field(foreign_key="item.id")] = None
    buyer_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    seller_id: Annotated[int | None, Field(foreign_key="user.id")] = None

    item: Annotated['Item', Relationship(back_populates="orders")] # The item associated with this order
    buyer: Annotated['User', Relationship(back_populates="buy_orders", 
                                          sa_relationship_kwargs={"foreign_keys": "Order.buyer_id"})] # The buyer associated with this order
    seller: Annotated['User', Relationship(back_populates="sell_orders",
                                           sa_relationship_kwargs={"foreign_keys": "Order.seller_id"})] # The seller associated with this order
    
    status: OrderStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    