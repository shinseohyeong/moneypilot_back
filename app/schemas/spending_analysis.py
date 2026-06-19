from pydantic import BaseModel, Field
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
  
  total_income: Decimal
  total_spending: Decimal
  fixed_expense: Decimal
  variable_expense: Decimal
  remaining_money: Decimal
  spending_diff: Decimal
  spending_change_rate: Decimal
  
  class Config:
    from_attributes = True
