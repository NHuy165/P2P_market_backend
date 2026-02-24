from sqlmodel.sql.expression import SelectOfScalar

from ...models_schemas.items import Item, ItemSortFilterBase, ItemSortFilterPrivate, ItemSortFilterPublic, ItemStatus

def item_sort_filter_base(query: SelectOfScalar[Item], sort_filter: ItemSortFilterBase) -> SelectOfScalar[Item]:
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
        
    # Public query will ONLY return active items.
    query = query.where(Item.status is ItemStatus.ACTIVE)
        
    return query

def item_sort_filter_private(query: SelectOfScalar[Item], sort_filter: ItemSortFilterPrivate) -> SelectOfScalar[Item]:
    query = item_sort_filter_base(query, sort_filter)
    
    if sort_filter.include_active is False:
        query = query.where(Item.status is not ItemStatus.ACTIVE)
    if sort_filter.include_suspended is False:
        query = query.where(Item.status is not ItemStatus.SUSPENDED)
    if sort_filter.include_banned is False:
        query = query.where(Item.status is not ItemStatus.BANNED)

    if sort_filter.sorted_by is not None:
        att = getattr(Item, sort_filter.sorted_by.value)
        if sort_filter.sorted_ascending:
            query = query.order_by(att.asc())
        else:
            query = query.order_by(att.desc())
        
    return query
    

