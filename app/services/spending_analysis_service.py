import re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from dateutil.relativedelta import relativedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.spending_analysis_model import CategorySpending
from app.repositories.spending_repository import SpendingAnalysisRepository, SpendingRepository


class SpendingAnalysisService:
  def __init__(self, db:Session):
    self.repository = SpendingAnalysisRepository(db)
    
  def validate_month_format(self, month:str) -> None:
    """
    month가 YYYY-MM 형식인지 검증한다.
    ex) 2026-06
    """
    
    if not re.match(r"^\d{4}-\d{2}$", month):
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="month는 YYYY-MM 형식이어야 합니다. ex) 2026-06",
      )
      
    try:
      datetime.strptime(month, "%Y-%m")
    except ValueError:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="올바르지 않은 month 값입니다. ex) 2026-06",
      )
  
  def get_previous_month(self, month: str) -> str:
    """
    전달받은 month의 전월을 구한다.
    ex) 2026-06 -> 2026-05 
    """
    date = datetime.strptime(month, "%Y-%m")
    
    if date.month == 1:
      return f"{date.year - 1}-12"
    
    return f"{date.year}-{date.month - 1:02d}"

  
  def calculate_change_rate(
    self,
    spending_diff: Decimal,
    previous_total_spending: Decimal,
  ):
    """
    전월 대비 지출 증감률 계산
    """
    if previous_total_spending == 0:
      return Decimal("0")
    
    return (
      spending_diff / previous_total_spending * Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    
  def analyze_and_save_monthly_summary(
    self,
    user_id: int,
    month: str,
  ):
    """
    월별 분석 실행 및 저장
    1. month 형식 검증
    2. finance_profiles에서 월급 조회
    3. transactions에서 월별 총지출 조회
    4. transactions에서 월별 고정비 조회
    5. total_income, total_spending, fixed_expense, variable_expense 계산
    6. 전월 대비 지출 증감액/증감률 계산
    7. monthly_spending_summaries에 저장 또는 수정
    """
    
    self.validate_month_format(month)
    
    finance_profile = self.repository.get_finance_profile(user_id=user_id)
    
    if not finance_profile:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="금융 프로필이 없습니다. 월급 정보를 먼저 입력해주세요.",
      )
    
    
    # 총 수입액
    total_income = Decimal(finance_profile.monthly_salary or 0)
    
    # 월급
    monthly_salary = total_income
    
    # 프로필 고정액
    # profile_fixed_expense = Decimal(getattr(finance_profile, "fixed_expense", 0) or 0)
    
    # 총 지출액
    total_transaction_amount = self.repository.get_monthly_total_transaction_amount(
      user_id=user_id,
      month=month,
    )
    
    # 거래내역 중 고정비 합계
    fixed_transaction_amount = self.repository.get_monthly_fixed_transaction_amount(
      user_id=user_id,
      month=month,
    )
    
    total_spending = abs(Decimal(total_transaction_amount or 0))
    
    fixed_expense = abs(Decimal(fixed_transaction_amount or 0))
    
    # 고정비 = 거래내역 고정비 + 사용자가 직접 입력한 월 고정비
    # fixed_expense = fixed_transaction_amount + profile_fixed_expense
    
    # 변동비 = 총지출 - 고정비
    variable_expense = total_spending - fixed_expense
    
    if variable_expense < 0:
      variable_expense = Decimal("0")
    
    # 여유자금 = 총수입 - 총지출
    remaining_money = total_income - total_spending
    
    # 전월 대비 계산
    previous_month = self.get_previous_month(month)
    
    previous_summary = self.repository.get_previous_month_summary(
      user_id=user_id,
      previous_month=previous_month,
    )
    
    if previous_summary:
      previous_total_spending = Decimal(previous_summary.total_spending or 0)
      spending_diff = total_spending - previous_total_spending
      spending_change_rate = self.calculate_change_rate(
        spending_diff=spending_diff,
        previous_total_spending=previous_total_spending,
      )
    else:
      spending_diff = Decimal("0")
      spending_change_rate = Decimal("0")
    
    data = {
      "total_income": total_income,
      "monthly_salary": monthly_salary,
      "total_spending": total_spending,
      "fixed_expense": fixed_expense,
      "variable_expense": variable_expense,
      "remaining_money": remaining_money,
      "spending_diff": spending_diff,
      "spending_change_rate": spending_change_rate,
    }
    
    existing_summary = self.repository.get_monthly_summary(
      user_id=user_id,
      month=month,
    )
    
    if existing_summary:
      return self.repository.update_monthly_summary(
        summary=existing_summary,
        data=data,
    )
      
    return self.repository.create_monthly_summary(
      user_id=user_id,
      month=month,
      data=data,
    )
  
  
  def get_monthly_summary_by_month(
    self,
    user_id: int,
    month: str,
  ):
    """
    월별 요약 조회 
    monthly_spending_summaries 테이블에서
    user_id + month 기준으로 저장된 요약 데이터를 조회한다.
    """
    
    self.validate_month_format(month)
    
    summary = self.repository.get_monthly_summary(
      user_id=user_id,
      month=month,
    )
    
    if not summary:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="해당 월의 소비 요약 데이터가 없습니다. 먼저 월별 분석을 실행해주세요.",
      )
    
    return summary


# --------------------------------------------------------------
#  카테고리
# --------------------------------------------------------------
class SpendingService:
  def __init__(self, db: Session):
    self.db = db
    self.repository = SpendingRepository(db)
  
  def save_monthly_category_spendings(
    self,
    user_id: int,
    month: str,
  ) -> list[CategorySpending]:
    """ 특정 월의 거래내역을 카테고리별로 합산하여 저장 """
    
    summary = self.repository.get_monthly_summary_by_user_and_month(
      user_id=user_id,
      month=month,
    )
    
    if not summary:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="해당 월의 월별 요약 데이터가 없습니다.",
      )
    
    category_totals = self.repository.get_category_totals_by_user_and_month(
      user_id=user_id,
      month=month,
    )
    
    if not category_totals:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="해당 월의 거래내역이 없습니다.",
      )
    
    #  현재 month 기준으로 전월 계산
    current_month_date = datetime.strptime(month, "%Y-%m")
    previous_month = (
      current_month_date - relativedelta(months=1)
    ).strftime("%Y-%m")
      
    # 지출 금액 합계 계산
    total_amount = sum(
      abs(Decimal(row.category_amount or 0))
      for row in category_totals
    )
    
    if total_amount == 0:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="카테고리별 지출 합계가 0원입니다.",
      )
    
    # 기존 데이터 삭제 후 재저장
    self.repository.delete_category_spendings_by_summary_id(
      summary_id=summary.id,
    )
    
    category_spendings = []
    
    for row in category_totals:
      category_amount = abs(Decimal(row.category_amount or 0))
      
      category_ratio = round(
        (category_amount / total_amount) * Decimal("100"),
        2,
      )
      
      # 전월 같은 카테고리 지출액 조회
      previous_category_amount = self.repository.get_previous_category_amount(
        user_id=user_id,
        previous_month=previous_month,
        category=row.category,
      )
      
      # 전월 지출액도 저장
      previous_category_amount = abs(Decimal(previous_category_amount or 0))
      
      # 전월 대비 증감액 계산
      spending_diff = category_amount - previous_category_amount
      
      if previous_category_amount == 0:
        spending_change_rate = Decimal("0")
      else:
        spending_change_rate = round(
          (spending_diff / previous_category_amount) * Decimal("100"),
          2,
        )
      
      category_spending = CategorySpending(
        summary_id=summary.id,
        user_id=user_id,
        month=month,
        category=row.category,
        category_amount=category_amount,
        category_ratio=category_ratio,
        transaction_count=row.transaction_count,
        previous_category_amount=previous_category_amount,
        spending_diff=spending_diff,
        spending_change_rate=spending_change_rate,
      )
      
      category_spendings.append(category_spending)
    
    self.repository.create_category_spendings(category_spendings)
    
    self.db.commit()
    
    for category_spending in category_spendings:
      self.db.refresh(category_spending)
      
    return category_spendings
    
  
  