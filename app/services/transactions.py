from sqlmodel import select, Session

from ..models.users import User
from ..models.schemas import TransactionType
from ..models.transactions import Transaction

# ----- Balance operations ----- #

class ExceptionNegativeBalance(Exception):
    pass

def change_money(amount: float, current_user: User, trans_type: TransactionType, session: Session) -> User:
    # Prevents multiple requests at the same time
    user = session.get(User, current_user.id, with_for_update=True)
    assert user is not None
    
    if trans_type.value in ("WITHDRAWAL", "PURCHASE"):
        if user.balance < amount:
            raise ExceptionNegativeBalance()
        user.balance -= amount
        
    else:
        user.balance += amount
        
    trans = Transaction(
            amount=amount,
            type=trans_type,
            user=user
        )
    
    session.add(trans)
    session.commit()
    session.refresh(user)
    
    return user

# ----- Display transactions history ----- #

def display_history_service(user_id: int, session: Session) -> list:
    query = select(Transaction).where(Transaction.user_id == user_id)
    result = session.exec(query).all()
    
    return list(result)
    