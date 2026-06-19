from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal



class MonthlyAnalysisRequest(BaseModel):
  """ 월별 분석 실행 및 저장 """
  month: str


class MonthlySummaryResponse(BaseModel):
  """ 월별 요약 조회 응답 """
  month: str
  total_income: Decimal
  total_spending: Decimal
  remaining_money: Decimal
