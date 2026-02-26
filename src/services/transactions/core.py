from datetime import datetime, timezone

from sqlmodel import select, Session

from src.services.users.get import get_user_service

from ...models_schemas.exceptions import ExceptionInvalidValue_409, ExceptionNotFound_404, ObjectType
from .sort_filter import transaction_sort_filter
from ...models_schemas.users import User, UserGet
from ...models_schemas.transactions import Transaction, TransactionSearchSortFilter, TransactionStatus, TransactionType, TransactionInput

# ----- Transaction create ----- #

def change_money(user: User, session: Session, inp: TransactionInput, trans_type: TransactionType) -> Transaction:
    """
    Function for dealing with withdrawals and deposits.
    Transactions based on orders are dealt with in orders' code.
    """
    user_get = UserGet(id=user.id)
    user_reserved = get_user_service(session, user_get, with_for_update=True)
    if user_reserved is None:
        assert user.id is not None
        raise ExceptionNotFound_404(ObjectType.USER, user.id)
    
    if trans_type.value is TransactionType.WITHDRAWAL:
        if user_reserved.balance < inp.amount:
            raise ExceptionInvalidValue_409("Account balance", user_reserved.balance - inp.amount)
        user_reserved.balance -= inp.amount
        
    else:
        user_reserved.balance += inp.amount
        
    trans = Transaction(
            amount=inp.amount,
            type=trans_type,
            user=user_reserved,
            status=TransactionStatus.SUCCESS,
            finished_at=datetime.now(timezone.utc)
        )
    
    session.add(trans)
    session.add(user_reserved)
    session.commit()
    session.refresh(trans)
    
    return trans

def change_money_admin(session: Session, user_id: int, inp: TransactionInput, trans_type: TransactionType) -> Transaction:
    user_get = UserGet(id=user_id)
    user_reserved = get_user_service(session, user_get, with_for_update=True)
    if user_reserved is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)
    
    if trans_type.value is TransactionType.ADMIN_SUBTRACT:
        if user_reserved.balance < inp.amount:
            raise ExceptionInvalidValue_409("Account balance", user_reserved.balance - inp.amount)
        user_reserved.balance -= inp.amount
        
    else:
        user_reserved.balance += inp.amount
        
    trans = Transaction(
        amount=inp.amount,
        type=trans_type,
        user=user_reserved,
        status=TransactionStatus.SUCCESS,
        finished_at=datetime.now(timezone.utc)
    )
    
    session.add(trans)
    session.add(user_reserved)
    session.commit()
    session.refresh(trans)
    
    return trans

# ----- Transaction read ----- #

def read_transactions_service(user: User, session: Session, sort_filter: TransactionSearchSortFilter | None = None) -> list[Transaction]:
    query = select(Transaction).where(Transaction.user_id == user.id)
    
    if sort_filter is None:
        sort_filter = TransactionSearchSortFilter()
    query = transaction_sort_filter(query, sort_filter)
        
    result = session.exec(query).all()
    return list(result)

def read_transactions_admin_service(session: Session, user_id: int, sort_filter: TransactionSearchSortFilter) -> list[Transaction]:
    user_get = UserGet(id=user_id, include_banned=True)
    user = get_user_service(session, user_get)
    
    if user is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)
        
    return read_transactions_service(user, session, sort_filter)
    