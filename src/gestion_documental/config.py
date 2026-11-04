from functools import lru_cache

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIGURACION_ENV = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class ConfiguracionError(RuntimeError):
    pass


class Settings(BaseSettings):
    model_config = CONFIGURACION_ENV

    mongo_uri: str = Field(min_length=1)
    mongo_db: str = Field(min_length=1)


class ConfiguracionAuth(BaseSettings):
    model_config = CONFIGURACION_ENV

    jwt_secret: str = Field(min_length=32)
    jwt_minutos: int = Field(default=60, gt=0)


class ConfiguracionApi(BaseSettings):
    model_config = CONFIGURACION_ENV

    cors_origins: str = ""

    @property
    def origenes(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


def cargar[T: BaseSettings](clase: type[T]) -> T:
    try:
        return clase()
    except ValidationError as exc:
        variables = sorted({str(error["loc"][0]).upper() for error in exc.errors()})
        raise ConfiguracionError(
            f"Variables faltantes o inválidas en .env: {', '.join(variables)}"
        ) from exc


@lru_cache
def get_settings() -> Settings:
    return cargar(Settings)


@lru_cache
def get_config_auth() -> ConfiguracionAuth:
    return cargar(ConfiguracionAuth)
