import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# ===== Совместимость со старым кодом =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///mycost.db")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Tashkent")
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "UZS")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
VISION_MODEL = os.getenv("VISION_MODEL", "gemini-2.5-flash")


@dataclass
class Settings:
    bot_token: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None
    database_url: str = DATABASE_URL
    timezone: str = TIMEZONE
    default_currency: str = DEFAULT_CURRENCY
    debug: bool = DEBUG
    vision_model: str = VISION_MODEL


def get_settings() -> Settings:
    return Settings(
        bot_token=BOT_TOKEN,
        openai_api_key=OPENAI_API_KEY,
        gemini_api_key=GEMINI_API_KEY,
        database_url=DATABASE_URL,
        timezone=TIMEZONE,
        default_currency=DEFAULT_CURRENCY,
        debug=DEBUG,
        vision_model=VISION_MODEL,
    )


settings = get_settings()

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")