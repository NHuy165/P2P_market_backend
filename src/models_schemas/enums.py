from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BANNED = "BANNED"
    DELETED = "DELETED"


class ItemStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    DELETED = "DELETED"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"


class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    SALE = "SALE"
    PURCHASE = "PURCHASE"
    REFUND = "REFUND"
    ADMIN_ADD = "ADMIN_ADD"
    ADMIN_SUBTRACT = "ADMIN_SUBTRACT"


class TransactionStatus(str, Enum):
    ON_HOLD = "ON_HOLD"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


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


class ExceptionType(str, Enum):
    """
    Defines a bunch of custom error types.
    """

    # 400
    REQUEST = "REQUEST"
    INVALID_FIELD = "INVALID_FIELD"
    RELATIVE_ABSOLUTE = "RELATIVE_ABSOLUTE"
    SORT_CONTRADICTION = "SORT_CONTRADICTION"

    # 401
    AUTHENTICATION = "AUTHENTICATION"

    # 403
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    NOT_ADMIN = "NOT_ADMIN"
    MODIFIED_ADMIN = "MODIFIED_ADMIN"

    # 404
    NOT_FOUND = "NOT_FOUND"

    # 405:
    METHOD = "METHOD"

    # 409
    TAKEN_USER_NAME = "TAKEN_USER_NAME"
    TAKEN_USER_EMAIL = "TAKEN_USER_EMAIL"
    TAKEN_ITEM_NAME = "TAKEN_ITEM_NAME"
    UNFINISHED_ORDERS = "UNFINISHED_ORDERS"
    INVALID_VALUE = "INVALID_VALUE"
    SELF_OWNED = "SELF_OWNED"
    TIMEOUT = "TIMEOUT"
    INVALID_STATUS = "INVALID_STATUS"

    # 422
    REQUEST_VALIDATION = "REQUEST_VALIDATION"
