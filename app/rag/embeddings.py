import httpx
from ollama import Client, ResponseError

from app.core.config import settings


client = Client(
    host=settings.ollama_base_url.rstrip("/"),
    timeout=300.0,
)


def embed_text(text: str) -> list[float]:
    """
    단일 텍스트를 Ollama bge-m3로 임베딩한다.
    """

    cleaned_text = text.strip()

    if not cleaned_text:
        raise ValueError("임베딩할 텍스트가 비어 있습니다.")

    embeddings = embed_texts([cleaned_text])

    if not embeddings:
        raise RuntimeError("Ollama에서 임베딩을 반환하지 않았습니다.")

    return embeddings[0]


def embed_texts(
    texts: list[str],
) -> list[list[float]]:
    """
    여러 텍스트를 한 번의 요청으로 Ollama에 전달한다.

    문서 청크마다 개별 요청하지 않고 batch로 임베딩한다.
    """

    cleaned_texts = [
        text.strip()
        for text in texts
        if text and text.strip()
    ]

    if not cleaned_texts:
        return []

    try:
        response = client.embed(
            model=settings.ollama_embedding_model,
            input=cleaned_texts,
            keep_alive="30m",
        )

    except ResponseError as exc:
        raise RuntimeError(
            f"Ollama 임베딩 실행에 실패했습니다: {exc.error}"
        ) from exc

    except httpx.TimeoutException as exc:
        raise RuntimeError(
            "Ollama 임베딩 응답 시간이 초과되었습니다."
        ) from exc

    except httpx.ConnectError as exc:
        raise RuntimeError(
            "Ollama 임베딩 서버에 연결할 수 없습니다. "
            f"주소를 확인해주세요: {settings.ollama_base_url}"
        ) from exc

    embeddings = response.embeddings

    if len(embeddings) != len(cleaned_texts):
        raise RuntimeError(
            "요청한 텍스트 수와 반환된 임베딩 수가 다릅니다."
        )

    return [
        list(embedding)
        for embedding in embeddings
    ]