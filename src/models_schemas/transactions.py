from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated

from sqlmodel import Column, Field, Numeric, Relationship, SQLModel

if TYPE_CHECKING:
    from .orders import Order
    from .users import User


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
    amount: Annotated[Decimal, Field(sa_column=Column(Numeric(10, 2)), gt=0)]


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


# ----- UPDATE ----- #

# ----- DATABASE ----- #


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
