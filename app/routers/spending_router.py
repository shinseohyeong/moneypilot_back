from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.spending_analysis import (
    MonthlyAnalysisRequest,
    MonthlySummaryResponse,
    CategorySpendingResponse,
    MonthlyOverspendingResponse,
    ExpenseTypesResponse,
    MonthlyCardSpendingResponse
)
from app.services.spending_analysis_service import (
    SpendingAnalysisService,
    SpendingService,
)

router = APIRouter()


def get_spending_analysis_service(
    db: Session = Depends(get_db),
) -> SpendingAnalysisService:
    return SpendingAnalysisService(db)

def get_spending_service(db: Session = Depends(get_db)) -> SpendingService:
    return SpendingService(db)


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
    summary="월별 요약(총수입, 월급, 총지출, 고정비, 변동비, 여유자금, 전월대비 지출증감액, 전월 대비 지출 증감률) 조회",
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
    
# --------------------------------------------------------------
#  월별 고정비 / 변동비 조회
# --------------------------------------------------------------
@router.get(
    "/monthly/{month}/expense-types",
    response_model=ExpenseTypesResponse,
    summary="월별 고정/변동 금액, 총지출 기준 고정/변동 비율 조회",
)
def get_monthly_expense_types(
    month: str,
    db: Session = Depends(get_db),
):
    """
    월별 고정비/변동비 금액과 총수입 대비 비율 조회
    - fixed_expense.amount: 고정비 금액
    - fixed_expense.ratio: 총수입 대비 고정비 비율
    - variable_expense.amount: 변동비 금액
    - variable_expense.ratio: 총수입 대비 변동비 비율
    """
    # JWT 인증 완성 후 current_user.id로 변경
    user_id = 1
    service = SpendingAnalysisService(db)
    
    return service.get_monthly_expense_types(
        user_id=user_id,
        month=month,
    )
    

# --------------------------------------------------------------
#  카테고리
# --------------------------------------------------------------
@router.post(
    "/monthly/{month}/categories",
    response_model=list[CategorySpendingResponse],
    summary="월별 카테고리별 지출 분석 저장",
)
def save_monthly_category_spendings(
    month: str,
    service: SpendingService = Depends(get_spending_service),
):
    """
    특정 월의 카테고리별 지출 정보 조회
    - 카테고리별 지출 금액
    - 전체 지출 대비 비율
    """
    
    # JWT 인증 완성 후 current_user.id로 변경
    user_id = 1
    
    return service.save_monthly_category_spendings(
        user_id=user_id,
        month=month,
    )

# --------------------------------------------------------------
#  카테고리 - 과소비
# --------------------------------------------------------------
@router.get(
    "/monthly/{month}/overspending",
    response_model=MonthlyOverspendingResponse,
    summary="월별 과소비 카테고리 조회",
)
def get_monthly_overspending_categories(
    month: str,
    service: SpendingService = Depends(get_spending_service),
):
    """
    월별 과소비 카테고리 후보 조회
    기준 :
    - 이번 달 가장 많이 쓴 카테고리 TOP 3
    - 전월보다 많이 늘어난 카테고리 TOP 3
    """
    # JWT 인증 완성 후 current_user.id로 변경
    user_id = 1
    
    return service.get_monthly_overspending_categories(
        user_id=user_id,
        month=month,
    )

# --------------------------------------------------------------
#  카드별/현금별 사용금액 조회
# --------------------------------------------------------------
@router.post(
    "/monthly/{month}/cards",
    response_model=MonthlyCardSpendingResponse,
    summary="월별 카드별 사용금액 분석 저장",
)
def save_monthly_card_spendings(
    month: str,
    service: SpendingService = Depends(get_spending_service),
):
    """
    특정 월의 거래내역을 카드별/현금별로 합산하여 저장
    - statement_id가 있는 거래는 카드명 기준으로 계산
    - statement_id가 없는 거래는 현금으로 계산
    - 총지출 대비 사용비율 계산
    """
    # JWT 인증 완성 후 current_user.id로 변경
    user_id = 1
    
    card_spendings = service.save_monthly_card_spendings(
        user_id=user_id,
        month=month,
    )
    
    return service.get_monthly_card_spendings(
        user_id=user_id,
        month=month,
    )
    
    
@router.get(
    "/monthly/{month}/cards",
    response_model=MonthlyCardSpendingResponse,
    summary="월별 카드별 사용금액 조회",
)
def get_monthly_card_spendings(
    month: str,
    service: SpendingService = Depends(get_spending_service),
):
    """
    저장된 월별 카드별 사용금액 조회
    - 카드명
    - 카드별 사용금액
    - 현금 사용금액
    - 총지출 대비 사용비율
    """
    
    # JWT 인증 완성 후 current_user.id로 변경
    user_id = 1
    
    return service.get_monthly_card_spendings(
        user_id=user_id,
        month=month,
    )
