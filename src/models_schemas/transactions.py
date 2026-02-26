from pydantic import EmailStr, BaseModel
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum
from datetime import datetime, timezone

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    SALE = "SALE"
    PURCHASE = "PURCHASE"
    REFUND = "REFUND"
    ADMIN_ADD = "ADMIN_ADD"
    ADMIN_SUBTRACT = "ADMIN_SUBTRACT"
    
class TransactionStatus(str, Enum):
    ON_HOLD = "ON_HOLD"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    
    
# ----- BASE ----- #

class TransactionBase(SQLModel):
    amount: Annotated[float, Field(gt=0)]
    
# ----- INPUT ----- #

# This input is only used for withdraw and deposit transactions.
# Since order-related transactions are created manually in orders' code.
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
    finished_at: datetime | None
    status: TransactionStatus
    
# ----- SORT AND FILTER ----- #

class TransactionAttrSort(str, Enum):
    transaction_id = "id"
    transaction_order_id = "order_id"
    transaction_user_id = "user_id"
    
    transaction_type = "type"
    transaction_status = "status"
    
    transaction_created_at = "created_at"
    transaction_finished_at = "finished_at"
    transaction_amount = "amount"
    

class TransactionSearchSortFilter(BaseModel):
    id: int | None = None
    order_id: int | None = None
    user_id: int | None = None
    
    type: TransactionType | None = None
    status: TransactionStatus | None = None
    
    amount_lower: float | None = None
    amount_higher: float | None = None 
    
    created_at_lower: datetime | None = None
    created_at_higher: datetime | None = None
    
    finished_at_lower: datetime | None = None
    finished_at_higher: datetime | None = None
    
    include_deposit: bool = True
    include_withdrawal: bool = True
    include_sale: bool = True
    include_purchase: bool = True
    include_refund: bool = True
    include_admin_add: bool = True
    include_admin_subtract: bool = True
    
    include_on_hold: bool = True
    include_success: bool = True
    include_failed: bool = True
    
    sorted_by: TransactionAttrSort = TransactionAttrSort.transaction_id
    sorted_ascending: bool = True

# ----- FILTER ----- #

# ----- UPDATE ----- #
    
# ----- DATABASE ----- #

if TYPE_CHECKING:
    from .users import User
    from .orders import Order

class Transaction(TransactionBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    
    order_id: Annotated[int | None, Field(foreign_key="order.id", unique=True)] = None
    user_id: Annotated[int | None, Field(foreign_key="user.id", nullable=False)] = None
    
    type: TransactionType
    status: TransactionStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    
    user: "User" = Relationship(back_populates="transactions")
    order: "Order | None" = Relationship(back_populates="transactions")
    