from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class FinanceProfileCreate(BaseModel):
    monthly_salary: float = Field(..., ge=0, description="월급 (원)")
    annual_salary: Optional[float] = Field(None, ge=0, description="연봉 (미입력 시 월급×12 자동 계산)")
    fixed_expense: Optional[float] = Field(0, ge=0, description="월 고정비 (원)")
    risk_type: str = Field(..., max_length=30, description="투자 성향 (안정형, 중립형, 공격형 등)")
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
    id: int
    user_id: int
    monthly_salary: float
    annual_salary: float
    fixed_expense: Optional[float]
    risk_type: str
    investment_goal: Optional[str]
    target_saving_amount: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}