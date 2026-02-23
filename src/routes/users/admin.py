from fastapi import APIRouter, HTTPException, status

from src.core.database import SessionDep
from src.models_schemas.exceptions import ExceptionModifiedAdmin_403, Responses
from src.models_schemas.users import UserOutputPrivate
from src.services.users.core import change_active_status_service, change_ban_status_service, read_account_service

router = APIRouter()

# ----- User read (ADMIN) ----- #

@router.get("/{user_id}", response_model=UserOutputPrivate,
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def read_account_admin(session: SessionDep, user_id: int):
    result = read_account_service(session, user_id)
    return result
    
        
# ----- User update (ADMIN) ----- #

@router.patch("/{user_id}/deactivate", response_model=UserOutputPrivate,
              responses={
                  404: Responses.RESPONSE_404_NOT_FOUND,
                  409: Responses.RESPONSE_409_CONFLICT
              })
def deactivate_account(session: SessionDep, user_id: int):
    user = change_active_status_service(session, user_id, activate=False)
    return user
        
@router.patch("/{user_id}/activate", response_model=UserOutputPrivate,
              responses={
                  404: Responses.RESPONSE_404_NOT_FOUND,
                  409: Responses.RESPONSE_409_CONFLICT
              })
def activate_account(session: SessionDep, user_id: int):
    user = change_active_status_service(session, user_id, activate=True)
    return user
        
# ----- User delete (ADMIN) ----- #

@router.post("/{user_id}/ban", response_model=UserOutputPrivate,
             responses={
                 404: Responses.RESPONSE_404_NOT_FOUND,
                 409: Responses.RESPONSE_409_CONFLICT
             }
            )
def ban_account(session: SessionDep, user_id: int):
    user = change_ban_status_service(session, user_id, ban=True)
    return user
        
@router.post("/{user_id}/unban", response_model=UserOutputPrivate,
             responses={
                 404: Responses.RESPONSE_404_NOT_FOUND,
                 409: Responses.RESPONSE_409_CONFLICT
             }
            )
def unban_account(session: SessionDep, user_id: int):
    user = change_ban_status_service(session, user_id, ban=False)
    return user
        

        
