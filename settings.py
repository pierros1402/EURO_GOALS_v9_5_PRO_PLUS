# app/core/settings.py
from pydantic import BaseSettings, AnyHttpUrl
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "EURO_GOALS_UNIFIED"
    ENV: str = "development"

    # SmartMoney toggles
    SMARTMONEY_ENABLED: bool = True
    SMARTMONEY_REFRESH_INTERVAL: int = 60  # seconds
    SMARTMONEY_CACHE_TTL: int = 45  # seconds

    # Providers (placeholders)
    PROVIDER_ODDS_API_URL: Optional[AnyHttpUrl] = None
    PROVIDER_ODDS_API_KEY: Optional[str] = None

    PROVIDER_MARKET_DEPTH_API_URL: Optional[AnyHttpUrl] = None
    PROVIDER_MARKET_DEPTH_API_KEY: Optional[str] = None

    # Health / Render
    RENDER_HEALTH_URL: Optional[AnyHttpUrl] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
