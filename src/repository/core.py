from enum import Enum
from typing import Any, get_type_hints, Generic, TypeVar
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlmodel.sql.expression import SelectOfScalar
from sqlmodel import Session, col

from ..exceptions.core import ExceptionInvalidField_400, ExceptionRequest_400, ExceptionSortContradiction_400, ExceptionType_400

# ----- Criterion classes ----- #
class CompareOperator(str, Enum):
    EQ = "eq"
    NE = "ne"
    
    GT = "gt"
    GE = "ge"
    
    LT = "lt"
    LE = "le"
    
class ObjectType(str, Enum):
    ITEM = "Item"
    ORDER = "Order"
    USER = "User"
    TRANSACTION = "Transaction"
    
class Criterion():
    """
    Criteria are used for dynamic sorting and searching.
    """
    def __init__(self, field: str):
        self.field = field
        
class CriterionGet(Criterion):
    def __init__(self, field: str, value: Any, op: CompareOperator = CompareOperator.EQ):
        super().__init__(field)
        
        self.value = value
        self.op = op
        
class CriterionSort(Criterion):
    def __init__(self, field: str, ascending: bool = True):
        super().__init__(field)

        self.ascending = ascending
        
# ----- Criterion input ----- #

class CriterionInput(BaseModel):
    field: str
    
class CriterionGetInput(CriterionInput):
    value: Any
    op: CompareOperator = CompareOperator.EQ
    
class CriterionSortInput(CriterionInput):
    ascending: bool = True
        
# ----- Base Get class ----- #

ModelType = TypeVar("ModelType")

class GetObject(Generic[ModelType]):
    """
    Used together with the Criterion classes for dynamic searching, sorting and filtering.
    'base' system allows automatic enforcement of a few common rules.
    """
    def __init__(self):
        self.model_type: ObjectType
        self.model: type
        self.query: SelectOfScalar[ModelType]
        self.sort_criteria = dict()
        self.base = False
        
    def convert_pydantic(self, criterion: CriterionInput):
        """
        Converts from pydantic BaseModel to the normal Criterion.
        """
        if isinstance(criterion, CriterionGetInput):
            return CriterionGet(**criterion.model_dump())
        else:
            return CriterionSort(**criterion.model_dump())
    
    # Function for applying criteria
    def apply_criterion(self, criterion: Criterion | CriterionInput):
        """
        Automatically validate attribute name and type before applying.
        """
        if isinstance(criterion, CriterionInput):
            criterion = self.convert_pydantic(criterion)
        
        try:
            attr = getattr(self.model, criterion.field)
        
        except AttributeError:
            raise ExceptionInvalidField_400(self.model_type, criterion.field)
        
        # Get
        if isinstance(criterion, CriterionGet):
            try:
                attr_type = get_type_hints(self.model)[criterion.field]
                adapter = TypeAdapter(attr_type)
                criterion.value = adapter.validate_python(criterion.value)
                
            except ValidationError:
                raise ExceptionType_400(attr_type)
            
            if criterion.op == CompareOperator.EQ:
                self.query = self.query.where(attr == criterion.value)
            if criterion.op == CompareOperator.NE:
                self.query = self.query.where(attr != criterion.value)
                
            if criterion.op == CompareOperator.LE:
                self.query = self.query.where(attr <= criterion.value)
            if criterion.op == CompareOperator.LT:
                self.query = self.query.where(attr < criterion.value)
                
            if criterion.op == CompareOperator.GE:
                self.query = self.query.where(attr >= criterion.value)
            if criterion.op == CompareOperator.GT:
                self.query = self.query.where(attr > criterion.value)
        
        # Sort
        elif isinstance(criterion, CriterionSort):
            # Sorted by both ascending and descending.
            if self.sort_criteria.get(criterion.field, criterion.ascending) != criterion.ascending:
                raise ExceptionSortContradiction_400(criterion.field, self.model.__name__)
            else:
                self.sort_criteria[criterion.field] = criterion.ascending
                
            if criterion.ascending:
                self.query = self.query.order_by(col(attr).asc())
            else:
                self.query = self.query.order_by(col(attr).desc())
                
    # Utility functions
    def get_by(self, field: str, value: Any):
        """
        Utility function for applying a get criterion with the equals operator.
        """
        crit = CriterionGet(field, value)
        
        self.apply_criterion(crit)
        
    def sort_by(self, field: str, ascending: bool):
        """
        Utility function for applying a sort criterion.
        """
        crit = CriterionSort(field, ascending=ascending)
            
        self.apply_criterion(crit)
    
    # Base get function, enforce necessary stuff and provide default sort order.
    def get(self, criteria: list[Criterion] | list[CriterionInput] = [], with_for_update: bool = False):
        if not self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} getter didn't receive base type (public, private or admin).")
        if criteria is not None:
            for crit in criteria:
                self.apply_criterion(crit)
        
        # Default sort order
        if len(self.sort_criteria) == 0:
            crit = CriterionSort("id")
            self.apply_criterion(crit)
            
        if with_for_update:
            self.query = self.query.with_for_update()
            
    # Get one
    def get_one(self, session: Session, criteria: list[Criterion] | list[CriterionInput] = [], with_for_update: bool = False) -> ModelType | None:
        self.get(criteria, with_for_update=with_for_update)
            
            
        return session.exec(self.query).first()
    
    # Get many
    def get_many(self, session: Session, criteria: list[Criterion] | list[CriterionInput] = [], with_for_update: bool = False) -> list[ModelType]:
        self.get(criteria, with_for_update=with_for_update)
            
        return list(session.exec(self.query).all())