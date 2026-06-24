# .env 읽기, DB URL, JWT 설정
import os
from pathlib import Path

from dotenv import load_dotenv


# backend 폴더 기준 .env를 명확히 읽기 위한 설정
# config.py 위치: backend/app/core/config.py
# parents[2] => backend/
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

# override=True:
# 이미 터미널 환경변수에 같은 이름이 있어도 .env 값을 우선 사용합니다.
load_dotenv(ENV_PATH, override=True)


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "")

    # 종목 수집
    public_data_stock_service_key: str | None = os.getenv(
        "PUBLIC_DATA_STOCK_SERVICE_KEY"
    )

    # 네이버 뉴스
    naver_client_id: str = (os.getenv("NAVER_CLIENT_ID") or "").strip()
    naver_client_secret: str = (os.getenv("NAVER_CLIENT_SECRET") or "").strip()
    naver_news_base_url: str = (
        os.getenv(
            "NAVER_NEWS_BASE_URL",
            "https://openapi.naver.com/v1/search/news.json",
        )
        or ""
    ).strip()

    # LLM / OpenAI 설정
    llm_provider: str = (os.getenv("LLM_PROVIDER", "openai") or "openai").strip()

    openai_api_key: str = (os.getenv("OPENAI_API_KEY") or "").strip()
    openai_model: str = (os.getenv("OPENAI_MODEL", "gpt-4o-mini") or "").strip()

    # 나중에 Ollama 테스트할 때 사용할 예정
    ollama_base_url: str = (
        os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") or ""
    ).strip()
    ollama_model: str = (os.getenv("OLLAMA_MODEL", "llama3.1") or "").strip()

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )


settings = Settings()