"""Application Settings.

This module contains application-wide settings and configuration
loaded from environment variables and config files.
"""

import logging
from typing import Any

from dotenv import load_dotenv
from pydantic import Field, validator
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables with validation."""

    # Required settings
    OPENAI_API_KEY: str = Field(..., min_length=20, description="OpenAI API key")
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        ..., min_length=20, description="Supabase service role key"
    )
    RAPIDAPI_KEY: str = Field(
        ..., min_length=10, description="RapidAPI key for API-Football"
    )

    # OpenAI Configuration
    openai_model: str = Field(default="gpt-4-turbo", description="OpenAI model to use")

    # FastAPI Configuration
    fastapi_host: str = Field(default="127.0.0.1", description="FastAPI host")
    fastapi_port: int = Field(default=8000, ge=1, le=65535, description="FastAPI port")
    fastapi_reload: bool = Field(default=False, description="FastAPI reload mode")

    # Chainlit Configuration
    chainlit_host: str = Field(default="127.0.0.1", description="Chainlit host")
    chainlit_port: int = Field(
        default=8001, ge=1, le=65535, description="Chainlit port"
    )

    # Environment Configuration
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")

    # API Configuration
    api_football_base_url: str = Field(
        default="https://api-football-v1.p.rapidapi.com/v3",
        description="API-Football base URL",
    )

    @validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v: str) -> str:  # noqa: N805
        if not v or v == "your-openai-api-key" or v == "sk-...":
            raise ValueError("Valid OpenAI API key is required")
        if not v.startswith("sk-"):
            raise ValueError('OpenAI API key must start with "sk-"')
        return v

    @validator("SUPABASE_URL")
    def validate_supabase_url(cls, v: str) -> str:  # noqa: N805
        if not v.startswith("https://"):
            raise ValueError("Supabase URL must be a valid HTTPS URL")
        if not v.endswith(".supabase.co"):
            raise ValueError("Supabase URL must end with .supabase.co")
        return v

    @validator("environment")
    def validate_environment(cls, v: str) -> str:  # noqa: N805
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:  # noqa: N805
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return v_upper

    @validator("log_format")
    def validate_log_format(cls, v: str) -> str:  # noqa: N805
        allowed = ["json", "text"]
        if v not in allowed:
            raise ValueError(f"Log format must be one of: {allowed}")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive values)."""
        return {
            "openai_model": self.openai_model,
            "fastapi_host": self.fastapi_host,
            "fastapi_port": self.fastapi_port,
            "fastapi_reload": self.fastapi_reload,
            "chainlit_host": self.chainlit_host,
            "chainlit_port": self.chainlit_port,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "debug": self.debug,
            "environment": self.environment,
            "api_football_base_url": self.api_football_base_url,
        }

    class Config:
        """Pydantic configuration for Settings model."""

        env_file = ".env"
        case_sensitive = True
        # Allow extra fields for forward compatibility
        extra = "ignore"


# Global settings instance
settings: Settings | None = None

try:
    settings = Settings()  # type: ignore[call-arg]
    logger.info("Settings loaded successfully")
except Exception as e:
    logger.error(f"Failed to load settings: {e}")
    # In development, we might not have all environment variables set
    # This allows the module to be imported for testing
    if __name__ != "__main__":
        settings = None
    else:
        raise


def get_settings() -> Settings:
    """Get the global settings instance."""
    if settings is None:
        raise RuntimeError(
            "Settings not loaded. Please ensure all required environment variables are set."
        )
    return settings
