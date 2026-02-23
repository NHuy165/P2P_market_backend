from pydantic import BaseModel
from enum import Enum
from fastapi import status

# ----- CUSTOM EXCEPTIONS SCHEMAS ----- #
        
class ExceptionType(Enum):
    """
    Defines a bunch of custom error types.
    """
    
    # 400
    RELATIVE_ABSOLUTE = "RELATIVE_ABSOLUTE"
    
    # 401
    AUTHENTICATION = "AUTHENTICATION"
    
    # 403
    INVALID_ACCOUNT = "INVALID_ACCOUNT"
    NOT_ADMIN = "NOT_ADMIN"
    MODIFIED_ADMIN = "MODIFIED_ADMIN"
    
    # 404
    USER_NOT_FOUND = "USER_NOT_FOUND"
    ITEM_NOT_FOUND = "ITEM_NOT_FOUND"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    
    # 409 
    TAKEN_USER_NAME = "TAKEN_USER_NAME"
    TAKEN_USER_EMAIL = "TAKEN_USER_EMAIL"
    TAKEN_ITEM_NAME = "TAKEN_ITEM_NAME"
    PENDING_ORDERS = "PENDING_ORDERS"
    ACTIVATION_STATUS = "ACTIVATION_STATUS"
    BAN_STATUS = "BAN_STATUS"
    INVALID_VALUE = "INVALID_VALUE"
    SELF_OWNED = "SELF_OWNED"
    NOT_PENDING = "NOT_PENDING"
    TIMEOUT = "TIMEOUT"
    
# The actual exception model
class ExceptionCustom(Exception):
    def __init__(self, status_code: int, exception_type: ExceptionType, message: str, headers: dict | None = None):
        self.exception_type = exception_type
        self.message = message
        
        self.status_code = status_code
        self.headers = headers # For 401 errors
        super().__init__(self.message)
        
# Response schema for documentation
class ExceptionResponse(BaseModel):
    exception_type: ExceptionType
    message: str
    
# ----- DOCUMENTATION RESPONSES ----- #

# These things are for the frontend to read, not the users.

class Responses:
    RESPONSE_400_BAD_REQUEST = {
        "model": ExceptionResponse, 
        "description": "Request error."
    }
    
    RESPONSE_401_UNAUTHORIZED = {
        "model": ExceptionResponse, 
        "description": "Authentication error."
    }
    RESPONSE_403_FORBIDDEN = {
        "model": ExceptionResponse,
        "description": "Action is forbidden to the current account."
    }
    RESPONSE_404_NOT_FOUND = {
        "model": ExceptionResponse,
        "description": "Resource not found."
    }
    RESPONSE_409_CONFLICT = {
        "model": ExceptionResponse,
        "description": "Conflict with information in database."
    }
    
# ----- SPECIFIC ERRORS ----- #

# ----- 400 ----- #

class ExceptionRelativeAbsolute_400(ExceptionCustom):
    def __init__(self):
        super().__init__(400, ExceptionType.RELATIVE_ABSOLUTE, "Request features both relative and absolute modifications to a single value.")

# ----- 401 ----- #

class ExceptionAuthentication_401(ExceptionCustom):
    def __init__(self):
        super().__init__(401, ExceptionType.AUTHENTICATION, "Invalid credentials.",
                         {"WWW-Authenticate": "Bearer"})

# ----- 403 ----- #

class ExceptionInvalidAccount_403(ExceptionCustom):
    def __init__(self, is_banned: bool = False, is_deleted: bool = False, is_inactive: bool = False):
        if is_banned:
            super().__init__(403, ExceptionType.INVALID_ACCOUNT, "This account has been banned.")
        elif is_deleted:
            super().__init__(403, ExceptionType.AUTHENTICATION, "This account has been deleted.")
        # Checked last, since a deleted or banned account is automatically deactivated.
        elif is_inactive:
            super().__init__(403, ExceptionType.AUTHENTICATION, "This account is inactive.")

class ExceptionNotAdmin_403(ExceptionCustom):
    def __init__(self):
        super().__init__(403, ExceptionType.NOT_ADMIN, "You do not have admin privileges.")

class ExceptionModifiedAdmin_403(ExceptionCustom):
    def __init__(self):
        super().__init__(403, ExceptionType.MODIFIED_ADMIN, "Cannot modify another admin's account.")
        
# ----- 404 ----- #

class ExceptionUserNotFound_404(ExceptionCustom):
    def __init__(self, user_id: int):
        super().__init__(404, ExceptionType.USER_NOT_FOUND, f"Could not find a user with an ID of {user_id} under the predefined conditions.")

class ExceptionItemNotFound_404(ExceptionCustom):
    def __init__(self, item_id: int):
        super().__init__(404, ExceptionType.ITEM_NOT_FOUND, f"Could not find a valid item with an ID of {item_id} under the predefined conditions.")
        
class ExceptionOrderNotFound_404(ExceptionCustom):
    def __init__(self, order_id: int):
        super().__init__(404, ExceptionType.ORDER_NOT_FOUND, f"Could not find a valid order with an ID of {order_id} under the predefined conditions.")
    

# ----- 409 ----- #

class ExceptionTakenUserEmail_409(ExceptionCustom):
    def __init__(self):
        super().__init__(409, ExceptionType.TAKEN_USER_EMAIL, "Another account with this email already exists.")

class ExceptionTakenUserName_409(ExceptionCustom):
    def __init__(self):
        super().__init__(409, ExceptionType.TAKEN_USER_NAME, "Another account with this name already exists.")

class ExceptionTakenItemName_409(ExceptionCustom):
    def __init__(self):
        super().__init__(409, ExceptionType.TAKEN_ITEM_NAME, "Another one of your items already has this name.")

class ExceptionPendingOrders_409(ExceptionCustom):
    def __init__(self):
        super().__init__(409, ExceptionType.PENDING_ORDERS, "Your account still has pending buy or sell orders.")

class ExceptionActivationStatus_409(ExceptionCustom):
    def __init__(self, activated: bool):
        super().__init__(409, ExceptionType.ACTIVATION_STATUS, f"This account is already {"active" if activated else "inactive"}.")

class ExceptionBanStatus_409(ExceptionCustom):
    def __init__(self, banned: bool):
        super().__init__(409, ExceptionType.ACTIVATION_STATUS, f"This account is {"already banned" if banned else "not banned"}.")

class ExceptionInvalidValue_409(ExceptionCustom):
    def __init__(self, name: str, value: int | float):
        super().__init__(409, ExceptionType.INVALID_VALUE, f"Action causes value to fall out of acceptable range. Name: {name}. Value after action: {value}")

# Certain actions to self-owned objects are forbidden, such as buying your own items.        
class ExceptionSelfOwned_409(ExceptionCustom):
    def __init__(self, desc: str):
        super().__init__(409, ExceptionType.SELF_OWNED, f"Cannot perform the following actions on self-owned objects: {desc}")
        
class ExceptionNotPending_409(ExceptionCustom):
    def __init__(self):
        super().__init__(409, ExceptionType.NOT_PENDING, f"Action failed because the order is no longer pending.")
        
class ExceptionTimeout_409(ExceptionCustom):
    def __init__(self, time_desc: str | None = None):
        super().__init__(409, ExceptionType.TIMEOUT, f"The time allowed for this action has run out{f" ({time_desc})" if time_desc else ""}.")