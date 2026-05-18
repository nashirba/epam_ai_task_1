from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # LLM
    llm_model: str = "gemini/gemini-2.0-flash"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 768
    llm_num_retries: int = 3

    # Embeddings
    embedding_provider: Literal["openai", "gemini", "local"] = "local"
    embedding_model: str = "BAAI/bge-m3"

    # Weaviate
    weaviate_host: str = "localhost"
    weaviate_http_port: int = 8080
    weaviate_grpc_port: int = 50051

    # MCP
    tavily_api_key: str | None = None
    kz_data_mcp_path: str = "src/pia/mcp/server.py"

    # Observability
    langfuse_host: str = "https://cloud.langfuse.com"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None

    # App
    debug: bool = False
    data_dir: Path = Field(default=Path("./data"))
    rate_limit_per_minute: int = 10


def get_settings() -> Settings:
    """Singleton-ish accessor — Streamlit reloads import this."""
    return Settings()  # type: ignore[call-arg]
