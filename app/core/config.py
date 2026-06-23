import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


@dataclass
class Settings:
    bot_token: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    database_url: str = "sqlite:///mycost.db"
    timezone: str = "Asia/Tashkent"
    default_currency: str = "UZS"
    debug: bool = True
    vision_model: str = "gemini-2.5-flash"
    log_level: str = "INFO"


def get_settings() -> Settings:
    return Settings(
        bot_token=os.getenv("BOT_TOKEN"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///mycost.db"),
        timezone=os.getenv("TIMEZONE", "Asia/Tashkent"),
        default_currency=os.getenv("DEFAULT_CURRENCY", "UZS"),
        debug=os.getenv("DEBUG", "True").lower() == "true",
        vision_model=os.getenv("VISION_MODEL", "gemini-2.5-flash"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )