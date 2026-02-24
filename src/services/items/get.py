from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from ...models_schemas.items import Item, ItemSearch, ItemSortFilterPublic, ItemSortFilterPrivate, ItemStatus
from .search import item_search
from .sort_filter import item_sort_filter_public, item_sort_filter_private
        
def get_items(session: Session, 
              search: ItemSearch,
              many: bool,
              sf_public: ItemSortFilterPublic | None = None,
              sf_private: ItemSortFilterPrivate | None = None,
              with_for_update: bool = False,
              ) -> Item | None | list[Item]:
    """
    Function for getting MANY Items from database. 
    Is either passed user_id or nothing at all.
    """
    
    query = select(Item).where(Item.status is not ItemStatus.DELETED) # ALWAYS searches for non-deleted items
    query = item_search(query, search)
    if sf_public is not None:
        query = item_sort_filter_public(query, sf_public)
    elif sf_private is not None:
        query = item_sort_filter_private(query, sf_private)
        
    if with_for_update:
        query = query.with_for_update()
        
    if many:
        return list(session.exec(query).all())
    else:
        return session.exec(query).first()