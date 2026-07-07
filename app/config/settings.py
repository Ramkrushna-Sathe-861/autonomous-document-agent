"""
Configuration module using Pydantic Settings v2.

Purpose: Centralized configuration management with environment variable validation.
Responsibility: Load, validate, and provide access to all application settings.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


class Settings(BaseSettings):
    """Application configuration with environment variable support."""

    # API Configuration
    api_title: str = "Autonomous Document Generation Agent"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    # Groq LLM Configuration
    groq_api_key: str = Field(default="", repr=False)
    groq_model: str = DEFAULT_GROQ_MODEL
    groq_timeout: int = 60
    groq_max_retries: int = 5

    # Paths Configuration
    base_dir: Path = Path(__file__).parent.parent.parent
    output_dir: Path = Path("output")
    templates_dir: Path = Path("templates")
    logs_dir: Path = Path("logs")

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "standard"
    log_file: str = "app.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5

    # Agent Configuration
    planner_model: str = DEFAULT_GROQ_MODEL
    executor_model: str = DEFAULT_GROQ_MODEL
    reflection_model: str = DEFAULT_GROQ_MODEL
    max_planning_retries: int = 2
    max_execution_retries: int = 2

    # Document Configuration
    document_author: str = "Autonomous Document Agent"
    document_company: str = "AI Systems"
    document_font_name: str = "Calibri"
    document_font_size: int = 11

    # Validation Configuration
    max_document_sections: int = 50
    min_document_length: int = 100
    max_document_length: int = 50000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def get_output_path(self) -> Path:
        """Get absolute output directory path."""
        if self.output_dir.is_absolute():
            return self.output_dir
        return self.base_dir / self.output_dir

    def get_templates_path(self) -> Path:
        """Get absolute templates directory path."""
        if self.templates_dir.is_absolute():
            return self.templates_dir
        return self.base_dir / self.templates_dir

    def get_logs_path(self) -> Path:
        """Get absolute logs directory path."""
        if self.logs_dir.is_absolute():
            return self.logs_dir
        return self.base_dir / self.logs_dir


def get_settings() -> Settings:
    """Factory function to get settings instance."""
    return Settings()
