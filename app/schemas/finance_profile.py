"""
schemas/finance_profile.py — 금융 프로필 요청/응답 스키마
팀 모델 기준: age_group, income_level, investment_type, financial_goal (전부 문자열)
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