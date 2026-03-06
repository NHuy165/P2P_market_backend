from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.models_schemas.users import UserStatus

from ..core.security import create_access_token, verify_hashed
from ..exceptions.core import ExceptionAuthentication_401, ExceptionInvalidAccount_403
from ..repository.users import GetUser

# ----- Login for token ----- #


async def login_service(email: EmailStr, password: str, session: AsyncSession) -> str:
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("email", email)

    user = await get_user.get_one(session)

    # Check if email exists and password is correct.
    if user is None or not verify_hashed(password, user.hashed_password):
        raise ExceptionAuthentication_401()

    # If user is banned.
    if user.status == UserStatus.BANNED:
        raise ExceptionInvalidAccount_403("banned")

    # Credentials correct
    data = {"sub": str(user.id)}  # By convention, sub is of type string
    access_token = create_access_token(data)

    return access_token
