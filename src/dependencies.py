from fastapi import Depends, HTTPException, status
from typing import Annotated
from sqlmodel import Session
from pydantic import BaseModel, ValidationError
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
import jwt

from .core.security import settings
from .models.users import User
from .database import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Token validator
class TokenData(BaseModel):
    sub: int # Converts str to int
    iat: datetime
    exp: datetime
    type: str

# User check dependency, can't put in auth.py since bad practice (other services will import this one)
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_session)]):
    credential_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not verify credentials",
        headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        contents = jwt.decode(token, key=settings.SECRET_KEY, algorithms=[settings.TOKEN_ENCODE_ALGORITHM])
        contents_model = TokenData(**contents)
    
    # JWT can't decode token
    except jwt.InvalidTokenError:
        raise credential_error
    
    # Token validation failed
    except ValidationError:
        raise credential_error
        
    user = session.get(User, contents_model.sub)
    
    # User data received is invalid
    if user is None:
        raise credential_error
    
    # User account is invalid
    if not user.is_active:
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="This account isn't valid",
        headers={"WWW-Authenticate": "Bearer"}
        )
        
    return user