# app/rag/chunkers.py

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])

        if end >= text_length:
            break

        start = end - overlap

    return chunks