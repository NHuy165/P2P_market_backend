from sqlmodel import Session, select

from ..models.users import User
from ..models.items import Item
from ..models.schemas import ItemInput, ItemUpdate
from ..exceptions import *

def get_item_query(user_id: int | None = None, 
                   item_id: int | None = None,
                   item_name: str | None = None, 
                   include_banned: bool = False,
                   include_deleted: bool = False,
                   include_inactive: bool = True,
                   ):
    
    query = select(Item)
    
    if user_id is not None:
        query = query.where(Item.seller_id == user_id)
    if item_id is not None:
        query = query.where(Item.id == item_id)
    if item_name is not None:
        query = query.where(Item.name == item_name)
        
    if include_banned is False:
        query = query.where(Item.is_banned == False)
        
    if include_deleted is False:
        query = query.where(Item.is_deleted == False)
        
    if include_inactive is False:
        query = query.where(Item.is_active == True)
        
    return query

def get_item_one(session: Session,
                 user_id: int | None = None, 
                 item_id: int | None = None,
                 item_name: str | None = None, 
                 include_banned: bool = False,
                 include_deleted: bool = False,
                 include_inactive: bool = True,
                 ):
    query = get_item_query(
        user_id=user_id,
        item_id=item_id,
        item_name=item_name,
        include_banned=include_banned,
        include_deleted=include_deleted,
        include_inactive=include_inactive
    )
    return session.exec(query).first()
        
def get_item_many(session: Session,
                 user_id: int | None = None, 
                 item_id: int | None = None,
                 item_name: str | None = None, 
                 include_banned: bool = False,
                 include_deleted: bool = False,
                 include_inactive: bool = True,
                 ):
    query = get_item_query(
        user_id=user_id,
        item_id=item_id,
        item_name=item_name,
        include_banned=include_banned,
        include_deleted=include_deleted,
        include_inactive=include_inactive
    )
    return session.exec(query).all()

# ----- Item listing creation ----- #

def create_item_service(user: User, session: Session, item: ItemInput) -> Item:
    assert user.id is not None
    existing = get_item_one(session, user_id = user.id, item_name = item.name)
    
    if existing is not None:
        raise ExceptionTakenGeneric()
    
    listing = Item(**item.model_dump(), user=user)
    
    session.add(listing)
    session.commit()
    session.refresh(listing)
    
    return listing

# ----- Item listing edit ----- #

def edit_item_service(user: User, session: Session, item_id: int, item_update: ItemUpdate) -> Item:
    assert user.id is not None
    item = get_item_one(session, user_id = user.id, item_id = item_id)
    
    if item is None:
        raise ExceptionNotFound()
    
    # Negative relative quantity
    if item_update.stock_quantity_relative is not None and item_update.stock_quantity_relative + item.stock_quantity < 0:
        raise ExceptionNegativeValue()
    
    # Actual update code        
    if item_update.stock_quantity_relative is not None:
        item_update.stock_quantity = item.stock_quantity + item_update.stock_quantity_relative

    update_data = item_update.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_data)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    return item

def delete_item_service(user: User, session: Session, item_id: int):
    assert user.id is not None
    item = get_item_one(session, user_id = user.id, item_id = item_id)
    
    if item is None:
        raise ExceptionNotFound()
    
    item.is_active = False
    item.is_deleted = True
    
    session.add(item)
    session.commit()
    
    # returns nothing
    
# ----- Item listing display ----- #

def get_personal_items_service(user: User, session: Session) -> list[Item]:
    result = get_item_many(session, user_id=user.id, include_banned=True, include_deleted=True, include_inactive=True)
    
    return list(result)

def get_public_items_service(session: Session) -> list[Item]:
    result = get_item_many(session, include_inactive=False)
    
    return list(result)