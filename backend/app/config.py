"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = backend/app/config.py -> parents[0]=app, [1]=backend, [2]=root.
# Resolved from the file location so the app works whatever the CWD is
# (native run from backend/ or from the project root).
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Runtime configuration for the Dexter backend.

    Values are read from environment variables (or the root ``.env`` file).
    """

    model_config = SettingsConfigDict(env_file=_ENV_FILE, env_file_encoding="utf-8")

    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    db_url: str = ""
    jwt_secret: str = ""
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_model_generation: str = "openai/gpt-oss-120b"
    llm_api_key_cerebras: str = ""
    llm_api_key_sambanova: str = ""
    embedding_model: str = "intfloat/multilingual-e5-small"
    rag_min_score: float = 0.5
    rag_max_chunks: int = 5
    upload_dir: str = "uploads"


settings = Settings()
