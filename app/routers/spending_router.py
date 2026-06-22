from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.spending_analysis import (
    MonthlyAnalysisRequest,
    MonthlySummaryResponse,
)
from app.services.spending_analysis_service import SpendingAnalysisService

router = APIRouter()


@router.post(
    "/monthly",
    response_model=MonthlySummaryResponse,
    summary="월별 분석 실행 및 저장",
)
def analyze_monthly_spending(
    request: MonthlyAnalysisRequest,
    db: Session = Depends(get_db),
) : 
    """
    거래내역 기반으로 월별 소비 분석하고 실행하고 저장한다
    
    계산 기준:
    - 총수입: finance_profiles.monthly_salary
    - 총지출: transactions.amount 합계
    - 고정비: transactions.expense_type="FIXED" 금액 합계
    - 변동비: 초지출 - 고정비
    - 여유자금: 총수입 - 총지출
    - 전월 대비 증감액/증감률: 전월 total_spending 기준
    """
    
    # JWT 인증 완성 후 current_user.id로 변경
    user_id = 1
    service = SpendingAnalysisService(db)
    
    return service.analyze_and_save_monthly_summary(
        user_id=user_id,
        month=request.month,
    )


@router.get(
    "/monthly/{month}",
    response_model=MonthlySummaryResponse,
    summary="월별 요약 조회",
)
def get_monthly_spending_summary(
    month: str,
    db: Session = Depends(get_db),
):
    """
    특정 월의 소비 요약 정보를 조회
    - 총수입, 월급, 총지출
    - 고정비, 변동비, 여유자금
    - 전월 대비 지출 증감액
    - 전월 대비 지출 증감률
    """
    
    # JWT 인증 완성 후 current_user.id로 변경
    user_id = 1
    service = SpendingAnalysisService(db)
    
    return service.get_monthly_summary_by_month(
        user_id=user_id,
        month=month,
    )


