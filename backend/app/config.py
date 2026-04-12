from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "Ecommerce Agent API"
    app_env: str = "development"
    frontend_origin: str = "http://127.0.0.1:5173"
    database_url: str = ""
    admin_access_code: str = ""

    # 这里统一使用“兼容 OpenAI 协议”的配置命名。
    # 这样不管你接 OpenAI 官方、第三方中转网关，还是兼容 OpenAI 接口的国产模型平台，
    # 后端调用层都可以尽量复用同一套代码。
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str | None = None
    openai_api_style: str = "auto"

    # 固定读取 backend/.env，避免从不同工作目录启动时读不到配置。
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )


settings = Settings()
