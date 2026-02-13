from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
from sqlmodel import Session

from ..database import get_session
from ..services.users import *
from ..models.users import UserInput, UserOutputPrivate

router = APIRouter()

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
            detail="Another account with this email already exists",
            headers={"WWW-Authenticate": "Bearer"}
        ) 
        
    except ExceptionTakenUserName:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another account with this username already exists",
            headers={"WWW-Authenticate": "Bearer"}
        )