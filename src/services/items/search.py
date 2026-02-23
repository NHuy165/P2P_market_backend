from sqlmodel.sql.expression import SelectOfScalar

from ...models_schemas.items import Item, ItemSearch

def item_search(query: SelectOfScalar[Item], search: ItemSearch) -> SelectOfScalar[Item]:
    """
    This function is dumb, it only makes a query, it doesn't know whether we're searching for one or multiple
    """
    if search.seller_id is not None:
        query = query.where(Item.seller_id == search.seller_id)
    if search.item_id is not None:
        query = query.where(Item.id == search.item_id)
    if search.item_name is not None:
        query = query.where(Item.name == search.item_name)
        
    if search.include_banned is False:
        query = query.where(Item.is_banned == False)
    if search.include_deleted is False:
        query = query.where(Item.is_deleted == False)
    if search.include_inactive is False:
        query = query.where(Item.is_active == True)
        
    return query