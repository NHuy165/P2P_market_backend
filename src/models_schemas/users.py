from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, BeforeValidator, EmailStr
from sqlmodel import Column, DateTime, Field, Numeric, Relationship, SQLModel

from src.models_schemas.enums import UserStatus
from src.models_schemas.utils import bvalidator_forbid_none

if TYPE_CHECKING:
    from .items import Item
    from .orders import Order
    from .transactions import Transaction


# ----- BASE ----- #


class UserBase(SQLModel):
    username: Annotated[str, Field(regex=r"^[a-zA-Z0-9_]+$", unique=True, min_length=1)]
    description: str | None = None


# ----- INPUT ----- #


# Account creation
class UserInput(UserBase):
    email: EmailStr
    password: Annotated[str, Field(min_length=8)]


# ----- OUTPUT PUBLIC ----- #


# User profile shown to normal users
class UserOutput(UserBase):
    id: int

    status: UserStatus

    created_at: datetime
    banned_at: datetime | None


# ----- OUTPUT PRIVATE ----- #


# User profile shown to account owner and admins
class UserOutputPrivate(UserOutput):
    email: EmailStr
    balance: Decimal


# ----- SEARCH, SORT AND FILTER ----- #


class UserGet(BaseModel):
    """
    Since User doesn't have complex sorting and filtering, we cram everything into 1 model.
    """

    id: int | None = None
    username: str | None = None
    email: EmailStr | None = None

    include_admin: bool = False
    include_active: bool = True
    include_banned: bool = False
    include_deleted: bool = False


# ----- UPDATE ----- #


# User is not allowed to explicitly set the value to None.


class UserUpdate(UserBase):
    username: Annotated[
        str | None,
        BeforeValidator(bvalidator_forbid_none),
        Field(min_length=1),
    ] = None
    email: Annotated[
        EmailStr | None, BeforeValidator(bvalidator_forbid_none), Field()
    ] = None
    description: str | None = None

    # is_deleted: bool | None = None (user deletion is done via a separate request)


class PasswordUpdate(BaseModel):
    old_password: Annotated[
        str, Field(min_length=1)
    ]  # No need to be too strict here, since we verify it anyways
    new_password: Annotated[str, Field(min_length=8)]


# ----- DATABASE ----- #


# User in database
class User(UserBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None

    email: EmailStr
    hashed_password: Annotated[str, Field(min_length=8)]
    balance: Annotated[Decimal, Field(sa_column=Column(Numeric(10, 2)))] = Decimal(
        "0.00"
    )

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

    is_admin: bool = False
    status: UserStatus = UserStatus.ACTIVE

    items: list["Item"] = Relationship(back_populates="seller")  # Items in stock
    buy_orders: list["Order"] = Relationship(
        back_populates="buyer",
        sa_relationship_kwargs={"foreign_keys": "Order.buyer_id"},
    )
    sell_orders: list["Order"] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={"foreign_keys": "Order.seller_id"},
    )
    transactions: list["Transaction"] = Relationship(back_populates="user")
