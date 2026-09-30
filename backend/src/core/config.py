"""Application settings loaded from environment variables / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://baa:changeme@postgres:5432/baa"
    log_level: str = "INFO"
    fuzzy_match_threshold: int = 88
    corps_canada_api_key: str = ""
    bc_orgbook_base_url: str = "https://orgbook.gov.bc.ca/api/v4"
    crawl_user_agent: str = "baa-pipeline/0.1"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
