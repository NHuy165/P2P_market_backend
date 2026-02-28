from sqlmodel import Session
from pydantic import EmailStr

from ..exceptions.core import ExceptionAuthentication_401
from ..repository.users import GetUser
from ..core.security import verify_hashed, create_access_token


# ----- Login for token ----- #

def login_service(email: EmailStr, password: str, session: Session) -> str:
    get_user = GetUser()
    get_user.base_active()
    get_user.get_by("email", email)
    
    check_email = get_user.get_one(session)
    
    # Check if email exists and password is correct
    if check_email is None or not verify_hashed(password, check_email.hashed_password):
        raise ExceptionAuthentication_401()

    # Credentials correct
    data = {"sub": str(check_email.id)} # By convention, sub is of type string
    access_token = create_access_token(data)
    
    return access_token