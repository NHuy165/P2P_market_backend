from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar

from ...models.users import User
from ...models.items import Item, ItemInput, ItemUpdate, ItemSearch, ItemSortFilterPublic, ItemSortFilterPrivate
from ...exceptions import ExceptionNegativeValue, ExceptionNotFound, ExceptionTakenGeneric
from .get import get_item_one, get_item_many

# ----- Item create ----- #

def create_item_service(user: User, session: Session, item: ItemInput) -> Item:
    assert user.id is not None
    # Checks for overlapping names, does not check among banned and deleted items.
    search = ItemSearch(seller_id=user.id, item_name=item.name, include_inactive=True)
    existing = get_item_one(session, search)
    
    if existing is not None:
        raise ExceptionTakenGeneric()
    
    listing = Item(**item.model_dump(), seller=user)
    
    session.add(listing)
    session.commit()
    session.refresh(listing)
    
    return listing

# ----- Item read ----- #

def get_personal_item_many_service(user: User, session: Session, sort_filter: ItemSortFilterPrivate | None = None) -> list[Item]:
    '''
    Gets ALL items, including banned, deleted and inactive.
    '''
    search = ItemSearch(seller_id=user.id, include_banned=True, include_deleted=True, include_inactive=True)
    result = get_item_many(session, search, filter_private=sort_filter)
    
    return result

def get_public_item_many_service(session: Session, sort_filter: ItemSortFilterPublic | None = None) -> list[Item]:
    '''
    Public orders will only show non-banned, non-deleted and active functions.
    '''
    search = ItemSearch()
    result = get_item_many(session, search, filter_public=sort_filter)
    
    return result

def get_personal_item_one_service(user: User, session: Session, item_id: int) -> Item | None:
    '''
    Like the "get all" alternative, but only gets one item, based on id.
    '''
    search = ItemSearch(item_id=item_id, seller_id=user.id, include_banned=True, include_deleted=True, include_inactive=True)
    result = get_item_one(session, search)
    
    if result is None:
        raise ExceptionNotFound()
    
    return result

def get_public_item_one_service(session: Session, item_id: int) -> Item | None:
    '''
    Like the "get all" alternative, but only gets one item, based on id.
    '''
    search = ItemSearch(item_id=item_id)
    result = get_item_one(session, search)
    
    if result is None:
        raise ExceptionNotFound()
    
    return result

# ----- Item update ----- #

def edit_item_service(user: User, session: Session, item_id: int, item_update: ItemUpdate) -> Item:
    # Cannot edit banned and deleted items (enforced by default by ItemSearch).
    search = ItemSearch(seller_id=user.id, item_id=item_id, include_inactive=True)
    item = get_item_one(session, search, with_for_update=True)
    
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


# ----- Item delete ----- #

def delete_item_service(user: User, session: Session, item_id: int):
    # Banned and deleted items count as deleted and cannot be deleted again (enforced by default by ItemSearch).
    search = ItemSearch(seller_id=user.id, item_id=item_id, include_inactive=True)
    item = get_item_one(session, search, with_for_update=True) # with_for_update used because this depends on banned and deleted status
    
    if item is None:
        raise ExceptionNotFound()
    
    item.is_active = False
    item.is_deleted = True
    
    session.add(item)
    session.commit()
    
    # returns nothing
    
