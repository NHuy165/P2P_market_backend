from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions.core import (
    ExceptionInvalidValue_409,
    ExceptionNotFound_404,
    ObjectType,
)
from ..models_schemas.transactions import (
    Transaction,
    TransactionInput,
    TransactionStatus,
    TransactionType,
)
from ..models_schemas.users import User
from ..repository.core import CriterionInput
from ..repository.transactions import GetTransaction
from ..repository.users import GetUser

# ----- Transaction create ----- #


async def change_money(
    user: User,
    session: AsyncSession,
    inp: TransactionInput,
    trans_type: TransactionType,
) -> Transaction:
    """
    Function for dealing with withdrawals and deposits.
    Transactions based on orders are dealt with in orders' code.
    """

    get_user = GetUser()
    get_user.base_active()
    get_user.get_by("id", user.id)

    user_wfu = await get_user.get_one(session, with_for_update=True)
    if user_wfu is None:
        assert user.id is not None
        raise ExceptionNotFound_404(ObjectType.USER, user.id)

    if trans_type.value is TransactionType.WITHDRAWAL:
        if user_wfu.balance < inp.amount:
            raise ExceptionInvalidValue_409(
                "Account balance", user_wfu.balance - inp.amount
            )
        user_wfu.balance -= inp.amount

    else:
        user_wfu.balance += inp.amount

    trans = Transaction(
        amount=inp.amount,
        type=trans_type,
        user=user_wfu,
        status=TransactionStatus.SUCCESS,
        finished_at=datetime.now(timezone.utc),
    )

    session.add(trans)
    session.add(user_wfu)
    await session.commit()
    await session.refresh(trans, attribute_names=["user", "order"])

    return trans


async def change_money_admin(
    session: AsyncSession,
    user_id: int,
    inp: TransactionInput,
    trans_type: TransactionType,
) -> Transaction:
    get_user = GetUser()
    get_user.base_active()
    get_user.get_by("id", user_id)

    user_wfu = await get_user.get_one(session, with_for_update=True)

    if user_wfu is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)

    if trans_type.value is TransactionType.ADMIN_SUBTRACT:
        if user_wfu.balance < inp.amount:
            raise ExceptionInvalidValue_409(
                "Account balance", user_wfu.balance - inp.amount
            )
        user_wfu.balance -= inp.amount

    else:  # if trans_type.value is TransactionType.ADMIN_ADD
        user_wfu.balance += inp.amount

    trans = Transaction(
        amount=inp.amount,
        type=trans_type,
        user=user_wfu,
        status=TransactionStatus.SUCCESS,
        finished_at=datetime.now(timezone.utc),
    )

    session.add(trans)
    session.add(user_wfu)
    await session.commit()
    await session.refresh(trans, attribute_names=["user", "order"])

    return trans


# ----- Transaction read ----- #


async def read_transactions_service(
    user: User, session: AsyncSession, criteria: list[CriterionInput] = []
) -> list[Transaction]:
    get_transaction = GetTransaction()
    get_transaction.base_normal()
    get_transaction.get_by("user_id", user.id)

    transactions = await get_transaction.get_many(
        session, criteria=criteria, with_for_update=True
    )

    return transactions


async def read_transactions_admin_service(
    session: AsyncSession, user_id: int, criteria: list[CriterionInput] = []
) -> list[Transaction]:
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("id", user_id)

    user = await get_user.get_one(session)

    if user is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)

    return await read_transactions_service(user, session, criteria)
