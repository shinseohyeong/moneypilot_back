from decimal import Decimal

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.user_model import FinanceProfile
from app.models.spending_analysis_model import (
  MonthlySpendingSummary, CategorySpending,
  CardSpending
)
from app.models.transaction_model import Transaction
from app.models.card_statement_model import CardStatement



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
        Transaction.month == month,
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
        Transaction.month == month,
        Transaction.expense_type == "FIXED",
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
      monthly_salary=data["monthly_salary"],
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
    summary.monthly_salary=data["monthly_salary"],
    summary.total_spending=data["total_spending"],
    summary.fixed_expense=data["fixed_expense"],
    summary.variable_expense=data["variable_expense"],
    summary.remaining_money=data["remaining_money"],
    summary.spending_diff=data["spending_diff"],
    summary.spending_change_rate=data["spending_change_rate"],
    
    self.db.commit()
    self.db.refresh(summary)
    
    return summary

# --------------------------------------------------------------
#  카테고리
# --------------------------------------------------------------
class SpendingRepository:
  def __init__(self, db: Session):
    self.db = db
  
  def get_monthly_summary_by_user_and_month(
    self,
    user_id: int,
    month: str,
  ) -> MonthlySpendingSummary | None:
    """ 사용자 ID와 월 기준으로 월별 요약 데이터를 조회 """
    
    return (
      self.db.query(MonthlySpendingSummary)
      .filter(
        MonthlySpendingSummary.user_id == user_id,
        MonthlySpendingSummary.month == month,
      )
      .first()
    )
  
  
  def get_category_totals_by_user_and_month(
    self,
    user_id: int,
    month: str,
  ) :
    """ transactions 테이블에서 특정 월의 지출을 카테고리별로 합산 """
    
    return (
      self.db.query(
        Transaction.category.label("category"),
        func.sum(Transaction.amount).label("category_amount"),
        func.count(Transaction.id).label("transaction_count"),
      )
      .filter(
        Transaction.user_id == user_id,
        Transaction.month == month,
        Transaction.category.isnot(None),
      )
      .group_by(Transaction.category)
      .order_by(func.sum(Transaction.amount).desc())
      .all()
    )
    
  def get_previous_category_amount(
    self,
    user_id: int,
    previous_month: str,
    category: str,
  ):
    """ 전월의 특정 카테고리 지출 금액 조회 """
    
    return (
      self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
      .filter(
        Transaction.user_id == user_id,
        Transaction.month == previous_month,
        Transaction.category == category,
      )
      .scalar()
      or 0
    )


  def delete_category_spendings_by_summary_id(
    self,
    summary_id: int,
  ) -> None:
    """ 
    기존 카테고리별 지출 데이터 삭제,
    재분석 시 중복 저장 방지를 위함.
    """
    self.db.query(CategorySpending).filter(
      CategorySpending.summary_id == summary_id
    ).delete()
    
  
  def create_category_spendings(
    self,
    category_spendings: list[CategorySpending],
  ) -> None:
    """ 카테고리별 지출 데이터를 저장 """
    self.db.add_all(category_spendings)

  # --------------------------------------------------------------
  #  카테고리 - 과소비 항목
  # --------------------------------------------------------------
  def get_category_spendings_by_user_and_month(
    self,
    user_id: int,
    month: str,
  ) -> list[CategorySpending]:
    """
    user_id와 month 기준으로 저장된 카테고리별 지출 데이터 조회
    """
    
    return (
      self.db.query(CategorySpending)
      .filter(
        CategorySpending.user_id == user_id,
        CategorySpending.month == month,
      )
      .all()
    )
  
  # --------------------------------------------------------------
  #  카드별 사용금액 조회
  # --------------------------------------------------------------
  def get_card_totals_by_user_and_month(
    self, 
    user_id: int,
    month: str,
  ):
    """
    특정 월의 카드별/현금별 사용금액 계산
    기준:
    - statement_id가 있으면 card_statements.card_name 기준으로 계산
    - statement_id가 NULL이면 '현금'으로 계산
    """
    card_name_expr = case(
      (
        Transaction.statement_id.is_(None),
        "현금",
      ),
      (
        CardStatement.card_name.is_(None),
        "현금",
      ),
      (
        CardStatement.card_name == "",
        "현금",
      ),
      else_=CardStatement.card_name,
    )
    
    return (
      self.db.query(
        card_name_expr.label("card_name"),
        func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label("card_amount"),
        func.count(Transaction.id).label("transaction_count"),
      )
      .outerjoin(
        CardStatement,
        Transaction.statement_id == CardStatement.id,
      )
      .filter(
        Transaction.user_id == user_id,
        Transaction.month == month,
      )
      .group_by(card_name_expr)
      .order_by(func.sum(func.abs(Transaction.amount)).desc())
      .all()
    )
    
  
  def delete_card_spendings_by_summary_id(
    self,
    summary_id: int,
  ) -> None:
    """ 특정 월별 요약에 연결된 카드별 사용금액 데이터 삭제 """
    
    self.db.query(CardSpending).filter(
      CardSpending.summary_id == summary_id
    ).delete()
  
  
  def create_card_spendings(
    self,
    card_spendings: list[CardSpending],
  ) -> None:
    """ 카드별 사용금액 데이터를 저장 """
    self.db.add_all(card_spendings)


  def get_card_spendings_by_user_and_month(
    self,
    user_id: int,
    month: str, 
  ) -> list[CardSpending]:
    """ 저장된 월별 카드별 사용금액 데이터 조회 """
    
    return (
      self.db.query(CardSpending)
      .filter(
        CardSpending.user_id == user_id,
        CardSpending.month == month,
      )
      .order_by(CardSpending.card_amount.desc())
      .all()
    )