from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from pydantic import BaseModel
from sqlmodel import Session

from ..services.auth import *
from ..database import get_session

router = APIRouter()

# Token according to OAuth2 standards
class Token(BaseModel):
    access_token: str
    token_type: str 

@router.post("/token", response_model = Token)
def login(user: Annotated[OAuth2PasswordRequestForm, Depends()], session: Annotated[Session, Depends(get_session)]):
    try:
        access_token = login_service(user.username, user.password, session)
        return Token(access_token=access_token, token_type="bearer")
    
    except Exception_Auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )