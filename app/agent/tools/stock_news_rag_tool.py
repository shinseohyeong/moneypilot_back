# ============================================================
# 파일 위치: app/agent/tools/stock_news_rag_tool.py
# 역할:
#   - 팀 공통 RAG에서 주식 뉴스와 섹터 인사이트를 검색합니다.
#   - "내 관심종목" 질문이면 로그인 사용자의 관심종목명을
#     검색 query에 추가합니다.
# ============================================================

from sqlalchemy.orm import Session

from app.rag.metadata import RagDomain
from app.rag.rag_service import (
    search_rag_documents,
)
from app.repositories.stock_report_repository import (
    StockReportRepository,
)

import logging # 디버깅용

logger = logging.getLogger(__name__)


WATCHLIST_QUERY_KEYWORDS = (
    "관심종목",
    "관심 종목",
    "내 종목",
    "내 주식",
)


def _list_watchlist_stock_names(
    db: Session,
    user_id: int,
) -> list[str]:
    """
    로그인 사용자의 관심종목명을 조회합니다.
    """

    repository = StockReportRepository(db)

    watchlist_rows = (
        repository.list_user_watchlist_stocks(
            user_id=user_id,
        )
    )

    stock_names: list[str] = []

    for row in watchlist_rows:
        stock = row[1]

        stock_name = getattr(
            stock,
            "stock_name",
            None,
        )

        if stock_name:
            stock_names.append(
                str(stock_name)
            )

    # 중복 제거
    return list(
        dict.fromkeys(stock_names)
    )


def _build_stock_news_search_query(
    db: Session,
    user_id: int,
    query: str,
) -> tuple[str, list[str]]:
    """
    관심종목 질문이면 사용자의 관심종목명을
    RAG 검색어에 추가합니다.
    """

    normalized_query = query.strip()

    if not _is_watchlist_question(normalized_query):
        return normalized_query, []

    stock_names = _list_watchlist_stock_names(
        db=db,
        user_id=user_id,
    )

    if not stock_names:
        return normalized_query, []

    search_query = (
        f"{normalized_query}\n"
        f"사용자 관심종목: "
        f"{', '.join(stock_names[:10])}"
    )

    return search_query, stock_names


def search_stock_news_rag_tool(
    db: Session,
    user_id: int,
    query: str,
) -> dict:
    """
    주식 뉴스와 섹터 인사이트 RAG 문서를 검색합니다.
    """

    is_watchlist_question = (
        _is_watchlist_question(query)
    )

    search_query, watchlist_stock_names = (
        _build_stock_news_search_query(
            db=db,
            user_id=user_id,
            query=query,
        )
    )

    if (
        is_watchlist_question
        and not watchlist_stock_names
    ):
        return {
            "success": False,
            "documents": [],
            "data": None,
            "message": (
                "현재 로그인한 사용자에게 "
                "등록된 관심종목이 없습니다. "
                "관심종목을 먼저 등록해주세요."
            ),
        }

    result = search_rag_documents(
        query=search_query,
        user_id=None,
        domain=RagDomain.STOCK_NEWS,
        n_results=5,
    )

    if not result.get("success"):
        return {
            "success": False,
            "documents": [],
            "data": None,
            "message": (
                "관련 주식 뉴스 또는 "
                "섹터 인사이트를 찾지 못했습니다."
            ),
        }

    data = result.get("data") or {}

    data["original_query"] = query
    data["search_query"] = search_query
    data["watchlist_stock_names"] = (
        watchlist_stock_names
    )

    return {
        "success": True,
        "documents": result.get(
            "documents",
            [],
        ),
        "data": data,
        "message": (
            "관련 주식 뉴스와 "
            "섹터 인사이트를 검색했습니다."
        ),
    }

def _is_watchlist_question(
    query: str,
) -> bool:
    """
    사용자가 자신의 관심종목을 기준으로 질문했는지 판단합니다.
    """

    normalized_query = query.strip()

    return any(
        keyword in normalized_query
        for keyword in WATCHLIST_QUERY_KEYWORDS
    )