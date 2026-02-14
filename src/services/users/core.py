from pydantic import EmailStr
from sqlmodel import Session, select

from ...core.security import get_hashed, verify_hashed
from ...models.users import PasswordUpdate, User, UserInput, UserUpdate
from ...exceptions import *

# ----- User create ----- #

def check_name_exists(username: str, session: Session):
    check = select(User).where(User.username == username)
    result = session.exec(check).first()
    
    if result is not None:
        raise ExceptionTakenUserName()
        
def check_email_exists(email: EmailStr, session: Session):
    check = select(User).where(User.email == email)
    result = session.exec(check).first()
    
    if result is not None:
        raise ExceptionTakenUserEmail()

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

def read_account_service(session: Session, search_id: int) -> User:
    user = session.get(User, search_id)
    
    if user is None:
        raise ExceptionNotFound()
    
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
        raise ExceptionAuth()
    
    new_pass = get_hashed(update_info.new_password)
    user.sqlmodel_update({"hashed_password": new_pass})
    
    session.add(user)
    session.commit()
    
    # returns nothing
    
# ----- User delete ----- #
    
def delete_user_service(user: User, session: Session, password) -> None:
    if not verify_hashed(password, user.hashed_password):
        raise ExceptionAuth()
    
    session.delete(user)
    session.commit()
    