from sqlmodel import Session, or_, select

from ..exceptions.core import ExceptionRequest_400
from ..models_schemas.orders import Order, OrderOutput
from .core import Criterion, CriterionInput, GetObject, ObjectType

class GetOrder(GetObject[Order]):
    def __init__(self):
        self.model_type = ObjectType.ORDER
        self.model = Order
        self.query = select(self.model)
        self.user_id: int | None
        super().__init__()
        
    # Set base type functions
    def base_sell(self, user_id: int):
        if self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} received new base type with existing one.")
        self.query = self.query.where(Order.seller_id == user_id)
        self.user_id = user_id
        self.base = True
        
    def base_buy(self, user_id: int):
        if self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} received new base type with existing one.")
        self.query = self.query.where(Order.buyer_id == user_id)
        self.user_id = user_id
        self.base = True
        
    def base_both(self, user_id: int):
        if self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} received new base type with existing one.")
        self.query = self.query.where(or_(Order.buyer_id == user_id, Order.seller_id == user_id))
        self.user_id = user_id
        self.base = True
        
    def base_none(self):
        if self.base:
            raise ExceptionRequest_400(f"{self.model.__name__} received new base type with existing one.")
        self.user_id = None
        self.base = True
        
    def get_one_labeled(self, session: Session, criteria: list[Criterion] | list[CriterionInput] = []) -> OrderOutput | None:
        unlabeled = self.get_one(session, criteria)
        
        if unlabeled is not None:
            labeled = OrderOutput.model_validate(unlabeled, update={"type": "SELL" if unlabeled.seller_id == self.user_id else "BUY"})
            
        return labeled
    
    def get_many_labeled(self, session: Session, criteria: list[Criterion] | list[CriterionInput] = []) -> list[OrderOutput]:
        unlabeled = self.get_many(session, criteria)
        
        labeled = [OrderOutput.model_validate(ord, update={"type": "SELL" if ord.seller_id == self.user_id else "BUY"}) for ord in unlabeled]
            
        return labeled
    
            
        
            