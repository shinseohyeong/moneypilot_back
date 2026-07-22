from app.rag.vector_store import search_documents, get_rag_collection

collection = get_rag_collection()

print("문서 수:", collection.count())

print(collection.get(ids=["19"]))

result = search_documents(
    "20대 사회초년생에게 적합한 예금 상품 추천해줘",
    top_k=3,
)


print(result)