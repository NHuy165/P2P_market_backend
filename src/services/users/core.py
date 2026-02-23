from pydantic import EmailStr
from sqlmodel import Session, or_, select

from src.services.items.core import delete_items_all_service

from ...models_schemas.orders import Order, OrderStatus
from ...core.security import get_hashed, verify_hashed
from ...models_schemas.users import PasswordUpdate, User, UserInput, UserUpdate
from ...models_schemas.exceptions import ExceptionActivationStatus_409, ExceptionAuthentication_401, ExceptionBanStatus_409, ExceptionModifiedAdmin_403, ExceptionPendingOrders_409, ExceptionTakenUserEmail_409, ExceptionTakenUserName_409, ExceptionUserNotFound_404

# ----- User create ----- #

def check_name_exists(username: str, session: Session):
    check = select(User).where(User.username == username)
    result = session.exec(check).first()
    
    if result is not None:
        raise ExceptionTakenUserName_409()
        
def check_email_exists(email: EmailStr, session: Session):
    check = select(User).where(User.email == email)
    result = session.exec(check).first()
    
    if result is not None:
        raise ExceptionTakenUserEmail_409()

def register_user_service(user: UserInput, session: Session) -> User:
    check_name_exists(user.username, session)
    check_email_exists(user.email, session)
    
    user_data = user.model_dump(exclude={"password"})
    hashed_pass = get_hashed(user.password)
    userDB = User(**user_data, hashed_password = hashed_pass)
    
    session.add(userDB)
    session.commit()
    session.refresh(userDB)

    return userDB

# ----- User read ----- #

def read_account_service(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    
    if user is None:
        raise ExceptionUserNotFound_404(user_id)
    
    return user

# ----- User update ----- #

def update_account_service(user: User, session: Session, update_info: UserUpdate) -> User:
    user.sqlmodel_update(update_info.model_dump())
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user
    
def update_password_service(user: User, session: Session, update_info: PasswordUpdate) -> None:
    if not verify_hashed(update_info.old_password, user.hashed_password):
        raise ExceptionAuthentication_401()
    
    new_pass = get_hashed(update_info.new_password)
    user.sqlmodel_update({"hashed_password": new_pass})
    
    session.add(user)
    session.commit()
    
    # returns nothing
    
def change_active_status_service(session: Session, user_id: int, activate: bool) -> User:
    user = session.get(User, user_id)
    
    if user is None:
        raise ExceptionUserNotFound_404(user_id)
    
    if user.is_admin:
        raise ExceptionModifiedAdmin_403()
    
    if (user.is_active is True and activate is True) or (user.is_active is False and activate is False):
        raise ExceptionActivationStatus_409(activated=user.is_active)
    
    if activate:
        user.is_active = True
    else:
        user.is_active = False
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user
    
# ----- User delete ----- #
    
def delete_user_service(user: User, session: Session, password: str) -> User:
    if not verify_hashed(password, user.hashed_password):
        raise ExceptionAuthentication_401()
    
    query = select(Order).where(or_(Order.seller_id == user.id, Order.buyer_id == user.id), Order.status == OrderStatus.PENDING)
    result = session.exec(query).first()
    
    # Pending orders exist
    if result is not None:
        raise ExceptionPendingOrders_409()
    
    delete_items_all_service(user, session)
    
    user.is_active = False
    user.is_deleted = True
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user

def change_ban_status_service(session: Session, user_id: int, ban: bool) -> User:
    user = session.get(User, user_id)
    
    if user is None:
        raise ExceptionUserNotFound_404(user_id)
    
    if user.is_admin:
        raise ExceptionModifiedAdmin_403()
    
    if (user.is_banned is True and ban is True) or (user.is_banned is False and ban is False):
        raise ExceptionBanStatus_409(banned=user.is_banned)
    
    if user.is_banned:
        user.is_banned = False
    else:   
        user.is_active = False
        user.is_banned = True
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user
    
    
    
    