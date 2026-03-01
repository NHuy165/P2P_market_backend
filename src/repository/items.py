from sqlmodel import select

from ..exceptions.core import ExceptionRequest_400
from ..models_schemas.items import Item, ItemStatus
from .core import Criterion, CriterionInput, GetObject, ObjectType


class GetItem(GetObject[Item]):
    def __init__(self):
        self.model_type = ObjectType.ITEM
        self.model = Item
        self.query = select(self.model)
        super().__init__()
        
    # Set base type functions
    def base_public(self):
        if self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} received new base type with existing one.")
        self.query = self.query.where(Item.status == ItemStatus.ACTIVE)
        self.base = True
        
    def base_private(self):
        if self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} received new base type with existing one.")
        self.query = self.query.where(Item.status != ItemStatus.DELETED)
        self.base = True
        
    def base_admin(self):
        if self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} received new base type with existing one.")
        self.base = True
        
    def base_custom(self, criteria: list[Criterion] | list[CriterionInput] | None = None):
        if self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} received new base type with existing one.")
        self.base = True
        
        if criteria is not None:
            for crit in criteria:
                self.apply_criterion(crit)
            
        
            