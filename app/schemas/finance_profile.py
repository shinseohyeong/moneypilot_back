"""
schemas/finance_profile.py — 금융 프로필 요청/응답 스키마

팀 모델(app/models/user_model.py FinanceProfile) 기준:
  - age_group, income_level, investment_type, financial_goal  (전부 문자열 분류값)
  - 월급/연봉/위험성향 숫자 컬럼은 팀 모델에 없음

분류값 예시는 Literal로 강제하지 않고 자유 문자열로 둔다.
(팀에서 구간 정의가 확정되면 Literal로 좁히면 됨)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FinanceProfileCreate(BaseModel):
    age_group: Optional[str] = Field(None, max_length=20, description="연령대 구간 (예: '20대')")
    income_level: Optional[str] = Field(None, max_length=50, description="소득 구간 (예: '3000~4000만원')")
    investment_type: Optional[str] = Field(None, max_length=50, description="투자 성향 (예: '안정형')")
    financial_goal: Optional[str] = Field(None, max_length=255, description="투자 목표")


class FinanceProfileUpdate(BaseModel):
    age_group: Optional[str] = Field(None, max_length=20)
    income_level: Optional[str] = Field(None, max_length=50)
    investment_type: Optional[str] = Field(None, max_length=50)
    financial_goal: Optional[str] = Field(None, max_length=255)


class FinanceProfileResponse(BaseModel):
    user_id: int
    age_group: Optional[str]
    income_level: Optional[str]
    investment_type: Optional[str]
    financial_goal: Optional[str]
    updated_at: datetime

    model_config = {"from_attributes": True}