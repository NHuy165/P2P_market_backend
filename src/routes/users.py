from fastapi import APIRouter, Body, Depends, status, HTTPException
from typing import Annotated
from sqlmodel import Session

from ..database import get_session
from ..services.users.core import delete_user_service, register_user_service, read_account_service, update_account_service
from ..models.users import User, UserInput, UserOutput, UserOutputPrivate, UserUpdate
from ..dependencies import get_current_user
from ..exceptions import *

router = APIRouter()

UserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[Session, Depends(get_session)]

# ----- User create ----- #

@router.post("/register", response_model=UserOutputPrivate)
def register_user(user: UserInput, session: SessionDep):
    try:
        user_output = register_user_service(user, session)
        user_output = UserOutputPrivate.model_validate(user_output)
        
        return user_output
        
    except ExceptionTakenUserEmail:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another account with this email already exists"
        ) 
        
    except ExceptionTakenUserName:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another account with this username already exists"
        )
        
# ----- User read ----- #

@router.get("/{user_id}", response_model=UserOutputPrivate|UserOutput) # Specific model HAS to be placed first to avoid accidental type casting
def read_account(user: UserDep, session: SessionDep, user_id: int):
    if user_id == user.id:
        result = UserOutputPrivate.model_validate(user)
        return result
    try:
        result = read_account_service(session, user_id)
        result = UserOutput.model_validate(result)
        return result
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find user",
        )
    
# ----- User update ----- #

@router.patch("/update", response_model=UserOutputPrivate)
def update_account(user: UserDep, session: SessionDep, update_info: UserUpdate):
    result = update_account_service(user, session, update_info)
    
    return result

@router.patch("/change_password", status_code=status.HTTP_204_NO_CONTENT)
def update_password(user: UserDep, session: SessionDep, update_info: UserUpdate):
    try:
        update_password(user, session, update_info)
        
    except ExceptionAuth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"}
        )

# ----- User delete ----- #

@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user: UserDep, session: SessionDep, password: Annotated[str, Body(min_length=1)]):
    try:
        delete_user_service(user, session, password)
        
    except ExceptionAuth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"}
        )