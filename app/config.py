from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Base settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # Change made here
    )
    GCP_PROJECT_ID: str
    GCP_REGION: str
    
    
appSettings = AppSettings() #type: ignore
print(appSettings)
