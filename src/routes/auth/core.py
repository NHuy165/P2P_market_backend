from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated

from src.services.auth import login_service
from ...exceptions.core import Responses, ExceptionAuthentication_401
from ...models_schemas.auth import TokenOutput
from ...core.database import SessionDep

router = APIRouter()

# ----- Login for token ----- #            
        
@router.post("/token", response_model = TokenOutput,
             responses={
                 401: Responses.RESPONSE_401_UNAUTHORIZED
             })
def login(user: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    access_token = login_service(user.username, user.password, session)
    return TokenOutput(access_token=access_token, token_type="bearer")
        
     

