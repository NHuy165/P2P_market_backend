from pydantic import EmailStr, BaseModel
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from datetime import datetime, timezone

# ----- BASE ----- #

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    SALE = "SALE"
    PURCHASE = "PURCHASE"

class TransactionBase(SQLModel):
    amount: Annotated[float, Field(gt=0)]
    
# ----- INPUT ----- #
    
class TransactionInput(TransactionBase):
    pass
    
# ----- OUTPUT PUBLIC ----- #
    
# ----- OUTPUT PRIVATE ----- #
    
# Transaction history are only shown to account owner and admins
class TransactionOutput(TransactionBase):
    id: int
    type: TransactionType
    user_id: int
    created_at: datetime
    
# ----- SORT AND FILTER ----- #

# ----- FILTER ----- #

# ----- UPDATE ----- #
    
# ----- DATABASE ----- #

if TYPE_CHECKING:
    from .users import User

class Transaction(TransactionBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    type: TransactionType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    user_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    
    user: Annotated["User", Relationship(back_populates="transactions")]
    