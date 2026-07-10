# ==========================================
# 파일 위치 :
# moneypilot_back/app/routers/admin_router.py
# 역할 :
# 관리자 대시보드
# 토큰 사용량 통계
# 비용 통계
# 토큰 제한 조회/수정
# 시스템 사용량 조회
# 금융상품 데이터 갱신 시각 조회
# ==========================================
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.admin_schema import (
    DashboardResponse,
    UserTokenUsageResponse,
    FeatureTokenUsageResponse,
    DailyCostResponse,
    TokenLimitResponse,
    TokenLimitUpdateRequest,
    SystemStatusResponse,
    ProductLastUpdateResponse,
)
from app.services.admin_service import AdminService

router = APIRouter()


# ==========================================
# 관리자 대시보드
# ==========================================
@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="관리자 대시보드",
    description="관리자 메인 화면 통계를 조회합니다.",
)
async def dashboard(
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_dashboard()


# ==========================================
# 사용자별 토큰 사용량
# ==========================================
@router.get(
    "/token/users",
    response_model=list[UserTokenUsageResponse],
    summary="사용자별 토큰 사용량",
    description="사용자별 토큰 사용량과 비용을 조회합니다.",
)
async def get_user_token_usage(
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_user_token_usage()


# ==========================================
# 기능별 토큰 사용량
# ==========================================
@router.get(
    "/token/features",
    response_model=list[FeatureTokenUsageResponse],
    summary="기능별 토큰 사용량",
    description="기능별 토큰 사용량과 비용을 조회합니다.",
)
async def get_feature_token_usage(
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_feature_token_usage()


# ==========================================
# 일별 예상 비용
# ==========================================
@router.get(
    "/cost/daily",
    response_model=list[DailyCostResponse],
    summary="일별 예상 비용",
    description="일별 OpenAI 예상 비용을 조회합니다.",
)
async def get_daily_cost(
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_daily_cost()


# ==========================================
# 토큰 제한 조회
# ==========================================
@router.get(
    "/token-limit",
    response_model=TokenLimitResponse,
    summary="토큰 제한 조회",
    description="현재 일일 토큰 제한을 조회합니다.",
)
async def get_token_limit(
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_token_limit()


# ==========================================
# 토큰 제한 수정
# ==========================================
@router.put(
    "/token-limit",
    response_model=TokenLimitResponse,
    summary="토큰 제한 수정",
    description="일일 토큰 제한을 최초 설정하거나 수정합니다.",
)
async def update_token_limit(
    request: TokenLimitUpdateRequest,
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.update_token_limit(request.daily_token_limit)


# ==========================================
# 시스템 사용량
# ==========================================
@router.get(
    "/system",
    response_model=SystemStatusResponse,
    summary="시스템 사용량",
    description="CPU, RAM 사용량을 조회합니다.",
)
async def get_system_status(
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_system_status()


# ==========================================
# 금융상품 마지막 갱신 시각
# ==========================================
@router.get(
    "/product-update",
    response_model=ProductLastUpdateResponse,
    summary="금융상품 마지막 갱신 시각",
    description="예금, 적금, 보험 상품 데이터의 마지막 갱신 시각을 조회합니다.",
)
async def get_product_last_update(
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_financial_product_last_update()