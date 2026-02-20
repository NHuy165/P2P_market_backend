from fastapi import APIRouter, Body, Depends, status, HTTPException
from typing import Annotated

from ...database import SessionDep
from ..auth.core import UserDep
from ...services.users.core import delete_user_service, register_user_service, read_account_service, update_account_service
from ...models.users import UserInput, UserOutput, UserOutputPrivate, UserUpdate
from ...exceptions import *

router = APIRouter()

# ----- User create ----- #

@router.post("/register", response_model=UserOutputPrivate,
             responses={
                 409: {"description": "Registration failed due to overlapping name or email"}
             })
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

@router.get("/{user_id}", response_model=UserOutputPrivate|UserOutput, # Specific model HAS to be placed first to avoid accidental type casting
            responses= {
                404: {"description": "Couldn't find user."}
                }) 
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

@router.patch("/change_password", status_code=status.HTTP_204_NO_CONTENT,
              responses={
                  401: {"description": "Incorrect password."}
              })
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

@router.delete("/delete", response_model=UserOutputPrivate,
               responses={
                   401: {"description": "Incorrect password."},
                   409: {"description": "Account deletion failed due to existing pending orders."}
               })
def delete_user(user: UserDep, session: SessionDep, password: Annotated[str, Body(min_length=1)]):
    try:
        user_deleted = delete_user_service(user, session, password)
        return user_deleted
        
    except ExceptionAuth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    except ExceptionConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There are still pending orders for your items."
        )