import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    DB_USERNAME : str
    DB_PASSWORD : str
    DB_DSN : str

    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str

    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('ENVIRONMENT', 'local')}",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 🔍 This completely silences the extra_forbidden validation crashes
    ) 
@lru_cache
def get_settings():
    return Settings()

# Instantiate a single global instance for other scripts to call directly
settings = get_settings()
