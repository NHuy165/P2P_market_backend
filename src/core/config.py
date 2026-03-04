from pathlib import Path

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    POSTGRES_URL: PostgresDsn
    POSTGRES_URL_TEST: PostgresDsn
    SECRET_KEY: str
    TOKEN_EXPIRY_MIN: int
    TOKEN_ENCODE_ALGORITHM: str

    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore
