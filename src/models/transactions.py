from sqlmodel import Relationship, Field
from typing import Annotated, TYPE_CHECKING
from datetime import datetime, timezone

from .schemas import TransactionBase, TransactionType

if TYPE_CHECKING:
    from .users import User

class Transaction(TransactionBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    type: TransactionType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    user_id: Annotated[int | None, Field(foreign_key="user.id")] = None
    
    user: Annotated["User", Relationship(back_populates="transactions")]
    