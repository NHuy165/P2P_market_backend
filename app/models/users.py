from pydantic import EmailStr
from typing import Annotated, TYPE_CHECKING
from sqlmodel import SQLModel, Relationship, Field

if TYPE_CHECKING:
    from .items import Items

class UserBase(SQLModel):
    username: Annotated[str, Field(regex=r"^[a-zA-Z0-9_]+$")]
    email: EmailStr
    is_active: bool = True
    balance: float = 0
    
class User(UserBase, table=True):
    id: Annotated[int | None, Field(primary_key=True)] = None
    hashed_password: Annotated[str, Field(min_length=8)]
    
    items: list["Items"] = Relationship(back_populates="user")
    
class UserInput(UserBase):
    password: Annotated[str, Field(min_length=8)]
    
class UserOutput(UserBase):
    id: int
    