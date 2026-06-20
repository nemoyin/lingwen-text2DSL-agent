"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Lingwen application.

    All settings are loaded from environment variables with the LINGWEN_ prefix.
    """

    model_config = {
        "env_prefix": "LINGWEN_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "lingwen"
    db_password: str = "lingwen123"
    db_name: str = "lingwen_metadata"

    # LLM
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_embed_model: str = "deepseek-embed"

    # Embedding provider (may differ from LLM provider)
    embed_api_key: str = ""         # override for embedding API key
    embed_base_url: str = ""        # override for embedding base URL (defaults to DeepSeek if empty)

    # ChromaDB
    chroma_dir: str = "data/chromadb"

    # JWT
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 480

    @property
    def db_url(self) -> str:
        """Synchronous database URL for Alembic and other sync operations."""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def async_db_url(self) -> str:
        """Asynchronous database URL for SQLAlchemy async engine."""
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
