from sqlmodel import Session, select
from pydantic import EmailStr

from src.models_schemas.exceptions import ExceptionAuthentication_401
from src.models_schemas.users import User
from ...core.security import verify_hashed, create_access_token


# ----- Login for token ----- #

def login_service(email: EmailStr, password: str, session: Session) -> str:
    check_email = select(User).where(User.email == email)
    check_email_result = session.exec(check_email).first()
    
    # Check if email exists and password is correct
    if check_email_result is None or not verify_hashed(password, check_email_result.hashed_password):
        raise ExceptionAuthentication_401()

    # Credentials correct
    data = {"sub": str(check_email_result.id)} # By convention, sub is of type string
    access_token = create_access_token(data)
    
    return access_token