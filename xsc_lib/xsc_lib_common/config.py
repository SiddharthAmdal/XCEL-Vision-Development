import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    RING_CLIENT_ID: str
    RING_CLIENT_SECRET: str
    RING_HMAC_SECRET: str
    RING_ENCRYPTION_KEY: str
    RING_DEVICE_CACHE_TTL_SECONDS: int = 300
    
    # Optional tunnel base URL for redirect URIs (e.g., https://abc.ngrok-free.app)
    BASE_URL: str = "http://localhost:8000"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
