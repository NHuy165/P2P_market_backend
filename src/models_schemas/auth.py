from datetime import datetime

from pydantic import BaseModel

# ----- TOKEN INPUT ----- #


class TokenInput(BaseModel):
    sub: int  # Converts str to int
    iat: datetime
    exp: datetime
    type: str


# ----- TOKEN OUPUT ----- #


class TokenOutput(BaseModel):
    access_token: str
    token_type: str
