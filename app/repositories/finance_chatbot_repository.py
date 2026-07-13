# ==========================================
# 파일 위치: app/repositories/finance_chatbot_repository.py
# 역할:
# - 소비 데이터 기반 챗봇에 필요한 DB 데이터 조회
# - repository에서는 commit/rollback 금지
# ==========================================

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

# 실제 모델 파일명에 맞게 import 경로만 조정하면 됨
from app.models.user_model import FinanceProfile
from app.models.spending_analysis_model import (
    AnalysisReport,
    CategorySpending,
    MonthlySpendingSummary,
)
from app.models.transaction_model import Transaction


class FinanceChatbotRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_finance_profile_by_user_id(self, user_id: int) -> Optional[FinanceProfile]:
        """
        사용자 금융 프로필 조회
        - 월급
        - 고정비
        - 투자성향
        """
        return (
            self.db.query(FinanceProfile)
            .filter(FinanceProfile.user_id == user_id)
            .first()
        )

    def get_latest_monthly_spending_summary(
        self,
        user_id: int,
    ) -> Optional[MonthlySpendingSummary]:
        """
        사용자의 최신 월별 소비 요약 조회

        month 컬럼이 '2026-06' 형식이므로 문자열 내림차순 정렬로 최신 월 조회 가능
        """
        return (
            self.db.query(MonthlySpendingSummary)
            .filter(MonthlySpendingSummary.user_id == user_id)
            .order_by(MonthlySpendingSummary.month.desc())
            .first()
        )

    def get_category_spendings_by_summary_id(
        self,
        summary_id: int,
    ) -> List[CategorySpending]:
        """
        특정 월별 소비 요약에 연결된 카테고리별 소비 조회
        """
        return (
            self.db.query(CategorySpending)
            .filter(CategorySpending.summary_id == summary_id)
            .order_by(CategorySpending.category_amount.desc())
            .all()
        )

    def get_latest_analysis_report_by_summary_id(
        self,
        summary_id: int,
    ) -> Optional[AnalysisReport]:
        """
        특정 월별 소비 요약에 연결된 분석 리포트 조회
        """
        return (
            self.db.query(AnalysisReport)
            .filter(AnalysisReport.summary_id == summary_id)
            .first()
        )

    def get_monthly_transaction_total(
        self,
        user_id: int,
        month: str,
    ):
        """
        월별 소비 요약 데이터가 없거나 부족할 때 사용할 거래내역 합계 fallback

        주의:
        - transactions.amount는 소비 금액 기준으로 합산
        - repository에서는 commit/rollback 하지 않음
        """
        return (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(Transaction.user_id == user_id)
            .filter(Transaction.month == month)
            .scalar()
        )

    def get_recent_transactions(
        self,
        user_id: int,
        limit: int = 10,
    ) -> List[Transaction]:
        """
        필요 시 LLM prompt 참고용으로 사용할 최근 거래내역
        """
        return (
            self.db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .limit(limit)
            .all()
        )