from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    internal_api_key: str
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    chroma_persist_dir: str = "./data/chroma"

    # 인제스트 배치 전용 — 실시간 요청 경로에서는 쓰지 않는다.
    # (docs/AI_SERVICE_CONTRACT.md 5번: 인제스트만 예외적으로 MySQL 직접 읽기 허용)
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "drjudge"
    mysql_password: str = ""
    mysql_database: str = "drjudge"


settings = Settings()
