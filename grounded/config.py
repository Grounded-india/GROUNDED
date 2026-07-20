from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    voyage_api_key: str = Field(default="", alias="VOYAGE_API_KEY")
    database_url: str = Field(alias="DATABASE_URL")

    env: str = Field(default="dev", alias="GROUNDED_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    output_dir: Path = Field(default=Path("./output"), alias="OUTPUT_DIR")


settings = Settings()
