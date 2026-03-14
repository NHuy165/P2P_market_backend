import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.session import AsyncSession

from src.exceptions.core import ExceptionResponse
from src.models_schemas.enums import ExceptionType
from src.models_schemas.users import User
from tests.utils import response_validator_single

# ----- Transaction create ----- #


@pytest.mark.parametrize(
    "admin, action, status_code, exception_type",
    [
        (False, "deposit", 400, ExceptionType.REQUEST),
        (True, "add", 400, ExceptionType.REQUEST),
        (False, "withdraw", 409, ExceptionType.INVALID_VALUE),
        (True, "subtract", 409, ExceptionType.INVALID_VALUE),
    ],
)
async def test_change_money(
    authorized_client: AsyncClient,
    admin_client: AsyncClient,
    session: AsyncSession,
    userA: User,
    admin: bool,
    action: str,
    status_code: int,
    exception_type: ExceptionType,
):
    """
    Fails to deposit/add a negative amount as a user/admin.
    Fails to withdraw/subtract more than the current balance as a user/admin.
    """

    await session.refresh(userA)
    userA_id = userA.id

    session.expire_all()

    if action in ("deposit", "add"):
        amount = "-10"
    else:
        amount = "10"

    if admin:
        response = await admin_client.post(
            f"/admin/transactions/{userA_id}/{action}", json={"amount": amount}
        )
    else:
        response = await authorized_client.post(
            f"/transactions/{action}", json={"amount": amount}
        )

    response_validator_single(
        response, status_code, ExceptionResponse, {"exception_type": exception_type}
    )


# ----- Transaction read ----- #


# ----- Transaction update ----- #


# ----- Transaction delete ----- #
