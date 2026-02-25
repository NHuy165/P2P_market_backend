from fastapi import APIRouter

from src.core.database import SessionDep
from src.models_schemas.exceptions import Responses
from src.models_schemas.users import UserOutputPrivate
from src.services.users.core import change_user_ban_status_service, read_user_service

router = APIRouter()

# ----- User read (ADMIN) ----- #

@router.get("/{user_id}", response_model=UserOutputPrivate,
            responses={
                404: Responses.RESPONSE_404_NOT_FOUND
            })
def read_account_admin(session: SessionDep, user_id: int):
    result = read_user_service(session, user_id)
    return result
        
# ----- User delete (ADMIN) ----- #

@router.delete("/{user_id}", response_model=UserOutputPrivate,
             responses={
                 404: Responses.RESPONSE_404_NOT_FOUND,
                 409: Responses.RESPONSE_409_CONFLICT
             }
            )
def ban_account(session: SessionDep, user_id: int):
    user = change_user_ban_status_service(session, user_id, ban=True)
    return user
        
@router.post("/{user_id}", response_model=UserOutputPrivate,
             responses={
                 404: Responses.RESPONSE_404_NOT_FOUND,
                 409: Responses.RESPONSE_409_CONFLICT
             }
            )
def unban_account(session: SessionDep, user_id: int):
    user = change_user_ban_status_service(session, user_id, ban=False)
    return user
        

        
