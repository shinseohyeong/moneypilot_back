# ============================================================
# 파일 위치: app/services/stock_chatbot_intent_service.py
# 역할:
#   - 주식/뉴스 챗봇 질문의 의도를 규칙 기반으로 분류합니다.
#   - 질문에 포함된 관심종목과 섹터명을 추출합니다.
# ============================================================

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class StockChatIntent(str, Enum):
    STOCK_DETAIL = "STOCK_DETAIL"
    MARKET_OVERVIEW = "MARKET_OVERVIEW"
    NEWS_ANALYSIS = "NEWS_ANALYSIS"
    SECTOR_ANALYSIS = "SECTOR_ANALYSIS"
    WATCHLIST = "WATCHLIST"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


@dataclass(frozen=True)
class StockChatIntentResult:
    intent: StockChatIntent
    target_stock_ids: list[int] = field(default_factory=list)
    target_sector_names: list[str] = field(default_factory=list)


class StockChatbotIntentService:
    """
    주식·뉴스 도메인 안에서 질문 유형을 분류합니다.

    1차 MVP에서는 규칙 기반 분류를 사용합니다.
    추후 규칙으로 판단하기 어려운 질문만 LLM 분류로 확장할 수 있습니다.
    """

    OUT_OF_SCOPE_KEYWORDS = (
        "월급",
        "소비",
        "지출",
        "고정비",
        "생활비",
        "카드값",
        "카드 명세서",
        "여유자금",
        "예산",
        "저축액",
    )

    NEWS_KEYWORDS = (
        "뉴스",
        "기사",
        "보도",
        "이슈",
        "호재",
        "악재",
        "위험 뉴스",
        "최근 소식",
    )

    MARKET_KEYWORDS = (
        "시장",
        "증시",
        "코스피",
        "코스닥",
        "시장 흐름",
        "시장 상황",
        "전반적인 흐름",
    )

    WATCHLIST_KEYWORDS = (
        "관심종목",
        "내 종목",
        "저장한 종목",
        "찜한 종목",
    )

    SECTOR_KEYWORDS = {
        "반도체": (
            "반도체",
            "메모리",
            "hbm",
        ),
        "AI": (
            "ai",
            "인공지능",
            "엔비디아",
        ),
        "2차전지": (
            "2차전지",
            "이차전지",
            "배터리",
        ),
        "바이오": (
            "바이오",
            "제약",
            "헬스케어",
        ),
        "금융": (
            "금융",
            "은행",
            "금리",
        ),
    }

    def classify(
        self,
        message: str,
        stock_id: Optional[int],
        watchlist_rows: list,
    ) -> StockChatIntentResult:
        normalized_message = " ".join(message.lower().split())

        # 소비·자산관리 질문은 이 챗봇 담당 범위 밖으로 처리합니다.
        if self._contains_any(
            normalized_message,
            self.OUT_OF_SCOPE_KEYWORDS,
        ):
            return StockChatIntentResult(
                intent=StockChatIntent.OUT_OF_SCOPE,
            )

        mentioned_stock_ids = self._extract_stock_ids(
            message=normalized_message,
            watchlist_rows=watchlist_rows,
        )

        # 상세 페이지에서 stock_id를 전달한 경우 최우선으로 사용합니다.
        if stock_id is not None and stock_id > 0:
            mentioned_stock_ids = [stock_id]

        sector_names = self._extract_sector_names(
            normalized_message,
        )

        if sector_names:
            return StockChatIntentResult(
                intent=StockChatIntent.SECTOR_ANALYSIS,
                target_stock_ids=mentioned_stock_ids,
                target_sector_names=sector_names,
            )

        if mentioned_stock_ids:
            if self._contains_any(
                normalized_message,
                self.NEWS_KEYWORDS,
            ):
                intent = StockChatIntent.NEWS_ANALYSIS
            else:
                intent = StockChatIntent.STOCK_DETAIL

            return StockChatIntentResult(
                intent=intent,
                target_stock_ids=mentioned_stock_ids,
            )

        if self._contains_any(
            normalized_message,
            self.WATCHLIST_KEYWORDS,
        ):
            return StockChatIntentResult(
                intent=StockChatIntent.WATCHLIST,
            )

        if self._contains_any(
            normalized_message,
            self.NEWS_KEYWORDS,
        ):
            return StockChatIntentResult(
                intent=StockChatIntent.NEWS_ANALYSIS,
            )

        if self._contains_any(
            normalized_message,
            self.MARKET_KEYWORDS,
        ):
            return StockChatIntentResult(
                intent=StockChatIntent.MARKET_OVERVIEW,
            )

        # 주식 챗봇에서 애매한 질문은 관심종목 전체 흐름 질문으로 처리합니다.
        return StockChatIntentResult(
            intent=StockChatIntent.MARKET_OVERVIEW,
        )

    def _extract_stock_ids(
        self,
        message: str,
        watchlist_rows: list,
    ) -> list[int]:
        stock_ids = []

        for _, stock in watchlist_rows:
            stock_name = (stock.stock_name or "").lower()
            stock_code = (stock.stock_code or "").lower()

            if stock_name and stock_name in message:
                stock_ids.append(stock.id)
                continue

            if stock_code and stock_code in message:
                stock_ids.append(stock.id)

        return list(dict.fromkeys(stock_ids))

    def _extract_sector_names(
        self,
        message: str,
    ) -> list[str]:
        sector_names = []

        for sector_name, keywords in self.SECTOR_KEYWORDS.items():
            if self._contains_any(message, keywords):
                sector_names.append(sector_name)

        return sector_names

    @staticmethod
    def _contains_any(
        message: str,
        keywords: tuple[str, ...],
    ) -> bool:
        return any(
            keyword.lower() in message
            for keyword in keywords
        )