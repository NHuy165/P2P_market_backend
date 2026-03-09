from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated

from pydantic import BeforeValidator
from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

from src.exceptions.core import ExceptionRequest_400
from src.models_schemas.utils import (
    bvalidator_forbid_none,
)

if TYPE_CHECKING:
    from .orders import Order, OrderOutputNoType
    from .users import User, UserOutput


class ItemStatus(Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    DELETED = "DELETED"


def bvalidator_limit_item_status(status: ItemStatus):
    if status == ItemStatus.BANNED or status == ItemStatus.DELETED:
        raise ExceptionRequest_400("Can only set item to ACTIVE or SUSPENDED.")
    return status


# ----- BASE ----- #


class ItemBase(SQLModel):
    name: Annotated[str, Field(min_length=1)]
    price: Annotated[Decimal, Field(sa_column=Column(Numeric(10, 2)), gt=0)]
    description: str | None = None
    stock_quantity: Annotated[int, Field(ge=0)]


# ----- INPUT ----- #


# Item creation
class ItemInput(ItemBase):
    status: Annotated[ItemStatus, BeforeValidator(bvalidator_limit_item_status)]


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
    name: Annotated[
        str | None, BeforeValidator(bvalidator_forbid_none), Field(min_length=1)
    ] = None
    price: Annotated[
        Decimal | None, BeforeValidator(bvalidator_forbid_none), Field(gt=0)
    ] = None
    description: str | None = None
    stock_quantity: Annotated[
        int | None, BeforeValidator(bvalidator_forbid_none), Field(ge=0)
    ] = None
    stock_quantity_relative: Annotated[
        int | None, BeforeValidator(bvalidator_forbid_none)
    ] = None

    status: Annotated[
        ItemStatus | None,
        BeforeValidator(bvalidator_limit_item_status, bvalidator_forbid_none),
    ] = None


# ----- DATABASE ----- #


# Item in database
class Item(ItemBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    seller_id: Annotated[int | None, Field(foreign_key="user.id")] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    deleted_at: Annotated[
        datetime | None, Field(sa_column=Column(DateTime(timezone=True)))
    ] = None
    banned_at: Annotated[
        datetime | None, Field(sa_column=Column(DateTime(timezone=True)))
    ] = None

    status: ItemStatus

    seller: "User" = Relationship(
        back_populates="items"
    )  # The user this item belongs to
    orders: list["Order"] = Relationship(
        back_populates="item"
    )  # The orders associated with this item


from .orders import OrderOutputNoType
from .users import UserOutput
