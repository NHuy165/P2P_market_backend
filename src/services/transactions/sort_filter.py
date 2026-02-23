from sqlmodel.sql.expression import SelectOfScalar

from ...models_schemas.transactions import Transaction, TransactionSortFilter

def transaction_sort_filter(query: SelectOfScalar[Transaction], sort_filter: TransactionSortFilter) -> SelectOfScalar[Transaction]:
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

    if sort_filter.sorted_by is not None:
        att = getattr(Transaction, sort_filter.sorted_by.value)
        if sort_filter.sorted_ascending:
            query = query.order_by(att.asc())
        else:
            query = query.order_by(att.desc())
            
    return query