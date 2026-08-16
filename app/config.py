from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Discord Credentials
    DISCORD_APP_ID: str = ""
    DISCORD_PUBLIC_KEY: str = ""
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_GUILD_ID: Optional[str] = None

    # Google GenAI / GCP
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_CLOUD_LOCATION: str = "global"

    # Models & Thinking Configuration
    ORCHESTRATOR_MODEL: str = "gemini-3.5-flash-lite"
    EXPERT_MODEL: str = "gemini-3.5-flash-lite"
    THINKING_BUDGET: Optional[int] = None
    THINKING_LEVEL: Optional[str] = None

    # API Tokens
    NYC_SOCRATA_APP_TOKEN: Optional[str] = None
    NYPL_API_TOKEN: Optional[str] = None

    # Server & Web config
    PORT: int = 8080
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["*"]

    # Security & Protection
    FRONTEND_API_KEY: Optional[str] = None  # If set, enforces X-API-Key or Bearer token on /api/v1
    RATE_LIMIT_PER_MINUTE: int = 60         # IP-based sliding window rate limit

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
