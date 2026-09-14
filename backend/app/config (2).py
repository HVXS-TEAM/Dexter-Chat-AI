from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Dexter Chat AI"
    debug: bool = True

    db_user: str = "dexter"
    db_password: str = "dexter_dev"
    db_name: str = "dexter"
    db_host: str = "localhost"
    db_port: int = 5432
    db_url: str = ""
    db_echo: bool = False

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model_classification: str = "qwen/qwen3.8-27b"
    llm_model_generation: str = "openai/gpt-oss-120b"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.db_url:
            self.db_url = (
                f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )


settings = Settings()
