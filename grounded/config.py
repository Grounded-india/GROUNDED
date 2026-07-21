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

    # --- Layer 2: embeddings, clustering, ranking ---
    # "auto" picks voyage when a real VOYAGE_API_KEY is present, else the
    # offline local backend. Force one with EMBEDDING_BACKEND=voyage|local.
    embedding_backend: str = Field(default="auto", alias="EMBEDDING_BACKEND")
    embedding_model: str = Field(default="voyage-3", alias="EMBEDDING_MODEL")

    # Cluster two items together when cosine similarity is at least this and
    # they fall within the time window (hours) of each other.
    cluster_similarity: float = Field(default=0.80, alias="CLUSTER_SIMILARITY")
    cluster_window_hours: float = Field(default=48.0, alias="CLUSTER_WINDOW_HOURS")

    # How many top events advance to Layer 3 per ranking run.
    select_top_n: int = Field(default=30, alias="SELECT_TOP_N")

    def has_voyage_key(self) -> bool:
        key = (self.voyage_api_key or "").strip()
        return bool(key) and "..." not in key


settings = Settings()
