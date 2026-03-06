from decimal import Decimal
from enum import Enum

from pydantic import BaseModel

# ----- CUSTOM EXCEPTIONS SCHEMAS ----- #


class ObjectType(str, Enum):
    ITEM = "Item"
    ORDER = "Order"
    USER = "User"
    TRANSACTION = "Transaction"


class ExceptionType(Enum):
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


# The actual exception model
class ExceptionCustom(Exception):
    def __init__(
        self,
        status_code: int,
        exception_type: ExceptionType,
        message: str,
        headers: dict | None = None,
    ):
        self.exception_type = exception_type
        self.message = message

        self.status_code = status_code
        self.headers = headers  # For 401 errors
        super().__init__(self.message)


# Response schema for documentation
class ExceptionResponse(BaseModel):
    exception_type: str  # Taken from ExceptionType
    message: str


# ----- DOCUMENTATION RESPONSES ----- #

# These things are for the frontend to read, not the users.


class Responses:
    RESPONSE_400_BAD_REQUEST = {
        "model": ExceptionResponse,
        "description": "Request error.",
    }

    RESPONSE_401_UNAUTHORIZED = {
        "model": ExceptionResponse,
        "description": "Authentication error.",
    }
    RESPONSE_403_FORBIDDEN = {
        "model": ExceptionResponse,
        "description": "Action is forbidden to the current account.",
    }
    RESPONSE_404_NOT_FOUND = {
        "model": ExceptionResponse,
        "description": "Resource not found.",
    }

    RESPONSE_405_METHOD = {
        "model": ExceptionResponse,
        "description": "Method not allowed.",
    }

    RESPONSE_409_CONFLICT = {
        "model": ExceptionResponse,
        "description": "Conflict with information in database.",
    }

    RESPONSE_422_UNPROCESSABLE_CONTENT = {
        "model": ExceptionResponse,
        "description": "Request validation error.",
    }


# ----- SPECIFIC ERRORS ----- #

# ----- 400 ----- #


class ExceptionRequest_400(ExceptionCustom):
    def __init__(self, desc: str):
        super().__init__(400, ExceptionType.REQUEST, desc)


class ExceptionInvalidField_400(ExceptionCustom):
    def __init__(self, obj: ObjectType, field: str):
        super().__init__(
            400,
            ExceptionType.INVALID_FIELD,
            f"{obj.capitalize()} has no field called {field}.",
        )


class ExceptionRelativeAbsolute_400(ExceptionCustom):
    def __init__(self):
        super().__init__(
            400,
            ExceptionType.RELATIVE_ABSOLUTE,
            "Request features both relative and absolute modifications to a single value.",
        )


class ExceptionSortContradiction_400(ExceptionCustom):
    def __init__(self, att: str, obj: str):
        super().__init__(
            400,
            ExceptionType.SORT_CONTRADICTION,
            f"The following attribute was sorted by both descending and ascending orders: {att} (class: {obj})",
        )


# ----- 401 ----- #


class ExceptionAuthentication_401(ExceptionCustom):
    def __init__(self):
        super().__init__(
            401,
            ExceptionType.AUTHENTICATION,
            "Invalid credentials.",
            {"WWW-Authenticate": "Bearer"},
        )


# ----- 403 ----- #


class ExceptionInvalidAccount_403(ExceptionCustom):
    def __init__(self, status: str):
        super().__init__(
            403,
            ExceptionType.INVALID_ACCOUNT,
            f"This account has been {status}.",
        )


class ExceptionNotAdmin_403(ExceptionCustom):
    def __init__(self):
        super().__init__(
            403, ExceptionType.NOT_ADMIN, "You do not have admin privileges."
        )


class ExceptionModifiedAdmin_403(ExceptionCustom):
    def __init__(self):
        super().__init__(
            403, ExceptionType.MODIFIED_ADMIN, "Cannot modify another admin's account."
        )


# ----- 404 ----- #


class ExceptionNotFound_404(ExceptionCustom):
    def __init__(self, obj: ObjectType, id: int):
        super().__init__(
            404,
            ExceptionType.NOT_FOUND,
            f"Could not find any {obj.value} with an ID of {id} under the predefined conditions.",
        )


# ----- 409 ----- #


class ExceptionTakenUserEmail_409(ExceptionCustom):
    def __init__(self):
        super().__init__(
            409,
            ExceptionType.TAKEN_USER_EMAIL,
            "Another account with this email already exists.",
        )


class ExceptionTakenUserName_409(ExceptionCustom):
    def __init__(self):
        super().__init__(
            409,
            ExceptionType.TAKEN_USER_NAME,
            "Another account with this name already exists.",
        )


class ExceptionTakenItemName_409(ExceptionCustom):
    def __init__(self):
        super().__init__(
            409,
            ExceptionType.TAKEN_ITEM_NAME,
            "Another one of your items already has this name.",
        )


class ExceptionUnfinishedOrders_409(ExceptionCustom):
    def __init__(self):
        super().__init__(
            409,
            ExceptionType.UNFINISHED_ORDERS,
            "Your account still has unfinished orders.",
        )


class ExceptionInvalidStatus_409(ExceptionCustom):
    def __init__(self, obj: ObjectType, status: str):
        super().__init__(
            409,
            ExceptionType.INVALID_STATUS,
            f"This action cannot be performed on an object of type {obj.value} with the status {status}.",
        )


class ExceptionInvalidValue_409(ExceptionCustom):
    def __init__(self, name: str, value: int | Decimal):
        super().__init__(
            409,
            ExceptionType.INVALID_VALUE,
            f"Action causes value to fall out of acceptable range. Name: {name}. Value after action: {value}",
        )


# Certain actions to self-owned objects are forbidden, such as buying your own items.
class ExceptionSelfOwned_409(ExceptionCustom):
    def __init__(self, desc: str):
        super().__init__(
            409,
            ExceptionType.SELF_OWNED,
            f"Cannot perform the following actions on self-owned objects: {desc}",
        )


class ExceptionTimeout_409(ExceptionCustom):
    def __init__(self, time_desc: str | None = None):
        super().__init__(
            409,
            ExceptionType.TIMEOUT,
            f"The time allowed for this action has run out{f' ({time_desc})' if time_desc else ''}.",
        )
