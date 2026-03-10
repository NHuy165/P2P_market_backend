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
