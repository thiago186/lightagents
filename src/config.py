from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Base settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # Change made here
    )
    GCP_PROJECT_ID: Optional[str] = None
    GCP_REGION: Optional[str] = None
    AWS_ACCESS_KEY: Optional[str] = None
    AWS_SECRET_KEY: Optional[str] = None


appSettings = AppSettings()  # type: ignore
print(appSettings)
