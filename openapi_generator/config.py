"""Configuration management for OpenAPI generator."""

import logging
import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Anthropic API Configuration
    anthropic_api_key: str = Field(
        description="Anthropic API key for Claude",
        validation_alias="ANTHROPIC_API_KEY",
    )
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model to use",
        validation_alias="ANTHROPIC_MODEL",
    )

    # Timeout Settings (seconds)
    request_timeout: int = Field(
        default=60,
        description="Timeout for HTTP requests",
        validation_alias="REQUEST_TIMEOUT",
    )
    llm_timeout: int = Field(
        default=120,
        description="Timeout for LLM API calls",
        validation_alias="LLM_TIMEOUT",
    )

    # Rate Limiting
    max_concurrent_requests: int = Field(
        default=5,
        description="Maximum concurrent HTTP requests",
        validation_alias="MAX_CONCURRENT_REQUESTS",
    )
    max_concurrent_llm_calls: int = Field(
        default=3,
        description="Maximum concurrent LLM API calls",
        validation_alias="MAX_CONCURRENT_LLM_CALLS",
    )
    rate_limit_delay: float = Field(
        default=1.0,
        description="Delay between requests (seconds)",
        validation_alias="RATE_LIMIT_DELAY",
    )

    # Crawling Configuration
    max_pages_per_site: int = Field(
        default=50,
        description="Maximum pages to crawl per site",
        validation_alias="MAX_PAGES_PER_SITE",
    )
    max_depth: int = Field(
        default=3,
        description="Maximum crawl depth",
        validation_alias="MAX_DEPTH",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        validation_alias="LOG_LEVEL",
    )

    # Output Configuration
    output_dir: Path = Field(
        default=Path("output"),
        description="Directory for output files",
        validation_alias="OUTPUT_DIR",
    )

    # User Agent
    user_agent: str = Field(
        default="OpenAPI-Generator-Bot/1.0 (Educational Project)",
        description="User agent for HTTP requests",
        validation_alias="USER_AGENT",
    )

    # Caching Configuration
    enable_http_cache: bool = Field(
        default=True,
        description="Enable HTTP response caching",
        validation_alias="ENABLE_HTTP_CACHE",
    )
    enable_llm_cache: bool = Field(
        default=True,
        description="Enable LLM result caching",
        validation_alias="ENABLE_LLM_CACHE",
    )
    cache_dir: Path = Field(
        default=Path(".cache"),
        description="Directory for cache files",
        validation_alias="CACHE_DIR",
    )
    cache_ttl: int = Field(
        default=86400,
        description="Cache time-to-live in seconds (default: 24 hours)",
        validation_alias="CACHE_TTL",
    )

    # Discovery Configuration
    force_doc_urls: Optional[str] = Field(
        default=None,
        description="Comma-separated list of documentation URLs to use (bypasses discovery)",
        validation_alias="FORCE_DOC_URLS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def setup_logging(self) -> None:
        """Configure logging based on settings."""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore
        _settings.setup_logging()
        _settings.ensure_output_dir()
    return _settings


def reset_settings() -> None:
    """Reset settings instance (useful for testing)."""
    global _settings
    _settings = None
