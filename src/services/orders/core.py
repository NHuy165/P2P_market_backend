from sqlmodel import Session, case, or_, select
from datetime import datetime, timezone, timedelta

from .sort_filter import order_sort_filter
from ...exceptions import ExceptionConflict, ExceptionNegativeValue, ExceptionNotFound, ExceptionTimeOut
from ...models.items import Item
from ...models.orders import Order, OrderInput, OrderOutput, OrderSortFilter, OrderUpdate, OrderStatus
from ...models.users import User
from ...models.transactions import Transaction, TransactionType, TransactionStatus


# ----- Order create ----- #

def create_order_service(user: User, session: Session, order_inp: OrderInput) -> Order:
    """
    Creates an order and its transaction.
    Money is subtracted from the buyer and only gets transfered to the buyer on order completion (DELIVERED status).
    """
    user_reserved = session.get(User, user.id, with_for_update=True)
    if user_reserved is None:
        raise ExceptionNotFound("User")
    
    item = session.get(Item, order_inp.item_id, with_for_update=True)
    if item is None:
        raise ExceptionNotFound("Item")
    
    if user_reserved.id == item.seller_id:
        raise ExceptionConflict()
    
    if item.stock_quantity < order_inp.quantity:
        raise ExceptionNegativeValue("Negative stock quantity")
    
    total_amount = order_inp.quantity * item.price
    if total_amount > user_reserved.balance:
        raise ExceptionNegativeValue("Negative balance")
    
    # Subtracting item stock quantity and buyer's balance
    item.stock_quantity -= order_inp.quantity
    user_reserved.balance -= order_inp.quantity * item.price
    # Seller's balance is only updated when order's status is delivered
    
    # Creating order
    order = Order(**order_inp.model_dump())
    order.price_per_item = item.price
    
    order.item = item # This is technically redundant.
    order.seller = item.seller
    order.buyer = user_reserved
    
    # Buyer spends money right away.
    trans_buyer = Transaction(amount=total_amount,
                        type=TransactionType.PURCHASE,
                        order=order,
                        user=user_reserved,
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
    session.add(user_reserved)
    session.add(item)
    session.commit()
    session.refresh(order)
    
    return order
    
# ----- Order read ----- #

def read_orders_services(user: User, session: Session, sort_filter: OrderSortFilter | None = None) -> list[OrderOutput]:
    query = select(Order)
    
    if sort_filter is not None:
        query = order_sort_filter(query, sort_filter)
        
        # Only gets sell orders.
        if sort_filter.type is True: 
            query = query.where(Order.seller_id == user.id)
            result = [OrderOutput.model_validate(ord, update={"type": "SELL"}) for ord in session.exec(query).all()]
            
        # Only gets buy orders.
        elif sort_filter.type is False:
            query = query.where(Order.buyer_id == user.id)
            result = [OrderOutput.model_validate(ord, update={"type": "BUY"}) for ord in session.exec(query).all()]

    # Gets both types of orders and label accordingly.
    if sort_filter is None or sort_filter.type is None:
        query = query.where(or_(Order.seller_id == user.id, Order.buyer_id == user.id))
        result = [OrderOutput.model_validate(ord, update={"type": "SELL" if ord.seller_id == user.id else "BUY"}) for ord in session.exec(query).all()]
    
    return result

# ----- Order update ----- #

def update_order_service(user: User, session: Session, order_id: int, order_upd: OrderUpdate):
    """
    Allows users to change their order within 10 minutes of order creation, order is still pending, using new item price.
    """
    
    user_reserved = session.get(User, user.id, with_for_update=True)
    if user_reserved is None:
        raise ExceptionNotFound("User")
    
    query = select(Order).where(Order.id == order_id, Order.buyer_id == user_reserved.id).with_for_update()
    order = session.exec(query).first()
    if order is None:
        raise ExceptionNotFound("Order")
    
    # Order no longer pending
    if order.status is not OrderStatus.PENDING:
        raise ExceptionConflict()
    
    # Can only edit within 10 minutes of creation.
    now_time = datetime.now(timezone.utc)
    if now_time - order.created_at > timedelta(minutes=10):
        raise ExceptionTimeOut()
    
    item = session.get(Item, order.item_id, with_for_update=True)
    if item is None:
        raise ExceptionNotFound("Item")

    update_contents = order_upd.model_dump()
    if order_upd.quantity_relative is not None:
        update_contents["quantity"] = order.quantity + order_upd.quantity_relative
    
    # Edited content results in order quantity less than or equals 0 or higher than stock.
    if update_contents["quantity"] <= 0 or update_contents["quantity"] > item.stock_quantity + order.quantity:
        raise ExceptionNegativeValue("Item")
    
    # Edited content results in insufficient funds from buyer.
    if update_contents["quantity"] > order.quantity and user_reserved.balance + (order.price_per_item * order.quantity) - (update_contents["quantity"] * item.price) < 0:
        raise ExceptionNegativeValue("User")
    
    
    
    # Actual update logic.
    money_change = (order.price_per_item * order.quantity) - (update_contents["quantity"] * item.price)
    # If new order costs more, this number is negative
    
    # User update
    user_reserved.balance += money_change
    
    # Transactions update
    for trans in order.transactions:
        trans.amount -= money_change
    
    # Item update
    item.stock_quantity = item.stock_quantity + order.quantity - update_contents["quantity"]
    
    # Order update
    order.quantity = update_contents["quantity"]
    order.price_per_item = item.price
    
    session.add(user_reserved)
    session.add(order.transactions)
    session.add(item)
    session.add(order)
    
    session.commit()
    session.refresh(order)
    
    return order
    
# ----- Order delete ----- #

def delete_order_service(user: User, session: Session, order_id: int) -> Order:
    user_reserved = session.get(User, user.id, with_for_update=True)
    if user_reserved is None:
        raise ExceptionNotFound("User")
    
    # Both seller and buyer can cancel the order
    query = select(Order).where(Order.id == order_id, or_(Order.buyer_id == user.id, Order.seller_id == user.id), Order.status == OrderStatus.PENDING).with_for_update()
    order = session.exec(query).first()
    if order is None:
        raise ExceptionNotFound("Order")
    
    # Delete logic
    for trans in order.transactions:
        trans.status = TransactionStatus.FAILED
    order.item.stock_quantity += order.quantity
    order.buyer.balance += order.price_per_item * order.quantity
    order.status = OrderStatus.CANCELLED
    
    session.add(order)
    session.commit()
    session.refresh(order)
    
    return order
    
    
    
    
    
    
    
    

    
    
    
    
    
    
    
    
    