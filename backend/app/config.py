"""
Configuration module for FDA Drug Approval Tracker backend.
Loads settings from environment variables with sensible defaults.
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database settings
    database_url: str = "postgresql://fdauser:fdapassword@localhost:5432/fdatracker"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "fdatracker"
    db_user: str = "fdauser"
    db_password: str = "fdapassword"

    # Backend server settings
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    log_level: str = "INFO"

    # CORS settings
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # FDA scraping settings
    fda_request_delay_seconds: int = 1
    fda_max_retries: int = 3

    @field_validator('allowed_origins')
    @classmethod
    def parse_origins(cls, v: str) -> List[str]:
        """Parse comma-separated origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"


# Global settings instance
settings = Settings()
