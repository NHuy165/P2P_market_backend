from datetime import datetime, timezone
from pydantic import EmailStr
from sqlmodel import Session

from ..repository.core import CompareOperator, CriterionGet
from ..repository.orders import GetOrder
from ..repository.users import GetUser
from .items import delete_items_all_service, suspend_items_all_service
from ..models_schemas.orders import OrderStatus
from ..core.security import get_hashed, verify_hashed
from ..models_schemas.users import PasswordUpdate, User, UserInput, UserStatus, UserUpdate
from ..exceptions.core import ExceptionAuthentication_401, ExceptionModifiedAdmin_403, ExceptionStatusOverlap_409, ExceptionUnfinishedOrders_409, ExceptionTakenUserEmail_409, ExceptionTakenUserName_409, ExceptionNotFound_404, ObjectType

# ----- User create ----- #

def check_name_exists(username: str, session: Session):
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("username", username)

    user = get_user.get_one(session)
    
    if user is not None:
        raise ExceptionTakenUserName_409()
        
def check_email_exists(email: EmailStr, session: Session):
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("email", email)

    user = get_user.get_one(session)
    
    if user is not None:
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

def read_user_service(session: Session, user_id: int) -> User:
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("id", user_id)

    user = get_user.get_one(session)
    
    if user is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)
    
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
    
# ----- User delete ----- #
    
def delete_user_service(user: User, session: Session, password: str) -> User:
    if not verify_hashed(password, user.hashed_password):
        raise ExceptionAuthentication_401()
    
    # Checks for existing unfinished order
    assert user.id is not None
    
    get_order = GetOrder()
    get_order.base_both(user.id)
    not_delivered = CriterionGet("status", OrderStatus.DELIVERED, CompareOperator.NE)
    get_order.apply_criterion(not_delivered)
    
    order = get_order.get_one(session)
    
    if order is not None:
        raise ExceptionUnfinishedOrders_409()
    
    # Deletion
    
    # Deletes all items
    delete_items_all_service(user, session)

    user.status = UserStatus.DELETED
    user.deleted_at = datetime.now(timezone.utc)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user

def change_user_ban_status_service(session: Session, user_id: int, ban: bool) -> User:
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("id", user_id)
    
    user = get_user.get_one(session)
    
    if user is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)
    
    if user.is_admin:
        raise ExceptionModifiedAdmin_403()
    
    if (user.status is UserStatus.BANNED and ban is True) or (user.status is not UserStatus.BANNED is False and ban is False):
        raise ExceptionStatusOverlap_409(ObjectType.USER)
    
    if user.status is UserStatus.BANNED:
        user.status = UserStatus.ACTIVE
        user.banned_at = None
        # User has to manually reactivate his items here...
        
    else:   
        user.status = UserStatus.BANNED
        user.banned_at = datetime.now(timezone.utc)
        suspend_items_all_service(user, session)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user
    
    
    
    