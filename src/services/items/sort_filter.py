from sqlmodel.sql.expression import SelectOfScalar

from ...models.items import Item, ItemSortFilterBase, ItemSortFilterPrivate, ItemSortFilterPublic

def item_filter_base(query: SelectOfScalar[Item], filter: ItemSortFilterBase) -> SelectOfScalar[Item]:
    if filter.name is not None:
        query = query.where(Item.name == filter.name)
        
    if filter.price_lower is not None:
        query = query.where(Item.price >= filter.price_lower)
    if filter.price_upper is not None:
        query = query.where(Item.price <= filter.price_upper)
        
    if filter.stock_quantity_lower is not None:
        query = query.where(Item.stock_quantity >= filter.stock_quantity_lower)
    if filter.stock_quantity_higher is not None:
        query = query.where(Item.stock_quantity <= filter.stock_quantity_higher)
        
    if filter.created_at_lower is not None:
        query = query.where(Item.created_at >= filter.created_at_lower)
    if filter.created_at_higher is not None:
        query = query.where(Item.created_at <= filter.created_at_higher)
        
    if filter.sorted_by is not None:
        att = getattr(Item, filter.sorted_by.value)
        if filter.sorted_ascending:
            query = query.order_by(att.asc())
        else:
            query = query.order_by(att.desc())
        
    return query

def item_filter_public(query: SelectOfScalar[Item], filter: ItemSortFilterPublic) -> SelectOfScalar[Item]:
    query = item_filter_base(query, filter)
    
    if filter.seller_id is not None:
        query = query.where(Item.seller_id == filter.seller_id)
    if filter.seller_name is not None:
        query = query.where(Item.seller.username == filter.seller_name)
        
    return query

def item_filter_private(query: SelectOfScalar[Item], filter: ItemSortFilterPrivate) -> SelectOfScalar[Item]:
    query = item_filter_base(query, filter)
    
    if filter.is_active is not None:
        query = query.where(Item.is_active == filter.is_active)
    if filter.is_deleted is not None:
        query = query.where(Item.is_deleted == filter.is_deleted)
    if filter.is_banned is not None:
        query = query.where(Item.is_banned == filter.is_banned)
        
    return query
    

