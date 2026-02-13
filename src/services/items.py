from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from ..models.users import User
from ..models.items import Item
from ..models.schemas import ItemInput, ItemUpdate, ItemSearch, ItemFilterBase, ItemFilterPublic, ItemFilterSpecial
from ..exceptions import *

# ----- Utility ----- #

def item_filter_base(filter: ItemFilterBase) -> SelectOfScalar[Item]:
    """
    Function for filtering Items.
    """
    query = select(Item)
    
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
        
    return query

def item_filter_public(filter: ItemFilterPublic) -> SelectOfScalar[Item]:
    """
    Function for filtering Items shown to the public.
    """
    query = item_filter_base(filter)
    
    if filter.seller_id is not None:
        query = query.where(Item.seller_id == filter.seller_id)
    if filter.seller_name is not None:
        query = query.where(Item.seller.username == filter.seller_name)
        
    return query

def item_filter_special(filter: ItemFilterSpecial) -> SelectOfScalar[Item]:
    """
    Function for filtering Items shown to account owner and admins.
    """
    query = item_filter_base(filter)
    
    if filter.is_active is not None:
        query = query.where(Item.is_active == filter.is_active)
    if filter.is_deleted is not None:
        query = query.where(Item.is_deleted == filter.is_deleted)
    if filter.is_banned is not None:
        query = query.where(Item.is_banned == filter.is_banned)
        
    return query
    

def get_item_query(search: ItemSearch, query: SelectOfScalar[Item] | None = None):
    """
    Function for getting Item(s) from database. 
    Dumb and doesn't know if the query is for multiple or one object. 
    Only returns the SQL query.
    Receives a pre-passed query returned from the filter functions.
    """
    
    if query is None:
        query = select(Item)
    
    if search.user_id is not None:
        query = query.where(Item.seller_id == search.user_id)
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

def get_item_one(session: Session, search: ItemSearch) -> Item | None:
    """
    Function for getting ONE Item from database. 
    Is always passed item_id when used.
    """
    
    query = get_item_query(search)
    return session.exec(query).first()
        
def get_item_many(session: Session, 
                  search: ItemSearch,
                  filter_public: ItemFilterPublic | None = None,
                  filter_special: ItemFilterSpecial | None = None,
                  ) -> list[Item]:
    """
    Function for getting MANY Items from database. 
    Is either passed user_id or nothing at all.
    """
    
    if filter_public is not None:
        query = item_filter_public(filter_public)
    elif filter_special is not None:
        query = item_filter_special(filter_special)
    else:
        query = None
    
    query = get_item_query(search, query=query)
    
    return list(session.exec(query).all())

# ----- Item listing creation ----- #

def create_item_service(user: User, session: Session, item: ItemInput) -> Item:
    assert user.id is not None
    # Checks for overlapping names, does not check among banned and deleted items.
    search = ItemSearch(user_id=user.id, item_name=item.name, include_inactive=True)
    existing = get_item_one(session, search)
    
    if existing is not None:
        raise ExceptionTakenGeneric()
    
    listing = Item(**item.model_dump(), seller=user)
    
    session.add(listing)
    session.commit()
    session.refresh(listing)
    
    return listing

# ----- Item listing edit ----- #

def edit_item_service(user_id: int, session: Session, item_id: int, item_update: ItemUpdate) -> Item:
    # Cannot edit banned and deleted items (enforced by default by ItemSearch).
    search = ItemSearch(user_id=user_id, item_id=item_id, include_inactive=True)
    item = get_item_one(session, search)
    
    if item is None:
        raise ExceptionNotFound()
    
    # Negative relative quantity
    if item_update.stock_quantity_relative is not None and item_update.stock_quantity_relative + item.stock_quantity < 0:
        raise ExceptionNegativeValue()
    
    # Actual update code
    update_data = item_update.model_dump(exclude_unset=True)
    
    if item_update.stock_quantity_relative is not None:
        update_data["stock_quantity"] = item.stock_quantity + item_update.stock_quantity_relative

    item.sqlmodel_update(update_data)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return item

def delete_item_service(user_id: int, session: Session, item_id: int):
    # Banned and deleted items count as deleted and cannot be deleted again (enforced by default by ItemSearch).
    search = ItemSearch(user_id=user_id, item_id=item_id, include_inactive=True)
    item = get_item_one(session, search)
    
    if item is None:
        raise ExceptionNotFound()
    
    item.is_active = False
    item.is_deleted = True
    
    session.add(item)
    session.commit()
    
    # returns nothing
    
# ----- Item listing display ----- #

def get_personal_items_all_service(user_id: int, session: Session, filter: ItemFilterSpecial | None = None) -> list[Item]:
    '''
    Gets ALL items, including banned, deleted and inactive.
    '''
    search = ItemSearch(user_id=user_id, include_banned=True, include_deleted=True, include_inactive=True)
    result = get_item_many(session, search, filter_special=filter)
    
    return result

def get_personal_item_specific_service(user_id: int, session: Session, item_id: int) -> Item | None:
    '''
    Like the "get all" alternative, but only gets one item, based on id.
    '''
    search = ItemSearch(item_id=item_id, user_id=user_id, include_banned=True, include_deleted=True, include_inactive=True)
    result = get_item_one(session, search)
    
    if result is None:
        raise ExceptionNotFound()
    
    return result

def get_public_items_all_service(session: Session, filter: ItemFilterPublic | None = None) -> list[Item]:
    '''
    Public orders will only show non-banned, non-deleted and active functions.
    '''
    search = ItemSearch()
    result = get_item_many(session, search, filter_public=filter)
    
    return result

def get_public_item_specific_service(session: Session, item_id: int) -> Item | None:
    '''
    Like the "get all" alternative, but only gets one item, based on id.
    '''
    search = ItemSearch(item_id=item_id)
    result = get_item_one(session, search)
    
    if result is None:
        raise ExceptionNotFound()
    
    return result