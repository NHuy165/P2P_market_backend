from fastapi import APIRouter, Body, status
from typing import Annotated

from ...core.dependencies import UserDep
from ...core.database import SessionDep
from ...services.users import delete_user_service, register_user_service, read_user_service, update_account_service
from ...models_schemas.users import UserInput, UserOutput, UserOutputPrivate, UserUpdate
from ...exceptions.core import *

router = APIRouter()

# ----- User create ----- #

@router.post("/register", response_model=UserOutputPrivate,
             responses={
                 409: Responses.RESPONSE_409_CONFLICT
             })
def register_user(user: UserInput, session: SessionDep):
    user_output = register_user_service(user, session)
    user_output = UserOutputPrivate.model_validate(user_output)
    
    return user_output
        
# ----- User read ----- #

@router.get("/me", response_model=UserOutputPrivate,
            responses={
                401: Responses.RESPONSE_401_UNAUTHORIZED,
                403: Responses.RESPONSE_403_FORBIDDEN,
            })
def read_my_account(user: UserDep):
    return user


@router.get("/{user_id}", response_model=UserOutput,
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND
                }) 
def read_user(session: SessionDep, user_id: int):
    result = read_user_service(session, user_id)
    return result

# ----- User update ----- #

@router.patch("/update", response_model=UserOutputPrivate,
              responses={
                  401: Responses.RESPONSE_401_UNAUTHORIZED,
                  403: Responses.RESPONSE_403_FORBIDDEN,
              })
def update_account(user: UserDep, session: SessionDep, update_info: UserUpdate):
    result = update_account_service(user, session, update_info)
    
    return result

@router.patch("/change_password", status_code=status.HTTP_204_NO_CONTENT,
              responses={
                  401: Responses.RESPONSE_401_UNAUTHORIZED,
                  403: Responses.RESPONSE_403_FORBIDDEN,
              })
def update_password(user: UserDep, session: SessionDep, update_info: UserUpdate):
    update_password(user, session, update_info)

# ----- User delete ----- #

@router.delete("/delete", response_model=UserOutputPrivate,
               responses={
                   401: Responses.RESPONSE_401_UNAUTHORIZED,
                   403: Responses.RESPONSE_403_FORBIDDEN,
                   409: Responses.RESPONSE_409_CONFLICT,
               })
def delete_user(user: UserDep, session: SessionDep, password: Annotated[str, Body(min_length=1)]):
    user_deleted = delete_user_service(user, session, password)
    return user_deleted
