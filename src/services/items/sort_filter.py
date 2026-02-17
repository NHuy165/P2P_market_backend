from sqlmodel.sql.expression import SelectOfScalar

from ...models.items import Item, ItemSortFilterBase, ItemSortFilterPrivate, ItemSortFilterPublic

def item_sort_filter_base(query: SelectOfScalar[Item], sort_filter: ItemSortFilterBase) -> SelectOfScalar[Item]:
    if sort_filter.name is not None:
        query = query.where(Item.name == sort_filter.name)
    if sort_filter.id is not None:
        query = query.where(Item.id == sort_filter.id)
        
    if sort_filter.price_lower is not None:
        query = query.where(Item.price >= sort_filter.price_lower)
    if sort_filter.price_upper is not None:
        query = query.where(Item.price <= sort_filter.price_upper)
        
    if sort_filter.stock_quantity_lower is not None:
        query = query.where(Item.stock_quantity >= sort_filter.stock_quantity_lower)
    if sort_filter.stock_quantity_higher is not None:
        query = query.where(Item.stock_quantity <= sort_filter.stock_quantity_higher)
        
    if sort_filter.created_at_lower is not None:
        query = query.where(Item.created_at >= sort_filter.created_at_lower)
    if sort_filter.created_at_higher is not None:
        query = query.where(Item.created_at <= sort_filter.created_at_higher)
        
    
        
    return query

def item_sort_filter_public(query: SelectOfScalar[Item], sort_filter: ItemSortFilterPublic) -> SelectOfScalar[Item]:
    query = item_sort_filter_base(query, sort_filter)
    
    if sort_filter.sorted_by is not None:
        att = getattr(Item, sort_filter.sorted_by.value)
        if sort_filter.sorted_ascending:
            query = query.order_by(att.asc())
        else:
            query = query.order_by(att.desc())
    
    if sort_filter.seller_id is not None:
        query = query.where(Item.seller_id == sort_filter.seller_id)
    if sort_filter.seller_name is not None:
        query = query.where(Item.seller.username == sort_filter.seller_name)
        
    return query

def item_sort_filter_private(query: SelectOfScalar[Item], sort_filter: ItemSortFilterPrivate) -> SelectOfScalar[Item]:
    query = item_sort_filter_base(query, sort_filter)
    
    if sort_filter.sorted_by is not None:
        att = getattr(Item, sort_filter.sorted_by.value)
        if sort_filter.sorted_ascending:
            query = query.order_by(att.asc())
        else:
            query = query.order_by(att.desc())
            
    if sort_filter.is_active is not None:
        query = query.where(Item.is_active == sort_filter.is_active)
    if sort_filter.is_deleted is not None:
        query = query.where(Item.is_deleted == sort_filter.is_deleted)
    if sort_filter.is_banned is not None:
        query = query.where(Item.is_banned == sort_filter.is_banned)
        
    return query
    

