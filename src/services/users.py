from pydantic import EmailStr
from sqlmodel import Session, select

from ..core.security import get_hashed
from ..models.users import User, UserInput
from ..exceptions import *

# ----- User registration ----- #

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
    

    
        
    
        
    