from sqlmodel.sql.expression import SelectOfScalar
from pydantic import Any

from ...models.orders import Order, OrderSortFilter

def order_sort_filter(query: SelectOfScalar[Order], sort_filter: OrderSortFilter) -> SelectOfScalar[Order]:
    if sort_filter.id is not None:
        query = query.where(Order.id == sort_filter.id)
    if sort_filter.item_id is not None:
        query = query.where(Order.item_id == sort_filter.item_id)
    if sort_filter.buyer_id is not None:
        query = query.where(Order.buyer_id == sort_filter.buyer_id)
    if sort_filter.seller_id is not None:
        query = query.where(Order.seller_id == sort_filter.seller_id)
        
    if sort_filter.status is not None:
        query = query.where(Order.status == sort_filter.status)
        
    if sort_filter.quantity_lower is not None:
        query = query.where(Order.quantity >= sort_filter.quantity_lower)
    if sort_filter.quantity_higher is not None:
        query = query.where(Order.quantity <= sort_filter.quantity_higher)
        
    if sort_filter.created_at_lower is not None:
        query = query.where(Order.created_at >= sort_filter.created_at_lower)
    if sort_filter.created_at_higher is not None:
        query = query.where(Order.created_at <= sort_filter.created_at_higher)
        
    if sort_filter.price_per_item_lower is not None:
        query = query.where(Order.price_per_item >= sort_filter.price_per_item_lower)
    if sort_filter.price_per_item_higher is not None:
        query = query.where(Order.price_per_item <= sort_filter.price_per_item_higher)
        
    if sort_filter.sorted_by is not None:
        att = getattr(Order, sort_filter.sorted_by.value)
        if sort_filter.sorted_ascending:
            query = query.order_by(att.asc())
        else:
            query = query.order_by(att.desc())
            
    return query
    
    
'''
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
    
    sorted_by: OrderAttrSort | None = None
    sorted_ascending: bool = True
'''