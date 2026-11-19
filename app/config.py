from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/chat_app_db"
    chat_api_key: str = "change-me"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None
    cors_origins: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    max_history_messages: int = 20
    rate_limit_messages: int = 20
    rate_limit_window_seconds: int = 3600
    input_cost_per_1m: float = 0.15
    output_cost_per_1m: float = 0.60
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
