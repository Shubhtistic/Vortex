from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # our app info
    PROJECT_NAME: str = "Vortex Telemetry Engine"
    VERSION: str = "0.1.0"

    # database url
    # our appp wiill crash without this
    DATABASE_URL: str

    REDIS_URL: str

    class Config:
        # Tell Pydantic to read the file named .env
        env_file = ".env"


# Instantiate the settings once to be imported everywhere
settings = Settings()
