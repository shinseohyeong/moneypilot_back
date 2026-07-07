# app/rag/embeddings.py

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv(
    "OPENAI_EMBEDDING_MODEL",
    "text-embedding-3-small",
)

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

client = OpenAI(api_key=OPENAI_API_KEY)


def embed_text(text: str) -> list[float]:
    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("임베딩할 텍스트가 비어 있습니다.")

    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=cleaned_text,
    )

    return response.data[0].embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    cleaned_texts = [
        text.strip()
        for text in texts
        if text and text.strip()
    ]

    if not cleaned_texts:
        return []

    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=cleaned_texts,
    )

    return [item.embedding for item in response.data]