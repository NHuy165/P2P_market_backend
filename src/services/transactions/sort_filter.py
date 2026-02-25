from sqlmodel import col
from sqlmodel.sql.expression import SelectOfScalar

from ...models_schemas.transactions import Transaction, TransactionSearchSortFilter, TransactionStatus, TransactionType

def transaction_sort_filter(query: SelectOfScalar[Transaction], sort_filter: TransactionSearchSortFilter) -> SelectOfScalar[Transaction]:
    if sort_filter.id is not None:
        query = query.where(Transaction.id == sort_filter.id)
    if sort_filter.order_id is not None:
        query = query.where(Transaction.order_id == sort_filter.order_id)
    if sort_filter.user_id is not None:
        query = query.where(Transaction.user_id == sort_filter.user_id)
        
    if sort_filter.type is not None:
        query = query.where(Transaction.type == sort_filter.type)   
    if sort_filter.status is not None:
        query = query.where(Transaction.status == sort_filter.status)
        
    if sort_filter.amount_lower is not None:
        query = query.where(Transaction.amount >= sort_filter.amount_lower)
    if sort_filter.amount_higher is not None:
        query = query.where(Transaction.amount <= sort_filter.amount_higher)
        
    if sort_filter.created_at_lower is not None:
        query = query.where(Transaction.created_at >= sort_filter.created_at_lower)
    if sort_filter.created_at_higher is not None:
        query = query.where(Transaction.created_at <= sort_filter.created_at_higher)
        
    if sort_filter.include_deposit is False:
        query = query.where(Transaction.type is not TransactionType.DEPOSIT)
    if sort_filter.include_withdrawal is False:
        query = query.where(Transaction.type is not TransactionType.WITHDRAWAL)
    if sort_filter.include_sale is False:
        query = query.where(Transaction.type is not TransactionType.SALE)
    if sort_filter.include_purchase is False:
        query = query.where(Transaction.type is not TransactionType.PURCHASE)
    if sort_filter.include_purchase is False:
        query = query.where(Transaction.type is not TransactionType.REFUND)
        
    if sort_filter.include_on_hold is False:
        query = query.where(Transaction.status is not TransactionStatus.ON_HOLD)
    if sort_filter.include_success is False:
        query = query.where(Transaction.status is not TransactionStatus.SUCCESS)
    if sort_filter.include_failed is False:
        query = query.where(Transaction.status is not TransactionStatus.FAILED)

    att = getattr(Transaction, sort_filter.sorted_by.value)
    if sort_filter.sorted_ascending:
        query = query.order_by(col(att).asc())
    else:
        query = query.order_by(col(att).desc())

    return query