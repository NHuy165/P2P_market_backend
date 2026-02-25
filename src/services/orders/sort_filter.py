from sqlmodel import col
from sqlmodel.sql.expression import SelectOfScalar

from ...models_schemas.orders import Order, OrderSearchSortFilter, OrderStatus

def order_sort_filter(query: SelectOfScalar[Order], sort_filter: OrderSearchSortFilter) -> SelectOfScalar[Order]:
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
        
    if sort_filter.include_pending is False:
        query = query.where(Order.status is not OrderStatus.PENDING)
    if sort_filter.include_cancelled is False:
        query = query.where(Order.status is not OrderStatus.CANCELLED)
    if sort_filter.include_shipped is False:
        query = query.where(Order.status is not OrderStatus.SHIPPED)
    if sort_filter.include_delivered is False:
        query = query.where(Order.status is not OrderStatus.DELIVERED)
        
    att = getattr(Order, sort_filter.sorted_by.value)
    if sort_filter.sorted_ascending:
        query = query.order_by(col(att).asc())
    else:
        query = query.order_by(col(att).desc())
            
            
    return query