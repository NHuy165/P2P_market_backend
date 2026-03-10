from src.exceptions.core import ExceptionRequest_400
from src.models_schemas.enums import ItemStatus


def bvalidator_forbid_none(s):
    if s is None:
        raise ExceptionRequest_400(
            "This field cannot receive a null. Either leave it empty or provide information of a suitable type.}."
        )
    return s


def avalidator_limit_item_status(status: ItemStatus):
    if status == ItemStatus.BANNED or status == ItemStatus.DELETED:
        raise ExceptionRequest_400("Can only set item to ACTIVE or SUSPENDED.")
    return status
