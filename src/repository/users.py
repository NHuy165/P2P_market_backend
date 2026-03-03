from sqlmodel import select

from ..exceptions.core import ExceptionRequest_400
from ..models_schemas.users import User, UserStatus
from .core import GetObject, ObjectType


class GetUser(GetObject[User]):
    def __init__(self):
        self.model_type = ObjectType.USER
        self.model = User
        self.query = select(self.model)
        super().__init__()

    # Set base type functions
    def base_active(self):
        if self.base:
            raise ExceptionRequest_400(
                f"{self.model.__name__} received new base type with existing one."
            )
        self.query = self.query.where(User.status == UserStatus.ACTIVE)
        self.base = True

    def base_existing(self):
        if self.base:
            raise ExceptionRequest_400(
                f"{self.model.__name__} received new base type with existing one."
            )
        self.query = self.query.where(User.status != UserStatus.DELETED)
        self.base = True

    def base_all(self):
        if self.base:
            raise ExceptionRequest_400(
                f"{self.model.__name__} received new base type with existing one."
            )
        self.base = True
