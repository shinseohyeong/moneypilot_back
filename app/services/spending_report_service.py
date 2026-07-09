import re
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.spending_analysis_model import AnalysisReport
from app.repositories.spending_repository import SpendingRepository
from app.repositories.spending_report_repository import AnalysisReportRepository
from app.services.spending_llm_service import SpendingLLMService
from app.services.spending_analysis_service import SpendingService
from app.services.spending_analysis_service import SpendingAnalysisService


class AnalysisReportService:
  """
  AI 소비 분석 리포트 비즈니스 로직 Service.
  역할:
  - 기존 소비 분석 데이터를 조회
  - LLM에 전달할 report_context 생성
  - SpendingLLMService 통해 LLM 리포트 생성
  - analysis_reports 테이블에 리포트를 저장하거나 수정
  - 저장된 AI 리포트 조회
  """
  def __init__(self, db: Session):
    """ AnalysisReportService 초기화 """
    self.db = db
    
    # 기존 분석 데이터 조회용 Repository
    self.spending_repository = SpendingRepository(db)
    
    # AI 리포트 저장/조회용 Repository
    self.report_repository = AnalysisReportRepository(db)
    
    # LLM 호출용 Service
    self.llm_service = SpendingLLMService()
    
    # 기존 소비 분석 서비스 재사용
    self.spending_service = SpendingService(db)
    self.spending_analysis_service = SpendingAnalysisService(db)
    
  
  def generate_monthly_report(
    self,
    user_id: int,
    month: str, 
  ) -> AnalysisReport:
    """
    특정 월의 AI 소비 분석 리포트를 생성하고 저장
    처리 흐름:
    1. month 형식 검증
    2. 기존 월별 요약 데이터 조회 함수 재사용
    3. 기존 과소비 카테고리 조회 함수 재사용
    4. 기존 카드별 사용금액 데이터 조회 함수 재사용
    5. LLM에 전달할 report_context 생성
    6. LLM을 호출해 소비 코칭 리포트 생성
    7. analysis_reports 테이블에 저장하거나 기존 리포트 수정
    8. 저장된 리포트 반환
    """
    
    self.spending_analysis_service.validate_month_format(month)
    
    # 1. 기존 월별 요약 조회 함수 재사용
    summary = self.spending_analysis_service.get_monthly_summary_by_month(
      user_id=user_id,
      month=month,
    )
    
    
    # 2. 기존 과소비 카테고리 조회 함수 재사용
    overspending_data = self.spending_service.get_monthly_overspending_categories(
      user_id=user_id,
      month=month,
    )
    
    # 3. 기존 카드별 사용금액 조회 함수 재사용
    card_data = self.spending_service.get_monthly_card_spendings(
      user_id=user_id,
      month=month,
    )
    
    # 4. LLM 전달용 context 생성
    report_context = self.build_report_context(
      summary=summary,
      overspending_data=overspending_data,
      card_data=card_data,
    )
    
    # 5. LLM 호출
    llm_result = self.llm_service.generate_spending_report(
      report_context=report_context,
    )
    
    # 6. 리포트 저장 또는 수정
    report = self.report_repository.save_or_update_report(
      summary_id=summary.id,
      user_id=user_id,
      month=month,
      report_title=llm_result.get("report_title", f"{month} AI 소비 코칭 리포트"),
      summary_text=llm_result.get("summary_text", ""),
      category_text=llm_result.get("category_text"),
      overspending_text=llm_result.get("overspending_text"),
      card_text=llm_result.get("card_text"),
      compare_text=llm_result.get("compare_text"),
      recommendation_text=llm_result.get("recommendation_text"),
      agent_response=llm_result.get("agent_response"),
    )
    
    return report

  
  def get_monthly_report(
    self,
    user_id: int, 
    month: str,
  ) -> AnalysisReport:
    """ 
    특정 월의 저장된 AI 소비 분석 리포트 조회 
    GET 요청에는 LLM 호출하지 않고,
    analysis_reports 테이블에 저장된 리포트만 조회
    """
    self.spending_analysis_service.validate_month_format(month)
    
    summary = self.spending_analysis_service.get_monthly_summary_by_month(
      user_id=user_id,
      month=month,
    )
    
    report = self.report_repository.get_report_by_summary_id(
      summary_id=summary.id,
    )
    
    if not summary:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="생성된 AI 소비 분석 리포트가 없습니다.",
      )
      
    return report
  
  
  def build_report_context(
    self,
    summary,
    overspending_data: dict, 
    card_data: dict,
  ) -> dict:
    """
    LLM에 전달할 소비 분석 context를 생성
    포함 데이터: 
    - 월별 소비 요약
    - 이번 달 지출 금액이 큰 카테고리 Top 3
    - 전월 대비 증가 카테고리 Top 3
    - 카드별 사용금액 Top 1 카드
    """
    top_card = self.extract_top_card(card_data)
    
    return {
      "month": summary.month,
      "monthly_summary": {
        "monthly_salary": self.decimal_to_int(summary.monthly_salary),
        "total_income": self.decimal_to_int(summary.total_income),
        "total_spending": self.decimal_to_int(summary.total_spending),
        "fixed_expense": self.decimal_to_int(summary.fixed_expense),
        "variable_expense": self.decimal_to_int(summary.variable_expense),
        "remaining_money": self.decimal_to_int(summary.remaining_money),
        "spending_diff": self.decimal_to_int(summary.spending_diff),
        "spending_change_rate": self.decimal_to_float(summary.spending_change_rate),
      },
      "top_spending_categories": overspending_data.get(
        "top_spending_categories",
        [],
      ),
      "top_increased_categories": overspending_data.get(
        "top_increased_categories",
        [],
      ),
      "top_card": top_card,
    }
  
  def extract_top_card(
    self,
    card_data: dict,
  ) -> dict | None:
    """ 카드별 사용금액 데이터에서 가장 많이 사용한 카드 1개 추출 """
    cards = card_data.get("cards", [])
    
    if not cards:
      return None
    
    sorted_cards = sorted(
      cards,
      key=lambda item: item.get("card_amount", 0),
      reverse=True,
    )
    
    return sorted_cards[0]
  
  
  def decimal_to_int(
    self, 
    value,
  ) -> int:
    """ Decimal 또는 None 값을 int로 변환 """
    if value is None:
      return 0
    
    return int(Decimal(value))
  
  def decimal_to_float(
    self,
    value,
  ) -> float:
    """ Decimal 또는 None 값을 float로 변환 """
    if value is None:
      return 0.0
    
    return float(Decimal(value))

  
  

  
  
    