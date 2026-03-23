from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # our app info
    PROJECT_NAME: str = "Vortex Telemetry Engine"
    VERSION: str = "0.1.0"

    # database url
    # our app wiill crash without this
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_TEST_DB:str

    REDIS_URL: str

    class Config:
        # Tell Pydantic to read the file named .env
        env_file = ".env"

    @property
    def POSTGRES_URL(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    @property
    def TEST_POSTGRES_URL(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


# Instantiate the settings once to be imported everywhere
settings = Settings()
