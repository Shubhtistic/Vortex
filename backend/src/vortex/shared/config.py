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

    environment: str = Field(
        validation_alias="ENVIRONMENT",
    )

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


# --- Project Settings ---
class ProjectSettings(CommonSettings):

    api_key_prefix: str = Field(
        validation_alias="API_KEY_PREFIX",
    )

    grace_period_mins: int = Field(validate_alias="GRACE_PERIOD_MINS")


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


# --- CORS ---
class CORSSettings(CommonSettings):

    allowed_origins: list[str] = Field(
        validation_alias="ALLOWED_ORIGINS",
    )

    allowed_methods: list[str] = Field(
        validation_alias="ALLOWED_METHODS",
    )

    allowed_headers: list[str] = Field(
        validation_alias="ALLOWED_HEADERS",
    )

    allow_credentials: bool = Field(
        validation_alias="ALLOW_CREDENTIALS",
    )

    max_age: int = Field(
        validation_alias="CORS_MAX_AGE",
    )


# --- Redpanda ---
class RedpandaSettings(CommonSettings):

    bootstrap_servers: str = Field(
        default="localhost:9092",
        validation_alias="REDPANDA_BOOTSTRAP_SERVERS",
    )

    client_id: str = Field(
        default="vortex",
        validation_alias="REDPANDA_CLIENT_ID",
    )

    security_protocol: str = Field(
        default="PLAINTEXT",
        validation_alias="REDPANDA_SECURITY_PROTOCOL",
    )

    request_timeout_ms: int = Field(
        default=40_000,
        validation_alias="REDPANDA_REQUEST_TIMEOUT_MS",
    )

    max_batch_size: int = Field(
        default=16_384,
        validation_alias="REDPANDA_MAX_BATCH_SIZE",
    )

    events_topic: str = Field(
        default="vortex.events",
        validation_alias="REDPANDA_EVENTS_TOPIC",
    )

    consumer_group_id: str = Field(
        validation_alias="REDPANDA_CONSUMER_GROUP_ID",
    )

    start_max_attempts: int = Field(
        default=5,
        validation_alias="REDPANDA_START_MAX_ATTEMPTS",
    )

    send_timeout_seconds: float = Field(
        default=10.0,
        validation_alias="REDPANDA_SEND_TIMEOUT_SECONDS",
    )

    sasl_mechanism: str = Field(
        default="PLAIN",
        validation_alias="REDPANDA_SASL_MECHANISM",
    )

    sasl_username: Optional[str] = Field(
        default=None,
        validation_alias="REDPANDA_SASL_USERNAME",
    )

    sasl_password: Optional[str] = Field(
        default=None,
        validation_alias="REDPANDA_SASL_PASSWORD",
    )


# --- Main Settings ---
class Settings(CommonSettings):

    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    jwt: JwtSettings = Field(default_factory=JwtSettings)
    project: ProjectSettings = Field(default_factory=ProjectSettings)
    cors: CORSSettings = Field(default_factory=CORSSettings)
    redpanda: RedpandaSettings = Field(default_factory=RedpandaSettings)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
