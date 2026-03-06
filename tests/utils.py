from typing import Any

from httpx import Response
from pydantic import BaseModel


def validator(
    response: Response,
    status_code,
    model: type[BaseModel] | None = None,
    contents: dict[str, Any] = {},
) -> None:
    # Status code
    assert response.status_code == status_code

    # Return model
    if model is not None:
        validated_response_body = model.model_validate(response.json())

    # Return model contents:
    for key, val in contents.items():
        attr = getattr(validated_response_body, key)

        assert attr == val
