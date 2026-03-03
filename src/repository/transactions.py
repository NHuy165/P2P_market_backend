from sqlmodel import select

from ..exceptions.core import ExceptionRequest_400
from ..models_schemas.transactions import Transaction
from .core import GetObject, ObjectType


class GetTransaction(GetObject[Transaction]):
    def __init__(self):
        self.model_type = ObjectType.TRANSACTION
        self.model = Transaction
        self.query = select(self.model)
        super().__init__()

    # Set base type functions
    def base_normal(self):
        if self.base:
            raise ExceptionRequest_400(
                f"{self.model.__name__} received new base type with existing one."
            )
        self.base = True
