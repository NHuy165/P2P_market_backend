from typing import Any

from httpx import Response
from pydantic import BaseModel

from src.models_schemas.enums import CompareOperator
from src.models_schemas.transactions import Transaction


def model_validator(data: dict, model: type[BaseModel], contents: dict[str, Any] = {}):
    validated_data = model.model_validate(data)

    for key, val in contents.items():
        attr = getattr(validated_data, key)
        try:
            if isinstance(val, tuple):
                if val[1] == CompareOperator.EQ:
                    assert attr == val[0]
                elif val[1] == CompareOperator.NE:
                    assert attr != val[0]
                elif val[1] == CompareOperator.GE:
                    assert attr >= val[0]
                elif val[1] == CompareOperator.GT:
                    assert attr > val[0]
                elif val[1] == CompareOperator.LE:
                    assert attr <= val[0]
                elif val[1] == CompareOperator.LT:
                    assert attr <= val[0]
            else:
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
    try:
        assert response.status_code == status_code
    except:
        print("CURRENTLY:", response.status_code)
        print("CORRECT:", status_code)

        raise

    # Return model
    if model is not None:
        model_validator(response.json(), model, contents)


def validate_results(
    data: list,
    columns: list[str],
    correct: set[tuple],
    validate: type[BaseModel] | None = None,
):
    current = set()

    for tran in data:
        if validate:
            tran = validate.model_validate(tran)
        tran_info = []

        for col in columns:
            info = getattr(tran, col)
            tran_info.append(info)

        current.add(tuple(tran_info))

    try:
        assert current == correct

    except:
        print(f"Current: {current}")
        print(f"Correct: {correct}")

        raise
