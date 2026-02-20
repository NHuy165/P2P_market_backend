from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated

from ...exceptions import ExceptionAuth
from ...models.auth import TokenOutput
from ...services.auth.core import get_current_user_service, login_service
from ...database import SessionDep
from ...models.users import User

router = APIRouter()

# ----- Login for token ----- #            
        
@router.post("/token", response_model = TokenOutput,
             responses={
                 409: {"description": "Invalid login credentials."}
             })
def login(user: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):
    try:
        access_token = login_service(user.username, user.password, session)
        return TokenOutput(access_token=access_token, token_type="bearer")
    
    except ExceptionAuth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
# ----- Token verification ----- #        

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    try:
        user = get_current_user_service(token, session)
        return user
        
    except ExceptionAuth as e:
        if str(e) == "Invalid account":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="This account isn't valid",
                headers={"WWW-Authenticate": "Bearer"}
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify credentials",
                headers={"WWW-Authenticate": "Bearer"}
                )
            
UserDep = Annotated[User, Depends(get_current_user)]

def verify_admin(user: UserDep) -> None:
    if user.is_admin is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have admin privileges."
        )