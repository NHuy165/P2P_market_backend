from sqlmodel import select, Session

from .sort_filter import transaction_sort_filter
from ...models.users import User
from ...models.transactions import Transaction, TransactionSortFilter, TransactionStatus, TransactionType, TransactionInput
from ...exceptions import ExceptionNegativeValue,  ExceptionNotFound

# ----- Transaction create ----- #

def change_money(user: User, session: Session, inp: TransactionInput, trans_type: TransactionType) -> Transaction:
    """
    Function for dealing with withdrawals and deposits.
    Transactions based on orders are dealt with in orders' code.
    """
    user_reserved = session.get(User, user.id, with_for_update=True)
    if user_reserved is None:
        raise ExceptionNotFound()
    
    if trans_type.value is TransactionType.WITHDRAWAL:
        if user_reserved.balance < inp.amount:
            raise ExceptionNegativeValue()
        user_reserved.balance -= inp.amount
        
    else:
        user_reserved.balance += inp.amount
        
    trans = Transaction(
            amount=inp.amount,
            type=trans_type,
            user=user_reserved,
            status=TransactionStatus.SUCCESS
        )
    
    session.add(trans)
    session.commit()
    session.refresh(trans)
    
    return trans

# ----- Transaction read ----- #

def read_transactions_service(user: User, session: Session, sort_filter: TransactionSortFilter | None = None) -> list:
    query = select(Transaction).where(Transaction.user_id == user.id)
    
    if sort_filter is not None:
        query = transaction_sort_filter(query, sort_filter)
        
    result = session.exec(query).all()
    return list(result)
    