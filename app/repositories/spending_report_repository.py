from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.spending_analysis_model import AnalysisReport
from app.models.spending_analysis_model import (
  MonthlySpendingSummary,
  CategorySpending,
)
from app.models.transaction_model import Transaction


class AnalysisReportRepository:
  """  
  AI 소비 분석 리포트 관련 DB 접근
  역할
  - analysis_reports 테이블 조회/저장/수정
  - 기존 리포트 수정
  """
  def __init__(self, db: Session):
    self.db = db
  
  
  def get_report_by_summary_id(
    self,
    summary_id: int,
  ) -> AnalysisReport | None:
    """ summary_id 기준으로 저장된 AI 소비 분석 리포트 조회 """
    
    return (
      self.db.query(AnalysisReport)
      .filter(AnalysisReport.summary_id == summary_id)
      .first()
    )
    
  
  def get_report_by_user_and_month(
    self,
    user_id: int,
    month: str,
  ) -> AnalysisReport | None:
    """ user_id와 month 기준으로 저장된 AI 소비 분석 리포트를 조회 """
    
    return (
      self.db.query(AnalysisReport)
      .filter(
        AnalysisReport.user_id == user_id,
        AnalysisReport.month == month,
      )
      .first()
    )
  
  
  def save_or_update_report(
    self,
    summary_id: int,
    user_id: int, 
    month: str,
    report_title: str, 
    summary_text: str, 
    category_text: str | None = None,
    overspending_text: str | None = None,
    card_text: str | None = None,
    compare_text: str | None = None,
    recommendation_text: str | None = None,
    agent_response: str | None = None,
  ) -> AnalysisReport:
    """ 
    AI 소비 분석 리포트를 저장하거나 수정
    summary_id 기준으로 기존 리포트가 있으면 update하고,
    없으면 새로 insert
    
    Args:
      summary_id (int): 월별 요약 ID
      user_id (int): 사용자 ID
      month (str): 리포트 대상 월
      report_title (str): 리포트 제목
      summary_text (str): 전체 소비 상태 평가
      category_text (str | None): 카테고리별 소비 패턴 해석
      overspending_text (str | None): 과소비 원인 분석
      card_text (str | None): 카드별 소비 습관 해석
      compare_text (str | None): 전월 대비 변화 해석
      recommendation_text (str | None): 다음 달 실천 전략
      agent_response (str | None): 최종 종합 피드백

    Returns:
      AnalysisReport:
        저장 또는 수정된 AI 소비 분석 리포트 객체
    """
    report = self.get_report_by_summary_id(summary_id)
    
    if report:
      report.report_title = report_title
      report.summary_text = summary_text
      report.category_text = category_text
      report.overspending_text = overspending_text
      report.card_text = card_text
      report.compare_text = compare_text
      report.recommendation_text = recommendation_text
      report.agent_response = agent_response
    
    else:
      report = AnalysisReport(
        summary_id=summary_id,
        user_id=user_id,
        month=month,
        report_title=report_title,
        summary_text=summary_text,
        category_text=category_text,
        overspending_text=overspending_text,
        card_text=card_text,
        compare_text=compare_text,
        recommendation_text=recommendation_text,
        agent_response=agent_response,
      )
      
      self.db.add(report)
    
    self.db.commit()
    self.db.refresh(report)
    
    return report