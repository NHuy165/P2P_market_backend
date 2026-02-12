from sqlmodel import select, Session

from ..models.users import User
from ..models.schemas import TransactionType, TransactionInput
from ..models.transactions import Transaction
from ..exceptions import *

# ----- Balance operations ----- #

def change_money(inp: TransactionInput, current_user: User, trans_type: TransactionType, session: Session) -> Transaction:
    # Prevents multiple requests at the same time
    user = session.get(User, current_user.id, with_for_update=True)
    assert user is not None
    
    if trans_type.value in (TransactionType.WITHDRAWAL, TransactionType.PURCHASE):
        if user.balance < inp.amount:
            raise ExceptionNegativeValue()
        user.balance -= inp.amount
        
    else:
        user.balance += inp.amount
        
    trans = Transaction(
            amount=inp.amount,
            type=trans_type,
            user=user
        )
    
    session.add(trans)
    session.commit()
    session.refresh(trans)
    
    return trans

# ----- Display transactions history ----- #

def display_history_service(user_id: int, session: Session) -> list:
    query = select(Transaction).where(Transaction.user_id == user_id)
    result = session.exec(query).all()
    
    return list(result)
    