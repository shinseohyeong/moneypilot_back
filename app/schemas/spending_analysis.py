from pydantic import BaseModel, Field, field_validator, field_serializer
from typing import List, Optional
from datetime import datetime
from decimal import Decimal



class MonthlyAnalysisRequest(BaseModel):
  """ 월별 분석 실행 및 저장 """
  month: str = Field(..., examples=["2026-06"])


class MonthlySummaryResponse(BaseModel):
  """ 월별 요약 조회 응답 """
  id: int
  user_id: int
  month: str
  
  total_income: int
  monthly_salary: int
  total_spending: int
  fixed_expense: int
  variable_expense: int
  remaining_money: int
  spending_diff: int | None = None
  spending_change_rate: float | None = None
  
  @field_validator(
    "total_income",
    "monthly_salary",
    "total_spending",
    "fixed_expense",
    "variable_expense",
    "remaining_money",
    "spending_diff",
    mode="before",
  )
  
  @classmethod
  def decimal_to_int(cls, value):
    if value is None:
      return None
    return int(value)

  @field_validator("spending_change_rate", mode="before")
  @classmethod
  def decimal_to_float(cls, value):
    if value is None:
      return None
    return float(value)
  
  class Config:
    from_attributes = True


# --------------------------------------------------------------
#  카테고리
# --------------------------------------------------------------

class CategorySpendingResponse(BaseModel):
  """ 월별 카테고리별 지출 조회 응답 """
  id: int
  summary_id: int
  user_id:int
  month: str
  
  category: str
  category_amount: int
  category_ratio: Decimal
  
  transaction_count: int
  previous_category_amount: int
  spending_diff: int
  spending_change_rate: Decimal
  
  created_at: datetime
  
  @field_validator(
    "category_amount",
    "previous_category_amount",
    "spending_diff",
    mode="before",
  )
  @classmethod
  def decimal_to_int(cls, value):
    if value is None:
      return 0

    return int(value)
  
  class Config:
    from_attributes = True
  

class OverspendingCategoryItemResponse(BaseModel):
  """ 과소비 카테고리 항목 응답 """
  category: str
  category_amount: Decimal
  category_ratio: Decimal
  previous_category_amount: Decimal
  spending_diff: Decimal
  spending_change_rate: Decimal
  reason: str
  
  @field_serializer(
    "category_amount",
    "previous_category_amount",
    "spending_diff",
  )
  def serialize_decimal_to_int(self, value: Decimal) -> int:
    return int(value or 0)

  @field_serializer(
    "category_ratio",
    "spending_change_rate",
  )
  def serialize_decimal_to_float(self, value: Decimal) -> float:
    return float(value or 0)

  class Config:
    from_attributes = True


class MonthlyOverspendingResponse(BaseModel):
  """ 월별 과소비 카테고리 응답 """
  month: str 
  top_spending_categories: list[OverspendingCategoryItemResponse]
  top_increased_categories: list[OverspendingCategoryItemResponse]
  
  
  