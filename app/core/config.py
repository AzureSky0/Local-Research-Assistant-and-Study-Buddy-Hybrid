from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import APP_NAME, APP_VERSION


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = APP_NAME
    app_version: str = APP_VERSION

    debug: bool = True


settings = Settings()
