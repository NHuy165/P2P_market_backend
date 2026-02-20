import jwt
from sqlmodel import Session, select
from pydantic import EmailStr, ValidationError

from ...models.auth import TokenInput
from ...models.users import User
from ...core.security import verify_hashed, create_access_token
from ...exceptions import ExceptionAuth
from ...core.config import settings

# ----- Login for token ----- #

def login_service(email: EmailStr, password: str, session: Session) -> str:
    check_email = select(User).where(User.email == email)
    check_email_result = session.exec(check_email).first()
    
    # Check if email exists and password is correct
    if check_email_result is None or not verify_hashed(password, check_email_result.hashed_password):
        raise ExceptionAuth()

    # Credentials correct
    data = {"sub": str(check_email_result.id)} # By convention, sub is of type string
    access_token = create_access_token(data)
    
    return access_token

# ----- Token verification ----- #

# User check dependency, can't put in auth.py since bad practice (other services will import this one)
def get_current_user_service(token: str, session: Session) -> User:
    # Checks if the token actually works
    try:
        contents = jwt.decode(token, key=settings.SECRET_KEY, algorithms=[settings.TOKEN_ENCODE_ALGORITHM])
        contents_model = TokenInput.model_validate(contents)
    
    # JWT can't decode token
    except jwt.InvalidTokenError:
        raise ExceptionAuth()
    
    # Token validation failed
    except ValidationError:
        raise ExceptionAuth()
        
    # Checks if the user is legit
    user = session.get(User, contents_model.sub)
    
    # User data received is invalid
    if user is None:
        raise ExceptionAuth()
    
    # User account is invalid
    if not user.is_active or user.is_banned or user.is_deleted:
        raise ExceptionAuth("Invalid account")
        
    return user