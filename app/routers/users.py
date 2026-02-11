from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, Field
from typing import Annotated
from sqlmodel import Session
from enum import Enum

from ..database import get_session
from ..services.users import *
from ..models.schemas import UserInput, UserOutputSpecial

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
# ----- User registration ----- #

@router.post("/register", response_model=UserOutputSpecial)
def register_user(user: UserInput, session: SessionDep):
    try:
        user_output = register_user_service(user, session)
        user_output = UserOutputSpecial.model_validate(user_output)
        
        return user_output
        
    except ExceptionTakenEmail:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another account with this email already exists"
        ) 
        
    except ExceptionTakenName:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another account with this username already exists"
        )