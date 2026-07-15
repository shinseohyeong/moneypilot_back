# ============================================================
# 파일 위치: app/routers/stock_rag_router.py
# 역할:
#   - 주식/경제 RAG 인덱싱 및 검색 API를 정의합니다.
# ============================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.stock_rag_schema import (
    StockRagBuildRequest,
    StockRagBuildResponse,
    StockRagSearchResponse,
    StockCommonRagBuildResponse,
)
from app.services.stock_rag_service import StockRagService
from app.rag.ingestors.stock_news_ingestor import (
    ingest_stock_news_documents,
)


router = APIRouter()


def get_stock_rag_service(
    db: Session = Depends(get_db),
) -> StockRagService:
    """
    StockRagService 의존성 주입 함수입니다.
    """
    return StockRagService(db)


@router.post(
    "/stock/build",
    response_model=StockRagBuildResponse,
    summary="주식/경제 RAG 인덱스 생성",
)
def build_stock_rag_index(
    request: StockRagBuildRequest,
    service: StockRagService = Depends(get_stock_rag_service),
) -> StockRagBuildResponse:
    """
    뉴스 요약과 섹터 인사이트를 vector store에 저장합니다.
    """
    return service.build_index(request)


@router.get(
    "/stock/search",
    response_model=StockRagSearchResponse,
    summary="주식/경제 RAG 검색",
)
def search_stock_rag(
    query: str = Query(..., description="검색 질문"),
    top_k: int = Query(default=5, ge=1, le=10),
    service: StockRagService = Depends(get_stock_rag_service),
) -> StockRagSearchResponse:
    """
    사용자 질문과 관련된 뉴스 요약/섹터 인사이트 문서를 검색합니다.
    """
    return service.search(
        query=query,
        top_k=top_k,
    )

@router.post(
    "/stock/common/build",
    response_model=StockCommonRagBuildResponse,
    summary="공통 Agent용 주식/뉴스 RAG 인덱싱",
)
def build_common_stock_rag_index(
    request: StockRagBuildRequest,
    db: Session = Depends(get_db),
) -> StockCommonRagBuildResponse:
    """
    DB의 뉴스 요약과 섹터 인사이트를
    팀 공통 Agent RAG 컬렉션에 저장합니다.
    """

    result = ingest_stock_news_documents(
        db=db,
        news_limit=request.news_limit,
        sector_limit=request.sector_limit,
    )

    return StockCommonRagBuildResponse(
        **result,
    )