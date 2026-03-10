from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated

from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

from src.models_schemas.enums import OrderStatus

if TYPE_CHECKING:
    from .items import Item, ItemOutputPublic
    from .transactions import Transaction
    from .users import User, UserOutput


# ----- BASE ----- #


class OrderBase(SQLModel):
    quantity: Annotated[int, Field(gt=0)]


# ----- INPUT ----- #


class OrderInput(OrderBase):
    item_id: int


# ----- OUTPUT PUBLIC ----- #

# Orders are only shown to account owner and admins

# ----- OUTPUT PRIVATE ----- #


class OrderOutputNoRelationship(OrderBase):
    id: int

    price_per_item: Decimal

    item_id: int
    buyer_id: int
    seller_id: int

    status: OrderStatus
    created_at: datetime
    finished_at: datetime | None  # Whether failed or delivered


class OrderOutputNoType(OrderOutputNoRelationship):
    item: "ItemOutputPublic"
    buyer: "UserOutput"
    seller: "UserOutput"


class OrderOutput(OrderOutputNoType):
    type: str


# ----- UPDATE ----- #


class OrderUpdate(OrderBase):
    quantity: Annotated[int | None, Field(gt=0)] = None
    quantity_relative: int | None = None


# ----- DATABASE ----- #


class Order(OrderBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None

    item_id: Annotated[int | None, Field(foreign_key="item.id", nullable=False)] = None
    buyer_id: Annotated[int | None, Field(foreign_key="user.id", nullable=False)] = None
    seller_id: Annotated[int | None, Field(foreign_key="user.id", nullable=False)] = (
        None
    )
    # No transaction foreign key.

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    finished_at: Annotated[
        datetime | None, Field(sa_column=Column(DateTime(timezone=True)))
    ] = None
    price_per_item: Annotated[
        Decimal, Field(sa_column=Column(Numeric(10, 2)), gt=0)
    ]  # Prevents price changes
    status: OrderStatus = OrderStatus.PENDING

    item: "Item" = Relationship(back_populates="orders")
    buyer: "User" = Relationship(
        back_populates="buy_orders",
        sa_relationship_kwargs={"foreign_keys": "Order.buyer_id"},
    )
    seller: "User" = Relationship(
        back_populates="sell_orders",
        sa_relationship_kwargs={"foreign_keys": "Order.seller_id"},
    )
    transactions: list["Transaction"] = Relationship(back_populates="order")


from .items import ItemOutputPublic
from .users import UserOutput
