from pydantic import EmailStr
from sqlmodel import Session, select
from fastapi import HTTPException, status

from ..models.schemas import UserLogin
from ..models.users import User
from ..core.security import verify_hashed, create_access_token



def login(user: UserLogin, session: Session):
    check_email = select(User).where(User.email == user.email)
    check_email_result = session.exec(check_email).first()
    
    # Check if email exists
    if check_email_result is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    # Check if password is correct
    if not verify_hashed(user.password, check_email_result.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    # Correct
    data = {"sub": check_email_result.username}