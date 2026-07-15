# ============================================================
# 파일 위치: app/schemas/stock_rag_schema.py
# 역할:
#   - 주식/경제 RAG 인덱싱 및 검색 API의 요청/응답 schema를 정의합니다.
# ============================================================

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StockRagBuildRequest(BaseModel):
    """
    RAG 문서 인덱싱 요청 schema입니다.
    """

    news_limit: int = Field(default=100, ge=1, le=500)
    sector_limit: int = Field(default=50, ge=1, le=200)
    rebuild: bool = Field(
        default=True,
        description="기존 vector store를 삭제하고 다시 만들지 여부",
    )


class StockRagBuildResponse(BaseModel):
    """
    RAG 문서 인덱싱 응답 schema입니다.
    """

    collection_name: str
    indexed_count: int
    message: str


class StockRagSearchItem(BaseModel):
    """
    RAG 검색 결과 item schema입니다.
    """

    source_type: str
    source_id: str
    title: Optional[str] = None
    content: str
    score: Optional[float] = None
    metadata: Dict[str, Any] = {}


class StockRagSearchResponse(BaseModel):
    """
    RAG 검색 응답 schema입니다.
    """

    query: str
    top_k: int
    total_count: int
    results: List[StockRagSearchItem]

class StockCommonRagBuildResponse(BaseModel):
    success: bool
    domain: str

    news_document_count: int = 0
    sector_document_count: int = 0

    indexed_document_count: int = 0
    indexed_chunk_count: int = 0

    failed_document_keys: List[str] = Field(
        default_factory=list,
    )

    message: str