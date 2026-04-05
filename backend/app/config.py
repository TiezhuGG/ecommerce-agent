from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "Ecommerce Agent API"
    app_env: str = "development"
    frontend_origin: str = "http://127.0.0.1:5173"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None
    openai_api_style: str = "auto"

    # 这里把 env 文件路径固定到 backend/.env，避免你从不同目录启动时读不到配置。
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )


settings = Settings()
