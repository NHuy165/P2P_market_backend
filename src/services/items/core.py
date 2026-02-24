from sqlmodel import Session

from ...models_schemas.exceptions import ExceptionInvalidValue_409, ExceptionItemNotFound_404, ExceptionTakenItemName_409
from ...models_schemas.users import User
from ...models_schemas.items import Item, ItemInput, ItemStatus, ItemUpdate, ItemSearch, ItemSortFilterPublic, ItemSortFilterPrivate
from .get import get_items, get_items

# ----- Item create ----- #

def create_item_service(user: User, session: Session, item: ItemInput) -> Item:
    assert user.id is not None
    # Checks for overlapping names, does not check among banned and deleted items.
    search = ItemSearch(seller_id=user.id, name=item.name)
    sort_filter = ItemSortFilterPrivate(include_suspended=True, include_banned=True)
    existing = get_items(session, search, many=False, sf_private=sort_filter)
    
    if existing is not None:
        raise ExceptionTakenItemName_409()
    
    listing = Item(**item.model_dump(), seller=user)
    
    session.add(listing)
    session.commit()
    session.refresh(listing)
    
    return listing

# ----- Item read ----- #

def read_private_items_all_service(user: User, session: Session) -> list[Item]:
    search = ItemSearch(seller_id=user.id)
    sort_filter = ItemSortFilterPrivate(include_banned=True, include_suspended=True)
    result = get_items(session, search, many=True, sf_private=sort_filter)
    return result # type: ignore

def read_private_items_with_sf_service(user: User, session: Session, sort_filter: ItemSortFilterPrivate | None = None) -> list[Item]:
    search = ItemSearch(seller_id=user.id)
    result = get_items(session, search, many=True, sf_private=sort_filter)
    return result # type: ignore

def read_private_item_one_service(user: User, session: Session, item_id: int) -> Item | None:
    search = ItemSearch(id=item_id, seller_id=user.id)
    sort_filter = ItemSortFilterPrivate(include_banned=True, include_suspended=True)
    result = get_items(session, search, many=False, sf_private=sort_filter)
    
    if result is None:
        raise ExceptionItemNotFound_404(item_id)
    
    return result # type: ignore

def read_public_items_all_service(session: Session) -> list[Item]:
    '''
    Public reading will only show active items.
    '''
    search = ItemSearch()
    sort_filter = ItemSortFilterPublic() # Enforces active items only by default
    result = get_items(session, search, many=True, sf_public=sort_filter)
    
    return result # type: ignore

def read_public_items_with_sf_service(session: Session, sort_filter: ItemSortFilterPublic | None = None) -> list[Item]:
    '''
    Public reading will only show active items.
    '''
    search = ItemSearch()
    result = get_items(session, search, many=True, sf_public=sort_filter)
    
    return result # type: ignore

def read_public_item_one_service(session: Session, item_id: int) -> Item | None:
    '''
    Like the "get all" alternative, but only gets one item, based on id.
    '''
    search = ItemSearch(id=item_id)
    sort_filter = ItemSortFilterPublic() # Enforces active items only by default
    result = get_items(session, search, many=False, sf_public=sort_filter)
    
    if result is None:
        raise ExceptionItemNotFound_404(item_id)
    
    return result # type: ignore

# ----- Item update ----- #

def update_item_service(user: User, session: Session, item_id: int, item_update: ItemUpdate) -> Item:
    # Cannot edit banned and deleted items.
    search = ItemSearch(seller_id=user.id, id=item_id)
    sort_filter = ItemSortFilterPrivate(include_suspended=True)
    item = get_items(session, search, many=False, sf_private=sort_filter, with_for_update=True)
    
    if item is None:
        raise ExceptionItemNotFound_404(item_id)
    assert isinstance(item, Item)
    
    # Negative relative quantity
    if item_update.stock_quantity_relative is not None and item_update.stock_quantity_relative + item.stock_quantity < 0:
        raise ExceptionInvalidValue_409("Item stock quantity", item_update.stock_quantity_relative + item.stock_quantity)
    
    # Actual update code
    update_data = item_update.model_dump(exclude_unset=True)
    
    if item_update.stock_quantity_relative is not None:
        update_data["stock_quantity"] = item.stock_quantity + item_update.stock_quantity_relative

    item.sqlmodel_update(update_data)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return item

# Used for when you want to delete your account
def suspend_items_all_service(user: User, session: Session) -> list[Item]:
    search = ItemSearch(seller_id=user.id)
    sort_filter = ItemSortFilterPrivate(include_suspended=True, include_banned=True)
    items = get_items(session, search, many=True, sf_private=sort_filter, with_for_update=True) # with_for_update for reasons similar to above
    assert isinstance(items, list)
    
    for item in items:
        item.status = ItemStatus.SUSPENDED
        
    session.add_all(items)
    session.commit()
    
    for item in items:
        session.refresh(item)
    
    return items

def restore_item_service(user: User, session: Session, item_id: int) -> Item:
    search = ItemSearch(seller_id=user.id, id=item_id)
    sort_filter = ItemSortFilterPrivate(include_suspended=True, include_active=False)
    item = get_items(session, search, many=False, sf_private=sort_filter, with_for_update=True) # with_for_update just in case, but is probably unnecessary since these items don't get interacted with anyways.
    
    if item is None:
        raise ExceptionItemNotFound_404(item_id)
    assert isinstance(item, Item)
    
    item.status = ItemStatus.ACTIVE
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return item

# ----- Item delete ----- #

def delete_item_service(user: User, session: Session, item_id: int) -> Item:
    # Banned and deleted items count as deleted and cannot be deleted again.
    search = ItemSearch(seller_id=user.id, id=item_id)
    sort_filter = ItemSortFilterPrivate(include_suspended=True, include_banned=True)
    item = get_items(session, search, many=False, sf_private=sort_filter, with_for_update=True)
    
    if item is None:
        raise ExceptionItemNotFound_404(item_id)
    assert isinstance(item, Item)
    
    # Soft delete so pending orders still have to get delivered.
    item.status = ItemStatus.DELETED
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return item
