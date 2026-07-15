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
  "reason": "분류 이유"
}}

사용 가능한 action:
- spending_summary
- spending_category
- spending_report
- agent_chat_rag
- general

month가 필요한 action이면 YYYY-MM 형식으로 반환하고,
필요하지 않으면 null로 반환하세요.

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
                "num_predict": 128,
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
        return AgentDecision.model_validate_json(content)

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
        )