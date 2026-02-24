from sqlmodel import Session, select

from ...models_schemas.users import User, UserGet, UserStatus


def get_user_service(session: Session, user_get: UserGet, with_for_update: bool = False) -> User | None:
    query = select(User)
    
    # Search
    if user_get.id is not None:
        query = query.where(User.id == user_get.id)
    if user_get.username is not None:
        query = query.where(User.username == user_get.username)
    if user_get.email is not None:
        query = query.where(User.email == user_get.email)
    
    # Filter
    if user_get.include_active is False:
        query = query.where(User.status is not UserStatus.ACTIVE)
    if user_get.include_banned is False:
        query = query.where(User.status is not UserStatus.BANNED)
    if user_get.include_deleted is False:
        query = query.where(User.status is not UserStatus.DELETED)
    if user_get.include_admin is False:
        query = query.where(User.is_admin == False)
        
    if with_for_update:
        query = query.with_for_update()
        
    return session.exec(query).first()
        