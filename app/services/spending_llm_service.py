import json
from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from ollama import Client, ResponseError
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.spending_analysis import LLMReportResult


class SpendingLLMService:
    """
    소비 분석 데이터 기반으로 LLM 소비 코칭 리포트 생성

    역할:
    - LLM 프롬프트 생성
    - Ollama API 호출
    - Ollama 응답 JSON 검증
    - Pydantic 스키마 검증
    """

    def __init__(self):
        self.client = Client(
            host=settings.ollama_base_url.rstrip("/"),
            timeout=300.0,
        )

    def generate_spending_report(
        self,
        report_context: dict,
    ) -> dict:
        """
        소비 분석 context를 기반으로 AI 소비 코칭 리포트를 생성한다.
        """

        prompt = self.build_prompt(report_context)

        try:
            response = self.client.chat(
                model=settings.ollama_llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "너는 개인 금융 소비 데이터를 분석해서 "
                            "소비 패턴, 과소비 원인, 다음 달 실천 전략을 "
                            "제안하는 AI 소비 코치다. "
                            "반드시 요청된 JSON 형식으로만 응답해야 한다."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                stream=False,
                format=LLMReportResult.model_json_schema(),
                options={
                    "temperature": 0.3,
                },
                keep_alive="30m",
            )

        except ResponseError as exc:
            print(
                "Ollama ResponseError:",
                type(exc).__name__,
                str(exc),
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ollama 모델 호출 중 오류가 발생했습니다: {exc}",
            ) from exc

        except Exception as exc:
            print(
                "Ollama 호출 오류:",
                type(exc).__name__,
                str(exc),
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM 호출 중 오류가 발생했습니다.",
            ) from exc

        content = response.message.content

        if not content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ollama 응답 내용이 비어 있습니다.",
            )

        try:
            validated = LLMReportResult.model_validate_json(content)

        except ValidationError as exc:
            print("Ollama 원본 응답:")
            print(content)
            print("LLM 응답 검증 오류:")
            print(exc)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="LLM 응답 형식이 올바르지 않습니다.",
            ) from exc

        return validated.model_dump()

    def build_prompt(
        self,
        report_context: dict,
    ) -> str:
        """
        Ollama에 전달할 소비 분석 프롬프트를 생성한다.
        """

        context_json = json.dumps(
            report_context,
            ensure_ascii=False,
            indent=2,
            default=self.json_default,
        )

        return f"""
아래 소비 분석 데이터를 기반으로 AI 소비 코칭 리포트를 작성해줘.

목표:
- 단순히 숫자를 다시 나열하지 말 것
- 소비 패턴을 해석할 것
- 과소비 원인을 분석할 것
- 전월 대비 변화가 의미하는 바를 설명할 것
- 다음 달에 실천할 수 있는 구체적인 전략을 제안할 것
- 사용자가 이해하기 쉬운 자연스러운 한국어로 작성할 것

주의사항:
- 제공된 데이터에서 확인할 수 없는 사실은 추측하지 말 것
- 데이터가 없는 항목은 없다고 명확하게 설명할 것
- 과도하게 단정적인 금융 조언은 하지 말 것
- 금액은 필요한 경우에만 원 단위로 언급할 것
- 모든 문장은 한국어로 작성할 것
- 반드시 JSON 객체 하나만 반환할 것
- JSON 앞뒤에 설명을 추가하지 말 것
- markdown 코드블록을 사용하지 말 것
- 모든 JSON 필드를 빠짐없이 작성할 것

소비 분석 데이터:
{context_json}

응답 형식:
{{
  "report_title": "YYYY년 M월 AI 소비 코칭 리포트",
  "summary_text": "전체 소비 상태에 대한 평가",
  "category_text": "카테고리별 소비 패턴에 대한 해석",
  "overspending_text": "과소비 원인과 주의가 필요한 항목에 대한 분석",
  "card_text": "카드별 소비 습관에 대한 해석",
  "compare_text": "전월 대비 소비 변화가 의미하는 내용",
  "recommendation_text": "다음 달에 실천할 수 있는 소비 개선 전략",
  "agent_response": "사용자에게 전달할 최종 종합 피드백"
}}
""".strip()

    def json_default(self, value):
        """
        json.dumps에서 기본적으로 처리하지 못하는 값을 변환한다.

        Decimal은 int 또는 float로 변환하고,
        datetime과 date는 ISO 형식 문자열로 변환한다.
        """

        if isinstance(value, Decimal):
            if value == value.to_integral_value():
                return int(value)

            return float(value)

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        return str(value)