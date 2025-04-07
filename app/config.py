import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from functools import lru_cache

# Load environment variables
load_dotenv()

# Configuration
class Settings(BaseSettings):
    # API Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10MB max file size

    # Model Configuration
    DEFAULT_MODEL_TYPE: str = "gemini"  # Default model type (gemini, openai, ollama)

    # API Keys
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Default model name

    # Supported MIME Types
    SUPPORTED_MIME_TYPES: list[str] = [
        "image/jpeg", "image/png", "image/tiff",
        "application/pdf"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 