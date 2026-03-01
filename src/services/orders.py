from sqlmodel import Session
from datetime import datetime, timezone

from ..repository.core import CriterionInput
from ..repository.items import GetItem
from ..repository.orders import GetOrder
from ..repository.users import GetUser
from ..exceptions.core import ExceptionInvalidValue_409, ExceptionNotPending_409, ExceptionSelfOwned_409, ExceptionNotFound_404, ObjectType
from ..models_schemas.orders import Order, OrderInput, OrderOutput, OrderStatus
from ..models_schemas.users import User
from ..models_schemas.transactions import Transaction, TransactionType, TransactionStatus

# ----- Order create ----- #

def create_order_service(user: User, session: Session, order_inp: OrderInput) -> Order:
    """
    Creates an order and its transaction.
    Money is subtracted from the buyer and only gets transfered to the buyer on order completion (DELIVERED status).
    """
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("id", user.id)
    
    user_wfu = get_user.get_one(session, with_for_update=True)
    if user_wfu is None:
        assert user.id is not None
        raise ExceptionNotFound_404(ObjectType.USER, user.id)
    
    get_item = GetItem()
    get_item.base_public()
    get_item.get_by("id", order_inp.item_id)
    
    item = get_item.get_one(session, with_for_update=True)
    if item is None:
        raise ExceptionNotFound_404(ObjectType.ITEM, order_inp.item_id)
    
    if user_wfu.id == item.seller_id:
        raise ExceptionSelfOwned_409("Buying item")
    
    if item.stock_quantity < order_inp.quantity:
        raise ExceptionInvalidValue_409("Item stock quantity", item.stock_quantity - order_inp.quantity)
    
    total_amount = order_inp.quantity * item.price
    if total_amount > user_wfu.balance:
        raise ExceptionInvalidValue_409("Account balance", user_wfu.balance - total_amount)
    
    # Subtracting item stock quantity and buyer's balance
    item.stock_quantity -= order_inp.quantity
    user_wfu.balance -= order_inp.quantity * item.price
    # Seller's balance is only updated when order's status is delivered
    
    # Creating order
    order = Order(**order_inp.model_dump())
    order.price_per_item = item.price
    
    order.item = item # This is technically redundant.
    order.seller = item.seller
    order.buyer = user_wfu
    
    # Buyer spends money right away.
    trans_buyer = Transaction(amount=total_amount,
                        type=TransactionType.PURCHASE,
                        order=order,
                        user=user_wfu,
                        finished_at=datetime.now(timezone.utc),
                        status=TransactionStatus.SUCCESS)
    
    # Seller only gets money when item arrives. That's why it's on hold.
    trans_seller = Transaction(amount=total_amount,
                        type=TransactionType.SALE,
                        order=order,
                        user=item.seller,
                        status=TransactionStatus.ON_HOLD)
    
    session.add(trans_buyer)
    session.add(trans_seller)
    session.add(order)
    session.add(user_wfu)
    session.add(item)
    session.commit()
    session.refresh(order)
    
    return order
    
# ----- Order read ----- #

def read_orders_services(user: User, session: Session, type: bool | None = None, criteria: list[CriterionInput] = []) -> list[OrderOutput]:
    """
    type: True for sell orders, False for buy orders, None for both
    """
    get_order = GetOrder()
    
    assert user.id is not None
    if type is True:
        get_order.base_sell(user.id)
    elif type is False:
        get_order.base_buy(user.id)
    else:
        get_order.base_both(user.id)
        
    orders = get_order.get_many_labeled(session, criteria)
    
    return orders

def read_orders_admin_service(session: Session, user_id: int, type: bool | None = None, criteria: list[CriterionInput] = []) -> list[OrderOutput]:
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("id", user_id)
    
    user = get_user.get_one(session)
    
    if user is None:
        raise ExceptionNotFound_404(ObjectType.USER, user_id)
    
    return read_orders_services(user, session, type, criteria)

# ----- Order update ----- #

# def update_order_service(user: User, session: Session, order_id: int, order_upd: OrderUpdate):
#     """
#     Allows users to change their order within 10 minutes of order creation, order is still pending, using new item price.
#     """
    
#     user_wfu = session.get(User, user.id, with_for_update=True)
#     if user_wfu is None:
#         assert user.id is not None
#         raise ExceptionNotFound_404(ObjectType.USER, user.id)
    
#     query = select(Order).where(Order.id == order_id, Order.buyer_id == user_wfu.id).with_for_update()
#     order = session.exec(query).first()
#     if order is None:
#         raise ExceptionNotFound_404(ObjectType.ORDER, order_id)
    
#     # Order no longer pending
#     if order.status is not OrderStatus.PENDING:
#         raise ExceptionNotPending_409()
    
#     # Can only edit within 10 minutes of creation.
#     now_time = datetime.now(timezone.utc)
#     if now_time - order.created_at > timedelta(minutes=10):
#         raise ExceptionTimeout_409("10 minutes")
    
#     item = session.get(Item, order.item_id, with_for_update=True)
#     if item is None:
#         assert order.item_id is not None
#         raise ExceptionNotFound_404(ObjectType.ITEM, order.item_id)

#     update_contents = order_upd.model_dump()
#     if order_upd.quantity_relative is not None:
#         update_contents["quantity"] = order.quantity + order_upd.quantity_relative
    
#     # Edited content results in order quantity being fewer than 0 or higher than stock.
#     if update_contents["quantity"] <= 0: 
#         raise ExceptionInvalidValue_409("Ordered item quantity", update_contents["quantity"])
#     if update_contents["quantity"] > item.stock_quantity + order.quantity:
#         raise ExceptionInvalidValue_409("Item stock quantity", item.stock_quantity + order.quantity - update_contents["quantity"])
    
#     # Edited content results in insufficient funds from buyer.
#     old_balance = user_wfu.balance
#     refund = order.price_per_item * order.quantity
#     new_cost = update_contents["quantity"] * item.price
#     new_balance = old_balance + refund - new_cost
    
#     if update_contents["quantity"] > order.quantity and new_balance < 0:
#         raise ExceptionInvalidValue_409("Account balance", new_balance)
    
#     # Actual update logic.
#     money_change = (order.price_per_item * order.quantity) - (update_contents["quantity"] * item.price)
#     # If new order costs more, this number is negative
    
#     # User update
#     user_wfu.balance += money_change
    
#     # Transactions update
#     for trans in order.transactions:
#         trans.amount -= money_change
    
#     # Item update
#     item.stock_quantity = item.stock_quantity + order.quantity - update_contents["quantity"]
    
#     # Order update
#     order.quantity = update_contents["quantity"]
#     order.price_per_item = item.price
    
#     session.add(user_wfu)
#     session.add(order.transactions)
#     session.add(item)
#     session.add(order)
    
#     session.commit()
#     session.refresh(order)
    
#     return order

# Deprecated function because it's kind of weird.

def approve_order_service(session: Session, order_id: int) -> Order:
    get_order = GetOrder()
    get_order.base_none()
    get_order.get_by("id", order_id)
    get_order.get_by("status", OrderStatus.PENDING)
    
    order = get_order.get_one(session, with_for_update=True)
    
    if order is None:
        raise ExceptionNotFound_404(ObjectType.ORDER, order_id)
    
    order.status = OrderStatus.SHIPPED
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order

def complete_order_service(session: Session, order_id: int) -> Order:
    get_order = GetOrder()
    get_order.base_none()
    get_order.get_by("id", order_id)
    get_order.get_by("status", OrderStatus.SHIPPED)
    
    order = get_order.get_one(session, with_for_update=True)
    
    if order is None:
        raise ExceptionNotFound_404(ObjectType.ORDER, order_id)
    
    # Completion logic
    order.status = OrderStatus.DELIVERED
    order.finished_at = datetime.now(timezone.utc)
    order.seller.balance += order.quantity * order.price_per_item
    
    for trans in order.transactions:
        if trans.type == TransactionType.SALE:
            trans.status = TransactionStatus.SUCCESS
            trans.finished_at = datetime.now(timezone.utc)
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order
    
# ----- Order delete ----- #

def delete_logic(order: Order):
    for trans in order.transactions:
        if trans.type == TransactionType.SALE:
            trans.status = TransactionStatus.FAILED
            trans.finished_at = datetime.now(timezone.utc)
            
    order.item.stock_quantity += order.quantity
    order.buyer.balance += order.price_per_item * order.quantity
    order.status = OrderStatus.CANCELLED
    order.finished_at = datetime.now(timezone.utc)
    
    # Refunds the buyer
    refund_trans = Transaction(amount=order.price_per_item * order.quantity,
                               type=TransactionType.REFUND,
                               order=order,
                               user=order.buyer,
                               status=TransactionStatus.SUCCESS)
    
    return refund_trans
    

def delete_order_service(user: User, session: Session, order_id: int) -> Order:
    get_user = GetUser()
    get_user.base_existing()
    get_user.get_by("id", user.id)
    
    user_wfu = get_user.get_one(session, with_for_update=True)
    
    # user_wfu can be either seller or buyer here
    
    if user_wfu is None:
        assert user.id is not None
        raise ExceptionNotFound_404(ObjectType.USER, user.id)
    
    # Both seller and buyer can cancel the order
    assert user_wfu.id is not None
    get_order = GetOrder()
    get_order.base_both(user_wfu.id)
    get_order.get_by("id", order_id)
    
    order = get_order.get_one(session, with_for_update=True)
    
    if order is None:
        raise ExceptionNotFound_404(ObjectType.ORDER, order_id)
    if order.status is not OrderStatus.PENDING:
        raise ExceptionNotPending_409()
    
    # Delete logic
    refund_trans = delete_logic(order)
    
    session.add(order)
    session.add(refund_trans)
    session.commit()
    session.refresh(order)
    
    return order

def delete_order_admin_service(session: Session, order_id: int) -> Order:
    get_order = GetOrder()
    get_order.base_none()
    get_order.get_by("id", order_id)
    
    order = get_order.get_one(session, with_for_update=True)
    
    if order is None:
        raise ExceptionNotFound_404(ObjectType.ORDER, order_id)
    if order.status is not OrderStatus.PENDING:
        raise ExceptionNotPending_409()
    
    # Delete logic
    refund_trans = delete_logic(order)
    
    session.add(order)
    session.add(refund_trans)
    session.commit()
    session.refresh(order)
    
    return order
    
    
    
    
    
    
    
    
    

    
    
    
    
    
    
    
    
    