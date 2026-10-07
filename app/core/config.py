from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import APP_NAME, APP_VERSION


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = APP_NAME
    app_version: str = APP_VERSION

    # Detailed logs for development: set DEBUG=true in a .env file.
    debug: bool = False


settings = Settings()
