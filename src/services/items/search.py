from sqlmodel.sql.expression import SelectOfScalar

from ...models_schemas.items import Item, ItemSearch

def item_search(query: SelectOfScalar[Item], search: ItemSearch) -> SelectOfScalar[Item]:
    """
    This function is dumb, it only makes a query, it doesn't know whether we're searching for one or multiple
    """
    if search.seller_id is not None:
        query = query.where(Item.seller_id == search.seller_id)
    if search.id is not None:
        query = query.where(Item.id == search.id)
    if search.name is not None:
        query = query.where(Item.name == search.name)
        
    return query