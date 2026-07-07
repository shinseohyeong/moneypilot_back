import json
from decimal import Decimal
from datetime import date, datetime

from fastapi import HTTPException, status
from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.spending_analysis import LLMReportResult


class SpendingLLMService:
  """
  소비 분석 데이터 기반으로 LLM 소비 코칭 리포트 생성
  역할 :
  - LLM 프롬프트 생성
  - OpenAI API 호출
  - LLM 응답 JSON 파싱
  - LLM 응답 스키마 검증
  """
  def __init__(self):
    self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
  def generate_spending_report(
    self, 
    report_context: dict,
  ) -> dict:
    """ 소비 분석 context를 기반으로 AI 소비 코칭 리포트 생성 """
    
    prompt = self.build_prompt(report_context)
    
    try:
      response = self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
          {
            "role": "system",
            "content": (
              "너는 개인 금융 소비 데이터를 분석해서 "
              "소비 패턴, 과소비 원인, 다음 달 실천 전략을 제안하는 AI 소비 코치다."
            ),
          },
          {
            "role": "user",
            "content": prompt,
          },
        ],
        temperature=0.3,
      )
    except Exception:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="LLM 호출 중 오류가 발생했습니다.",
      )
      
    content = response.choices[0].message.content
    
    try:
      result = json.loads(content)
    except json.JSONDecodeError:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="LLM 응답을 JSON으로 변환할 수 없습니다."
      )
    
    try:
      validated = LLMReportResult(**result)
    except ValidationError:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="LLM 응답 형식이 올바르지 않습니다.",
      )
      
    return validated.model_dump()
  
  
  def build_prompt(
    self,
    report_context: dict,
  ) -> str: 
    """  LLM 에 전달할 프롬프트를 생성 """
    
    return f"""
  아래 소비 분석 데이터를 기반으로 AI 소비 코칭 리포트를 작성해줘.

목표:
- 단순히 숫자를 다시 나열하지 말 것
- 소비 패턴을 해석할 것
- 과소비 원인을 추론할 것
- 다음 달 실천 전략을 제안할 것
- 사용자에게 자연스럽고 이해하기 쉬운 종합 피드백을 줄 것

주의사항:
- 제공된 데이터에 없는 내용은 추측하지 말 것
- 과도하게 단정적인 금융 조언은 하지 말 것
- 금액은 필요할 때만 원 단위로 언급할 것
- 응답은 반드시 JSON 형식으로만 반환할 것
- markdown 코드블록을 붙이지 말 것
- 모든 문장은 한국어로 작성할 것

소비 분석 데이터:
{json.dumps(report_context, ensure_ascii=False, indent=2, default=self.json_default)}

응답 형식:
{{
  "report_title": "YYYY년 M월 AI 소비 코칭 리포트",
  "summary_text": "전체 소비 상태 평가",
  "category_text": "카테고리별 소비 패턴 해석",
  "overspending_text": "과소비 원인 및 위험 항목 분석",
  "card_text": "카드별 소비 습관 해석",
  "compare_text": "전월 대비 변화의 의미 해석",
  "recommendation_text": "다음 달 실천 전략",
  "agent_response": "사용자에게 전달할 최종 종합 피드백"
}}
  """
  
  def json_default(self, value):
    """
    json.dumps에서 기본적으로 처리하지 못하는 값을 변환한다.

    Decimal, datetime 같은 객체가 LLM context에 포함되어도
    JSON 문자열로 변환할 수 있도록 처리한다.
    """
    if isinstance(value, Decimal):
      if value == value.to_integral_value():
        return int(value)
      return float(value)

    if isinstance(value, (datetime, date)):
      return value.isoformat()

    return str(value)