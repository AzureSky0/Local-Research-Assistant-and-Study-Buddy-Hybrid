from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Local Research Assistant and Study Buddy Hybrid"
    app_version: str = "0.1.0"

    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()