from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SolarInspect AI API"
    api_prefix: str = "/api/v1"
    storage_root: Path = Path("storage")
    max_upload_files: int = 50
    min_upload_files: int = 5
    cors_origins: list[str] = ["*"]

    model_config = SettingsConfigDict(env_prefix="SOLARINSPECT_")


settings = Settings()
