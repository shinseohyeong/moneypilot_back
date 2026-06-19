from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user_model import FinanceProfile
from app.models.spending_analysis_model import MonthlySpendingSummary
from app.models.transaction_model import Transaction


class SpendingAnalysisRepository:
  def __init__(self, db: Session):
    self.db = db
    
  def get_finance_profile(
    self,
    user_id: int,
  ) -> FinanceProfile | None:
    """
    사용자 금융 프로필 조회
    - monthly_salary
    가져올 때 사용
    """
    return (
      self.db.query(FinanceProfile)
      .filter(FinanceProfile.user_id == user_id)
      .first()
    )
  
  def get_monthly_summary(
    self,
    user_id: int,
    month: str,
  ) -> MonthlySpendingSummary | None:
    """
    월별 요약 조회(총수입, 총소비, 여유자금) 
    """
    return (
      self.db.query(MonthlySpendingSummary)
      .filter(
        MonthlySpendingSummary.user_id == user_id,
        MonthlySpendingSummary.month == month,
      )
      .first()
    )


  def get_previous_month_summary(
    self,
    user_id: int,
    previous_month: str,
  ) -> MonthlySpendingSummary | None:
    """
    전월 요약 조회
    전월 대비 지출 증감액 / 증감률 계산에 사용 
    """
    return (
      self.db.query(MonthlySpendingSummary)
      .filter(
        MonthlySpendingSummary.user_id == user_id,
        MonthlySpendingSummary.month == previous_month,
      )
      .first()
    )
  
  
  def get_monthly_total_transaction_amount(
    self,
    user_id: int,
    month: str,
  ) -> Decimal:
    """
    특정 월 전체 거래 금액 합계 조회
    total_spending 계산 재료
    """
    
    result = (
      self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
      .filter(
        Transaction.user_id == user_id,
        func.date_format(Transaction.trans_date, "%Y-%m") == month,
      )
      .scalar()
    )
    
    return Decimal(result or 0)

  
  def get_monthly_fixed_transaction_amount(
    self,
    user_id: int,
    month: str,
  ) -> Decimal:
    """
    특정 월 거래내역 중 is_fixed=True인 금액 합계 조회
    fixed_expense 계산 재료
    """
    result = (
      self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
      .filter(
        Transaction.user_id == user_id,
        func.date_format(Transaction.trans_date, "%Y-%m") == month,
        Transaction.is_fixed == True,
      )
      .scalar()
    )

    return Decimal(result or 0)


  def create_monthly_summary(
    self,
    user_id: int,
    month: str,
    data: dict,
  ) -> MonthlySpendingSummary:
    """ 월별 요약 신규 저장 """
    
    summary = MonthlySpendingSummary(
      user_id=user_id,
      month=month,
      total_income=data["total_income"],
      total_spending=data["total_spending"],
      fixed_expense=data["fixed_expense"],
      variable_expense=data["variable_expense"],
      remaining_money=data["remaining_money"],
      spending_diff=data["spending_diff"],
      spending_change_rate=data["spending_change_rate"],
    )
    self.db.add(summary)
    self.db.commit()
    self.db.refresh(summary)
  
  
  def update_monthly_summary(
    self,
    summary: MonthlySpendingSummary,
    data: dict,
  ) -> MonthlySpendingSummary:
    """ 기존 월별 요약 수정 """
    
    summary.total_income=data["total_income"],
    summary.total_spending=data["total_spending"],
    summary.fixed_expense=data["fixed_expense"],
    summary.variable_expense=data["variable_expense"],
    summary.remaining_money=data["remaining_money"],
    summary.spending_diff=data["spending_diff"],
    summary.spending_change_rate=data["spending_change_rate"],
    
    self.db.commit()
    self.db.refresh(summary)
    
    return summary
  