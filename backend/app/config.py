import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
	app_name: str = os.getenv("APP_NAME", "FinVault AI")
	env: str = os.getenv("ENV", "development")
	log_level: str = os.getenv("LOG_LEVEL", "INFO")
	groq_api_key: str = os.getenv("GROQ_API_KEY", "")
	groq_quick_model: str = os.getenv("GROQ_QUICK_MODEL", "llama-3.1-8b-instant")
	groq_deep_model: str = os.getenv("GROQ_DEEP_MODEL", "llama-3.3-70b-versatile")
	qdrant_url: str = os.getenv("QDRANT_URL", "")
	qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
	database_url: str = os.getenv("DATABASE_URL", "")


settings = Settings()
