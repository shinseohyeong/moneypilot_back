from app.core.database import SessionLocal
from app.rag.builders.document_builder import build_financial_documents


db = SessionLocal()

try:
    docs = build_financial_documents(db)

    print("문서 개수:", len(docs))

    print("====================")
    print(docs[0])

finally:
    db.close()