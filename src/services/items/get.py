from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from ...models.items import Item, ItemSearch, ItemSortFilterPublic, ItemSortFilterPrivate
from .search import item_search
from .sort_filter import item_sort_filter_public, item_sort_filter_private

def get_item_one(session: Session, search: ItemSearch, with_for_update: bool = False) -> Item | None:
    """
    Function for getting ONE Item from database. 
    Is always passed item_id when used.
    """
    
    query = select(Item)
    query = item_search(query, search)
    
    if with_for_update:
        query = query.with_for_update()
    
    return session.exec(query).first()
        
def get_items_many(session: Session, 
                  search: ItemSearch,
                  filter_public: ItemSortFilterPublic | None = None,
                  filter_private: ItemSortFilterPrivate | None = None,
                  with_for_update: bool = False,
                  ) -> list[Item]:
    """
    Function for getting MANY Items from database. 
    Is either passed user_id or nothing at all.
    """
    
    query = select(Item)
    query = item_search(query, search)
    if filter_public is not None:
        query = item_sort_filter_public(query, filter_public)
    elif filter_private is not None:
        query = item_sort_filter_private(query, filter_private)
        
    if with_for_update:
        query = query.with_for_update()
    
    return list(session.exec(query).all())