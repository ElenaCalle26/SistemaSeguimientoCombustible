from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = 'postgresql+psycopg://combustible_user:cambia_esta_clave@localhost:5432/combustible_db'
    secret_key: str = 'development-only-change-me'
    access_token_expire_minutes: int = 480
    cors_origins: str = 'http://localhost:5173'
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    alert_recipient: str | None = None
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

@lru_cache
def get_settings() -> Settings:
    return Settings()
