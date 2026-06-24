# ============================================================
# 파일 위치: app/clients/llm_client.py
# 역할:
#   - LLM 호출을 담당합니다.
#   - service는 OpenAI인지 Ollama인지 몰라도 되도록 client로 분리합니다.
# ============================================================

import json
import re
from typing import Dict, Optional

from fastapi import HTTPException
from openai import OpenAI

from app.core.config import settings


class BaseLlmClient:
    """
    LLM client 공통 인터페이스 역할
    """

    model_name: str

    def summarize_news(
        self,
        title: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict:
        raise NotImplementedError


class OpenAiLlmClient(BaseLlmClient):
    def __init__(self):
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY가 설정되지 않았습니다. .env를 확인해주세요.",
            )

        self.model_name = settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key)

    def summarize_news(
        self,
        title: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict:
        """
        뉴스 제목/설명/본문을 기반으로 투자 참고용 요약 JSON을 생성합니다.
        """
        prompt = self._build_prompt(
            title=title,
            description=description,
            content=content,
        )

        try:
            response = self.client.responses.create(
                model=self.model_name,
                instructions=(
                    "너는 금융 뉴스 요약을 도와주는 assistant야. "
                    "투자 권유를 하면 안 되고, 뉴스 기반 참고 정보만 제공해야 해. "
                    "반드시 JSON 객체만 반환해."
                ),
                input=prompt,
            )

            output_text = response.output_text
            return self._parse_json_output(output_text)

        except HTTPException:
            raise

        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI 뉴스 요약 호출 중 오류가 발생했습니다: {str(e)}",
            )

    def _build_prompt(
        self,
        title: str,
        description: Optional[str],
        content: Optional[str],
    ) -> str:
        """
        LLM에 전달할 프롬프트를 생성합니다.

        현재 네이버 뉴스 API는 원문 전체가 아니라 제목/요약문 중심이므로,
        content가 없으면 title + description만 사용합니다.
        """
        return f"""
아래 뉴스 정보를 바탕으로 투자 참고용 요약을 작성해줘.

[뉴스 제목]
{title}

[뉴스 설명]
{description or ""}

[뉴스 본문]
{content or ""}

반드시 아래 JSON 형식만 반환해.
마크다운 코드블록은 사용하지 마.

{{
  "one_line_summary": "뉴스를 한 문장으로 요약",
  "summary_text": "핵심 내용을 2~4문장으로 요약",
  "positive_factors": ["긍정 요인 1", "긍정 요인 2"],
  "risk_factors": ["위험 요인 1", "위험 요인 2"],
  "investment_note": "투자 판단 시 유의할 점. 단, 매수/매도 추천 금지",
  "sentiment": "POSITIVE | NEUTRAL | NEGATIVE 중 하나"
}}
"""

    def _parse_json_output(self, output_text: str) -> Dict:
        """
        LLM 응답에서 JSON 객체를 파싱합니다.
        """
        if not output_text:
            raise HTTPException(
                status_code=502,
                detail="LLM 응답이 비어 있습니다.",
            )

        cleaned = output_text.strip()

        # 혹시 모델이 ```json ... ``` 코드블록을 붙였을 경우 제거
        cleaned = re.sub(r"^```json", "", cleaned)
        cleaned = re.sub(r"^```", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)

        except json.JSONDecodeError:
            raise HTTPException(
                status_code=502,
                detail=f"LLM 응답을 JSON으로 파싱할 수 없습니다: {cleaned[:300]}",
            )

        return self._validate_summary_json(data)

    def _validate_summary_json(self, data: Dict) -> Dict:
        """
        LLM 결과에 필요한 키가 없을 때 기본값을 채웁니다.
        """
        sentiment = data.get("sentiment") or "NEUTRAL"
        sentiment = str(sentiment).upper()

        if sentiment not in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
            sentiment = "NEUTRAL"

        return {
            "one_line_summary": data.get("one_line_summary") or "",
            "summary_text": data.get("summary_text") or "",
            "positive_factors": data.get("positive_factors") or [],
            "risk_factors": data.get("risk_factors") or [],
            "investment_note": data.get("investment_note") or "",
            "sentiment": sentiment,
        }


class OllamaLlmClient(BaseLlmClient):
    """
    나중에 Ollama 테스트용으로 확장할 자리입니다.

    지금은 OpenAI부터 안정화하고,
    이후 LLM_PROVIDER=ollama일 때 이 클래스를 구현하면 됩니다.
    """

    def __init__(self):
        self.model_name = settings.ollama_model

    def summarize_news(
        self,
        title: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict:
        raise HTTPException(
            status_code=501,
            detail="Ollama LLM client는 아직 구현되지 않았습니다.",
        )


def get_llm_client() -> BaseLlmClient:
    """
    .env의 LLM_PROVIDER 값에 따라 LLM client를 선택합니다.
    """
    provider = settings.llm_provider.lower()

    if provider == "openai":
        return OpenAiLlmClient()

    if provider == "ollama":
        return OllamaLlmClient()

    raise HTTPException(
        status_code=500,
        detail=f"지원하지 않는 LLM_PROVIDER입니다: {settings.llm_provider}",
    )