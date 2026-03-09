from src.exceptions.core import ExceptionRequest_400


def bvalidator_forbid_none(s):
    if s is None:
        raise ExceptionRequest_400(
            "This field cannot receive a null. Either leave it empty or provide information of a suitable type.}."
        )
    return s
