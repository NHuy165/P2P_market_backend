from typing import Any

from httpx import Response
from pydantic import BaseModel


def model_validator(data: dict, model: type[BaseModel], contents: dict[str, Any] = {}):
    validated_data = model.model_validate(data)

    for key, val in contents.items():
        attr = getattr(validated_data, key)
        try:
            assert attr == val
        except:
            print("CURRENTLY:", attr)
            print("CORRECT:", val)

            raise


def response_validator_single(
    response: Response,
    status_code,
    model: type[BaseModel] | None = None,
    contents: dict[str, Any] = {},
) -> None:
    # Status code
    assert response.status_code == status_code

    # Return model
    if model is not None:
        model_validator(response.json(), model, contents)
