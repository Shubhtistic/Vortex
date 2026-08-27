from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Common ---
class CommonSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


# --- Postgres ---
class PostgresSettings(CommonSettings):
    postgres_server: str = Field(
        validation_alias="POSTGRES_SERVER",
    )

    postgres_port: int = Field(
        validation_alias="POSTGRES_PORT",
    )

    postgres_user: str = Field(
        validation_alias="POSTGRES_USER",
    )

    postgres_password: SecretStr = Field(
        validation_alias="POSTGRES_PASSWORD",
    )

    postgres_db: str = Field(
        validation_alias="POSTGRES_DB",
    )

    @property
    def postgres_async_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}"
            f"@{self.postgres_server}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )


# --- Redis ---
class RedisSettings(CommonSettings):
    redis_host: str = Field(
        validation_alias="REDIS_HOST",
    )

    redis_port: int = Field(
        validation_alias="REDIS_PORT",
    )

    redis_db: int = Field(
        validation_alias="REDIS_DB",
    )

    redis_password: Optional[SecretStr] = Field(
        default=None,
        validation_alias="REDIS_PASSWORD",
    )

    redis_tls: bool = Field(
        validation_alias="REDIS_TLS",
    )

    @property
    def redis_url(self) -> str:
        scheme = "rediss" if self.redis_tls else "redis"

        password = (
            f":{self.redis_password.get_secret_value()}@" if self.redis_password else ""
        )

        return (
            f"{scheme}://"
            f"{password}"
            f"{self.redis_host}:"
            f"{self.redis_port}/"
            f"{self.redis_db}"
        )


# --- App settings ---
class AppSettings(CommonSettings):
    project_name: str = Field(
        default="SonClarus",
        validation_alias="PROJECT_NAME",
    )

    version: str = Field(
        validation_alias="VERSION",
    )

    docs_endpoint: str = Field(
        validation_alias="DOCS_ENDPOINT",
    )


# --- Jwt Auth ---
class JwtSettings(CommonSettings):
    private_key: SecretStr = Field(validation_alias="JWT_PRIVATE_KEY")
    public_key: str = Field(validation_alias="JWT_PUBLIC_KEY")
    algorithm: str = Field(
        validation_alias="ALGORITHM",
    )
    access_token_expire_seconds: int = Field(
        validation_alias="ACCESS_TOKEN_EXPIRE_SECONDS"
    )
    refresh_token_expire_seconds: int = Field(
        validation_alias="REFRESH_TOKEN_EXPIRE_SECONDS"
    )


# --- Main Settings ---
class Settings(CommonSettings):
    postgres: PostgresSettings = Field(
        default_factory=PostgresSettings,
    )

    redis: RedisSettings = Field(
        default_factory=RedisSettings,
    )

    app: AppSettings = Field(
        default_factory=AppSettings,
    )

    jwt: JwtSettings = Field(
        default_factory=JwtSettings,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
