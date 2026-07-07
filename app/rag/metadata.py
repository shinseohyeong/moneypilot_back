# app/rag/metadata.py

RAG_COLLECTION_NAME = "finance_agent_rag"
CHROMA_DB_PATH = "./chroma_db"


class RagDomain:
    FINANCE_PROFILE = "finance_profile"
    SPENDING = "spending"
    PRODUCT = "product"
    STOCK_NEWS = "stock_news"
    POLICY = "policy"


class RagSourceType:
    FINANCE_PROFILE = "finance_profile"
    MONTHLY_REPORT = "monthly_report"
    PRODUCT = "product"
    NEWS = "news"
    DISCLAIMER = "disclaimer"


class RagCreatedBy:
    SYSTEM = "system"
    USER = "user"