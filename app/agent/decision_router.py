import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from ollama import Client, ResponseError
from pydantic import ValidationError

from app.agent.prompts import AGENT_DECISION_SYSTEM_PROMPT
from app.agent.schemas import AgentDecision
from app.core.config import settings


logger = logging.getLogger(__name__)

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

STOCK_NEWS_FOLLOWUP_KEYWORDS = (
    "뉴스",
    "기사",
    "소식",
    "이슈",
    "호재",
    "악재",
    "긍정",
    "부정",
    "중립",
    "요약",
    "정리",
)

POSITIVE_KEYWORDS = (
    "긍정",
    "호재",
    "좋은 뉴스",
    "좋은 소식",
)

NEGATIVE_KEYWORDS = (
    "부정",
    "악재",
    "위험 뉴스",
    "나쁜 소식",
)

NEUTRAL_KEYWORDS = (
    "중립",
    "중립적",
)

SUMMARY_KEYWORDS = (
    "요약",
    "정리",
    "모아서",
    "전반적인 내용",
    "핵심 내용",
)


def create_ollama_client() -> Client:
    return Client(
        host=settings.ollama_base_url.rstrip("/"),
        timeout=httpx.Timeout(
            connect=10.0,
            read=300.0,
            write=30.0,
            pool=10.0,
        ),
    )

def _normalize_text(
    value: str,
) -> str:
    return " ".join(
        value.lower().split()
    )


def _extract_sector(
    text: str,
) -> str | None:
    """
    현재 문장에서 섹터명을 추출합니다.
    """
    normalized_text = _normalize_text(text)

    for sector_name, keywords in SECTOR_KEYWORDS.items():
        if any(
            keyword.lower() in normalized_text
            for keyword in keywords
        ):
            return sector_name

    return None


def _find_recent_sector(
    history: list[dict] | None,
) -> str | None:
    """
    이전 사용자 질문에서 가장 최근에 언급한
    섹터명을 추출합니다.
    """
    if not history:
        return None

    for item in reversed(history):
        if item.get("role") != "user":
            continue

        content = str(
            item.get("content") or ""
        )

        sector_name = _extract_sector(content)

        if sector_name:
            return sector_name

    return None


def _extract_sentiment(
    message: str,
) -> str | None:
    normalized_message = _normalize_text(message)

    if any(
        keyword in normalized_message
        for keyword in POSITIVE_KEYWORDS
    ):
        return "긍정"

    if any(
        keyword in normalized_message
        for keyword in NEGATIVE_KEYWORDS
    ):
        return "부정"

    if any(
        keyword in normalized_message
        for keyword in NEUTRAL_KEYWORDS
    ):
        return "중립"

    return None


def _is_summary_question(
    message: str,
) -> bool:
    normalized_message = _normalize_text(message)

    return any(
        keyword in normalized_message
        for keyword in SUMMARY_KEYWORDS
    )


def _should_force_stock_news(
    message: str,
    history: list[dict] | None,
) -> bool:
    """
    현재 질문 또는 이전 질문에 주식 섹터 문맥이 있고,
    현재 질문이 뉴스 후속 질문이면 stock_news로 처리합니다.
    """
    normalized_message = _normalize_text(message)

    has_news_keyword = any(
        keyword in normalized_message
        for keyword in STOCK_NEWS_FOLLOWUP_KEYWORDS
    )

    if not has_news_keyword:
        return False

    sector_name = (
        _extract_sector(message)
        or _find_recent_sector(history)
    )

    return sector_name is not None


def _build_resolved_stock_news_query(
    message: str,
    history: list[dict] | None,
) -> str:
    """
    후속 질문에 생략된 섹터를 이전 대화에서 복원하여
    주식 뉴스 RAG 검색용 질문을 생성합니다.
    """
    normalized_message = " ".join(
        message.split()
    )

    sector_name = (
        _extract_sector(normalized_message)
        or _find_recent_sector(history)
    )

    if not sector_name:
        return normalized_message

    sentiment = _extract_sentiment(
        normalized_message
    )

    sentiment_text = (
        f"{sentiment} 뉴스"
        if sentiment
        else "뉴스"
    )

    if _is_summary_question(normalized_message):
        task_text = (
            "기사 제목, 요약, 긍정 요인과 위험 요인을 "
            "근거로 핵심 내용을 종합해서 요약해줘."
        )
    else:
        task_text = (
            "최근 흐름과 주요 이슈, 긍정 요인과 "
            "위험 요인을 분석해줘."
        )

    return (
        f"{sector_name} 섹터의 최근 30일 "
        f"{sentiment_text}와 섹터 인사이트를 조회해서 "
        f"{task_text}"
    )

def decide_agent_action(
    message: str,
    history: list[dict] | None = None,
) -> AgentDecision:
    """
    사용자 질문과 최근 대화를 분석하여
    실행할 action과 조회할 month를 결정한다.
    """

    current_date = datetime.now(
        ZoneInfo("Asia/Seoul")
    ).strftime("%Y-%m-%d")

    history_text = ""

    if history:
        history_text = "\n".join(
            (
                f"{item.get('role', 'unknown')}: "
                f"{item.get('content', '')}"
            )
            for item in history[-6:]
        )

    user_prompt = f"""
현재 날짜:
{current_date}

최근 대화:
{history_text or "최근 대화 없음"}

사용자 질문:
{message}

사용자 질문과 최근 대화를 분석하여
반드시 다음 JSON 형식으로만 응답하세요.

{{
  "action": "general",
  "month": null,
  "reason": "분류 이유",
  "resolved_query": null
}}

사용 가능한 action:
- spending_summary
- spending_category
- spending_report
- stock_price
- stock_news
- agent_chat_rag
- finance_profile
- risk_profile
- general

month가 필요한 action이면 YYYY-MM 형식으로 반환하고,
필요하지 않으면 null로 반환하세요.

resolved_query 규칙:
- 일반 질문이면 사용자 질문을 그대로 반환하거나 null로 반환합니다.
- 후속 질문이면 최근 대화에서 생략된 종목명이나 섹터명을 복원합니다.
- 예를 들어 이전 질문이 "반도체 뉴스 알려줘"이고,
  현재 질문이 "그럼 긍정적인 것만 요약해줘"라면
  resolved_query는
  "반도체 섹터의 최근 긍정 뉴스를 요약해줘"로 반환합니다.

JSON 외의 설명이나 마크다운은 출력하지 마세요.
""".strip()

    try:
        logger.info(
            "Ollama Router 요청: pid=%s, url=%s, model=%s",
            os.getpid(),
            settings.ollama_base_url,
            settings.ollama_llm_model,
        )

        client = create_ollama_client()

        response = client.chat(
            model=settings.ollama_llm_model,
            messages=[
                {
                    "role": "system",
                    "content": AGENT_DECISION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            stream=False,
            think=False,

            # Pydantic JSON Schema 대신 JSON 모드 사용
            format="json",

            keep_alive="30m",
            options={
                "temperature": 0,
                "num_predict": 512,
                "num_ctx": 4096,
            },
        )

    except ResponseError as exc:
        raise RuntimeError(
            f"Ollama Router 실행에 실패했습니다: {exc.error}"
        ) from exc

    except httpx.ConnectTimeout as exc:
        raise RuntimeError(
            "Ollama 서버 연결 시간이 초과되었습니다. "
            f"주소: {settings.ollama_base_url}"
        ) from exc

    except httpx.ConnectError as exc:
        raise RuntimeError(
            "Ollama 서버에 연결할 수 없습니다. "
            f"주소: {settings.ollama_base_url}"
        ) from exc

    except httpx.ReadTimeout as exc:
        raise RuntimeError(
            "Ollama Router 응답 시간이 초과되었습니다."
        ) from exc

    except httpx.TimeoutException as exc:
        raise RuntimeError(
            "Ollama Router 요청 처리 시간이 초과되었습니다."
        ) from exc

    content = response.message.content

    if not content:
        return AgentDecision(
            action="general",
            month=None,
            reason="Ollama Router 응답이 비어 있음",
        )

    logger.info(
        "Ollama Router 원본 응답: %s",
        content,
    )

    try:
        decision = AgentDecision.model_validate_json(
            content
        )

        # 주식 뉴스 후속 질문은 Router 결과가 흔들리더라도
        # 규칙 기반으로 stock_news를 우선 적용합니다.
        if _should_force_stock_news(
            message=message,
            history=history,
        ):
            resolved_query = (
                _build_resolved_stock_news_query(
                    message=message,
                    history=history,
                )
            )

            return decision.model_copy(
                update={
                    "action": "stock_news",
                    "resolved_query": resolved_query,
                }
            )

        if decision.action == "stock_news":
            resolved_query = (
                _build_resolved_stock_news_query(
                    message=message,
                    history=history,
                )
            )

            return decision.model_copy(
                update={
                    "resolved_query": resolved_query,
                }
            )

        return decision

    except ValidationError as exc:
        logger.error(
            "Router 응답 검증 실패: content=%s, error=%s",
            content,
            exc,
        )

        return AgentDecision(
            action="general",
            month=None,
            reason="Router 응답 형식 오류",
            resolved_query=message,
        )