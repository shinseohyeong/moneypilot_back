# .env 읽기, DB URL, JWT 설정, OAuth 설정
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

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
    
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    FINANCE_API_KEY: str = os.getenv("FINANCE_API_KEY", "")
    PUBLIC_DATA_API_KEY: str =os.getenv("PUBLIC_DATA_API_KEY", "")


    # ── JWT (1번 담당 추가) ──────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ── OAuth (1번 담당 추가) ──────────────────
    # 구글
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")

    # 카카오
    KAKAO_CLIENT_ID: str = os.getenv("KAKAO_CLIENT_ID", "")
    KAKAO_CLIENT_SECRET: str = os.getenv("KAKAO_CLIENT_SECRET", "")
    KAKAO_REDIRECT_URI: str = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/api/auth/kakao/callback")
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

    # Ollama 설정
    ollama_base_url: str = (
        os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434",
        )
        or "http://localhost:11434"
    ).strip()

    ollama_llm_model: str = (
        os.getenv(
            "OLLAMA_LLM_MODEL",
            "gemma4:e4b-it-qat",
        )
        or "gemma4:e4b-it-qat"
    ).strip()

    ollama_embedding_model: str = (
        os.getenv(
            "OLLAMA_EMBEDDING_MODEL",
            "bge-m3:latest",
        )
        or "bge-m3:latest"
    ).strip()

    # YouTube API
    youtube_api_key: str = (os.getenv("YOUTUBE_API_KEY") or "").strip()

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4"
        )
    
    class Config:
        env_file=".env"


settings = Settings()