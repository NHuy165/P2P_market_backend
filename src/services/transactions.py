from sqlmodel import select, Session

from ..models.users import User
from ..models.transactions import Transaction, TransactionType, TransactionInput
from ..exceptions import *

# ----- Balance operations ----- #

def change_money(inp: TransactionInput, user: User, trans_type: TransactionType, session: Session) -> Transaction:
    # Prevents multiple requests at the same time
    user_reserved = session.get(User, user.id, with_for_update=True)
    assert user_reserved is not None
    
    if trans_type.value in (TransactionType.WITHDRAWAL, TransactionType.PURCHASE):
        if user_reserved.balance < inp.amount:
            raise ExceptionNegativeValue()
        user_reserved.balance -= inp.amount
        
    else:
        user_reserved.balance += inp.amount
        
    trans = Transaction(
            amount=inp.amount,
            type=trans_type,
            user=user_reserved
        )
    
    session.add(trans)
    session.commit()
    session.refresh(trans)
    
    return trans

# ----- Display transactions history ----- #

def read_transactions_service(user: User, session: Session) -> list:
    query = select(Transaction).where(Transaction.user_id == user.id)
    result = session.exec(query).all()
    
    return list(result)
    