from datetime import datetime, timezone

from sqlmodel import Session

from src.services.users.get import get_user_service

from ...models_schemas.exceptions import ExceptionInvalidValue_409, ExceptionStatusOverlap_409, ExceptionTakenItemName_409, ExceptionNotFound_404, ObjectType
from ...models_schemas.users import User, UserGet
from ...models_schemas.items import Item, ItemInput, ItemStatus, ItemUpdate, ItemSearch, ItemSortFilterPublic, ItemSortFilterPrivate
from .get import get_items, get_items

# ----- Item create ----- #

def create_item_service(user: User, session: Session, item: ItemInput) -> Item:
    assert user.id is not None
    # Checks for overlapping names, does not check among banned and deleted items.
    search = ItemSearch(seller_id=user.id, name=item.name)
    sort_filter = ItemSortFilterPrivate(include_suspended=True, include_banned=True)
    existing = get_items(session, False, search=search, sf_private=sort_filter)
    
    if existing is not None:
        raise ExceptionTakenItemName_409()
    
    listing = Item(**item.model_dump(), seller=user)
    
    session.add(listing)
    session.commit()
    session.refresh(listing)
    
    return listing

# ----- Item read ----- #

def read_private_items_many_service(user: User, session: Session, search: ItemSearch, sort_filter: ItemSortFilterPrivate | None = None) -> list[Item]:
    search.seller_id = user.id # Just in case, but this is usually enforced by the front end.
    result = get_items(session, many=True, search=search, sf_private=sort_filter)
    return result # type: ignore

def read_private_items_many_admin_service(session: Session, user_id: int, search: ItemSearch, sort_filter: ItemSortFilterPrivate | None = None) -> list[Item]:
    user_get = UserGet(id=user_id,
                       include_banned=True,
                       include_deleted=True)
    user = get_user_service(session, user_get)
    
    if user is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)

    return read_private_items_many_service(user, session, search, sort_filter=sort_filter)

def read_private_item_one_service(user: User, session: Session, item_id: int) -> Item | None:
    search = ItemSearch(id=item_id, seller_id=user.id) # Used by normal user to make sure the item belongs to them.
        
    sort_filter = ItemSortFilterPrivate(include_banned=True, include_suspended=True)
    result = get_items(session, many=False, search=search, sf_private=sort_filter)
    
    if result is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)
    
    return result # type: ignore

def read_private_item_one_admin_service(session: Session, item_id: int) -> Item | None:
    """
    This entire function is not much different from the normal function. It exists just for clarity's sake.
    """
    search = ItemSearch(id=item_id) # The only difference
        
    sort_filter = ItemSortFilterPrivate(include_banned=True, include_suspended=True)
    result = get_items(session, many=False, search=search, sf_private=sort_filter)
    
    if result is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)
    
    return result # type: ignore

def read_public_items_many_service(session: Session, search: ItemSearch, sort_filter: ItemSortFilterPublic | None = None) -> list[Item]:
    '''
    Public reading will only show active items.
    '''
    result = get_items(session, many=True, search=search, sf_public=sort_filter)
    
    return result # type: ignore

def read_public_item_one_service(session: Session, item_id: int) -> Item | None:
    '''
    Like the "get all" alternative, but only gets one item, based on id.
    '''
    search = ItemSearch(id=item_id)
    sort_filter = ItemSortFilterPublic() # Enforces active items only by default
    result = get_items(session, many=False, search=search, sf_public=sort_filter)
    
    if result is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)
    
    return result # type: ignore

# ----- Item update ----- #

def update_item_service(user: User, session: Session, item_id: int, item_update: ItemUpdate) -> Item:
    # Cannot edit banned and deleted items.
    search = ItemSearch(seller_id=user.id, id=item_id)
    sort_filter = ItemSortFilterPrivate(include_suspended=True)
    item = get_items(session, many=False, search=search, sf_private=sort_filter, with_for_update=True)
    
    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)
    assert isinstance(item, Item)
    
    # Negative relative quantity
    if item_update.stock_quantity_relative is not None and item_update.stock_quantity_relative + item.stock_quantity < 0:
        raise ExceptionInvalidValue_409("Item stock quantity", item_update.stock_quantity_relative + item.stock_quantity)
    
    # Activate/suspend overlap
    if item_update.status == item.status:
        raise ExceptionStatusOverlap_409(ObjectType.ITEM)
    
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
    sort_filter = ItemSortFilterPrivate(include_banned=True)
    items = get_items(session, many=True, search=search, sf_private=sort_filter, with_for_update=True) # with_for_update for reasons similar to above
    assert isinstance(items, list)
    
    for item in items:
        item.status = ItemStatus.SUSPENDED
        
    session.add_all(items)
    session.commit()
    
    for item in items:
        session.refresh(item)
    
    return items

# ----- Item delete ----- #

def delete_item_service(user: User, session: Session, item_id: int) -> Item:
    # Banned and deleted items count as deleted and cannot be deleted again.
    search = ItemSearch(seller_id=user.id, id=item_id)
    sort_filter = ItemSortFilterPrivate(include_suspended=True, include_banned=True)
    item = get_items(session, many=False, search=search, sf_private=sort_filter, with_for_update=True)
    
    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)
    assert isinstance(item, Item)
    
    # Soft delete so pending orders still have to get delivered.
    item.status = ItemStatus.DELETED
    item.deleted_at = datetime.now(timezone.utc)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return item

def delete_items_all_service(user: User, session: Session) -> list[Item]:
    """
    This function is automatically called upon user deletion.
    """
    search = ItemSearch(seller_id=user.id)
    sort_filter = ItemSortFilterPrivate(include_suspended=True, include_banned=True)
    items = get_items(session, many=True, search=search, sf_private=sort_filter, with_for_update=True) # with_for_update for reasons similar to above
    assert isinstance(items, list)
    
    for item in items:
        item.status = ItemStatus.DELETED
        item.deleted_at = datetime.now(timezone.utc)
        
    session.add_all(items)
    session.commit()
    
    for item in items:
        session.refresh(item)
    
    return items

def change_item_ban_status_service(session: Session, item_id: int, ban: bool) -> Item:
    search = ItemSearch(id=item_id)
    sort_filter = ItemSortFilterPrivate(include_banned=True)
    item = get_items(session, many=False, search=search, sf_private=sort_filter, with_for_update=True)
    assert not isinstance(item, list)
    
    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, item_id)
    
    if (item.status is ItemStatus.BANNED and ban is True) or (item.status is not ItemStatus.BANNED and ban is False):
        raise ExceptionStatusOverlap_409(ObjectType.ITEM)
    
    if item.status is ItemStatus.BANNED:
        item.status = ItemStatus.SUSPENDED
        item.banned_at = None
    else:
        item.status = ItemStatus.BANNED
        item.banned_at = datetime.now(timezone.utc)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return item
