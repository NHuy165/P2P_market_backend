from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel
from sqlmodel import Column, Field, Numeric, Relationship, SQLModel

if TYPE_CHECKING:
    from .orders import Order, OrderOutputNoType
    from .users import User, UserOutput


class ItemStatus(Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    DELETED = "DELETED"


class ItemStatusRestricted(Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


# ----- BASE ----- #


class ItemBase(SQLModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[Decimal, Field(sa_column=Column(Numeric(10, 2)), gt=0)]
    description: str | None = None
    stock_quantity: Annotated[int, Field(ge=0)] = 0


# ----- INPUT ----- #


# Item creation
class ItemInput(ItemBase):
    status: ItemStatusRestricted


# ----- OUTPUT PUBLIC ----- #


# This model is only used by other classes' models to display relationships.
# The actual item shown to the public is the class below.
class ItemOutputNoSeller(ItemBase):
    id: int
    seller_id: int

    created_at: datetime


# Item shown to normal users
class ItemOutputPublic(ItemOutputNoSeller):
    seller: "UserOutput"


# ----- OUTPUT PRIVATE ----- #


# Item shown to account owner and admins
class ItemOutputPrivate(ItemOutputPublic):
    status: ItemStatus
    banned_at: datetime | None


class ItemOutputPrivateFull(ItemOutputPrivate):
    orders: list["OrderOutputNoType"]


# ----- UPDATE ----- #


class ItemUpdate(ItemBase):
    name: Annotated[str | None, Field(min_length=1)] = None
    price: Annotated[Decimal | None, Field(gt=0)] = None
    description: str | None = None
    stock_quantity: Annotated[int | None, Field(ge=0)] = None
    stock_quantity_relative: int | None = None

    status: ItemStatusRestricted | None = None
    # is_deleted: bool | None = None (item deletion is done via a separate request)


# ----- DATABASE ----- #


# Item in database
class Item(ItemBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    seller_id: Annotated[int | None, Field(foreign_key="user.id")] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: datetime | None = None
    banned_at: datetime | None = None

    status: ItemStatus

    seller: "User" = Relationship(
        back_populates="items"
    )  # The user this item belongs to
    orders: list["Order"] = Relationship(
        back_populates="item"
    )  # The orders associated with this item
