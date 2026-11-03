from functools import lru_cache

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfiguracionError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongo_uri: str = Field(min_length=1)
    mongo_db: str = Field(min_length=1)


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        variables = sorted({str(error["loc"][0]).upper() for error in exc.errors()})
        raise ConfiguracionError(
            f"Variables faltantes o vacías en .env: {', '.join(variables)}"
        ) from exc
