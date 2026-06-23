"""
schemas/finance_profile.py — 금융 프로필 요청/응답 스키마
<<<<<<< Updated upstream
팀 모델 기준: age_group, income_level, investment_type, financial_goal (전부 문자열)
=======

실제 팀 모델(user_model.py FinanceProfile) 기준:
  monthly_salary        DECIMAL, NOT NULL  (필수)
  annual_salary         DECIMAL, NOT NULL  (필수)
  fixed_expense         DECIMAL, nullable, 기본 0
  risk_type             String(30), NOT NULL  (필수)
  investment_goal       String(100), nullable
  target_saving_amount  DECIMAL, nullable, 기본 0
>>>>>>> Stashed changes
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FinanceProfileCreate(BaseModel):
    monthly_salary: float = Field(..., ge=0, description="월급 (원)")
    annual_salary: Optional[float] = Field(None, ge=0, description="연봉 (미입력 시 월급×12 자동 계산)")
    fixed_expense: Optional[float] = Field(0, ge=0, description="월 고정비 (원)")
    risk_type: str = Field(..., max_length=30, description="투자 성향")
    investment_goal: Optional[str] = Field(None, max_length=100, description="투자 목표")
    target_saving_amount: Optional[float] = Field(0, ge=0, description="목표 저축액 (원)")


class FinanceProfileUpdate(BaseModel):
    monthly_salary: Optional[float] = Field(None, ge=0)
    annual_salary: Optional[float] = Field(None, ge=0)
    fixed_expense: Optional[float] = Field(None, ge=0)
    risk_type: Optional[str] = Field(None, max_length=30)
    investment_goal: Optional[str] = Field(None, max_length=100)
    target_saving_amount: Optional[float] = Field(None, ge=0)


class FinanceProfileResponse(BaseModel):
    user_id: int
    monthly_salary: float
    annual_salary: float
    fixed_expense: Optional[float]
    risk_type: str
    investment_goal: Optional[str]
    target_saving_amount: Optional[float]
    updated_at: datetime

    model_config = {"from_attributes": True}