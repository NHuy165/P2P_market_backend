from fastapi import APIRouter, HTTPException, status

from src.database import SessionDep
from src.exceptions import ExceptionConflict, ExceptionForbidden, ExceptionNotFound
from src.models.users import UserOutputPrivate
from src.services.users.core import change_active_status_service, change_ban_status_service, read_account_service

router = APIRouter()

# ----- User read (ADMIN) ----- #

@router.get("/{user_id}", response_model=UserOutputPrivate,
            responses={
                404: {"description": "Couldn't find user."}
            })
def read_account_admin(session: SessionDep, user_id: int):
    try:
        result = read_account_service(session, user_id)
        return result
    
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find user",
        )
        
# ----- User update (ADMIN) ----- #

@router.patch("/{user_id}/deactivate", response_model=UserOutputPrivate,
              responses={
                  403: {"description": "Tried to modify another admin's account."},
                  404: {"description": "Couldn't find user."},
                  409: {"description": "Account deactivation failed due to account already being inactive."}
              })
def deactivate_account(session: SessionDep, user_id: int):
    try:
        user = change_active_status_service(session, user_id, activate=False)
        return user
    
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find user",
        )
        
    except ExceptionForbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another admin's account"
        )
        
    except ExceptionConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user account is already inactive.",
        )
        
@router.patch("/{user_id}/activate", response_model=UserOutputPrivate,
              responses={
                  403: {"description": "Tried to modify another admin's account."},
                  404: {"description": "Couldn't find user."},
                  409: {"description": "Account activation failed due to account already being active."}
              })
def activate_account(session: SessionDep, user_id: int):
    try:
        user = change_active_status_service(session, user_id, activate=True)
        return user
    
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find user",
        )
        
    except ExceptionForbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another admin's account"
        )
        
    except ExceptionConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user account is already active.",
        )
        
# ----- User delete (ADMIN) ----- #

@router.post("/{user_id}/ban", response_model=UserOutputPrivate,
             responses={
                 403: {"description": "Tried to modify another admin's account."},
                 404: {"description": "Couldn't find user."},
                 409: {"description": "Account ban failed due to account already being banned."}
             }
            )
def ban_account(session: SessionDep, user_id: int):
    try:
        user = change_ban_status_service(session, user_id, ban=True)
        return user
    
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find user",
        )
        
    except ExceptionForbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another admin's account"
        )
        
    except ExceptionConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user account is already banned.",
        )
        
@router.post("/{user_id}/unban", response_model=UserOutputPrivate,
             responses={
                 403: {"description": "Tried to modify another admin's account."},
                 404: {"description": "Couldn't find user."},
                 409: {"description": "Account unban failed due to account not having being banned."}
             }
            )
def unban_account(session: SessionDep, user_id: int):
    try:
        user = change_ban_status_service(session, user_id, ban=False)
        return user
    
    except ExceptionNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find user",
        )
        
    except ExceptionForbidden:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify another admin's account"
        )
        
    except ExceptionConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user account is not banned.",
        )
               
        

        
