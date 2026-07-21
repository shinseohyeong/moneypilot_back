from app.rag.embeddings import embed_text

result = embed_text(
    "우리은행 WON플러스예금 상품입니다."
)

print(len(result))
print(result[:5])