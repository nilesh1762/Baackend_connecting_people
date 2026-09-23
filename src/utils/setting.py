import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_USERNAME : str =""
    DB_PASSWORD : str =""
    DB_DSN : str = ""
    SECRET_KEY : str = ""
    ALGORITHM : str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES : int = 0

    REDIS_HOST : str = "localhost"
    REDIS_PORT : int = 6379
    
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('ENVIRONMENT', 'local')}",
        extra="ignore",         # Safely bypasses extra validation failures
        case_sensitive=False    # Maps UPPERCASE env keys seamlessly to your fields
    )  


@lru_cache
def get_settings():
    return Settings()

# Instantiate a single global instance for other scripts to call directly
settings = get_settings()
