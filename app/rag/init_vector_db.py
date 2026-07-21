from app.core.database import SessionLocal

from app.rag.builders.document_builder import (
    build_financial_documents
)

from app.rag.vector_store import (
    save_documents, get_rag_collection
)

db = SessionLocal()

documents = build_financial_documents(db)

print("문서 개수:", len(documents))
print(documents[0]["content"])

save_documents(documents)

collection = get_rag_collection()

print("문서 수:", collection.count())

result = collection.get(ids=["19"])
print(result)