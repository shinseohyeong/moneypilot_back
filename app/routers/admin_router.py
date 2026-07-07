# ==========================================
# 파일 위치 :
# moneypilot_back/app/routers/admin_router.py
# 역할 :
# 사용자 사용량 조회
# 일일 사용한도 제한 수정
# 총 api비용 확인
# ==========================================
from fastapi import APIRouter,Depends, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.admin_service import AdminService
from app.schemas.admin_schema import (
    DashboardResponse,
    TokenLimitUpdateRequest
)

router = APIRouter(tags=["Admin"])

# 관리자 로그인 auth_route에 따로 만들어 놓아야함

# ==========================================
# 관리자 대시보드
# GET
# /api/admin/dashboard
# ==========================================
@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="관리자 대시보드",
    description="관리자 메인 화면 통계를 조회합니다."
)
async def dashboard(
    db: Session = Depends(get_db)
):
    service = AdminService(db)
    return service.get_dashboard()

# ==========================================
# 사용자 사용량 조회
# GET
# /api/admin/usage
# ==========================================
@router.get(
    "/usage",
    summary="사용자 사용량 조회",
    description="사용자가 사용한 토큰량과 금액을 조회합니다."
)
async def get_usage_list(
    db:Session = Depends(get_db)
):
    service = AdminService(db)
    return service.get_usage_list()
    
# ==========================================
# 특정 사용자 사용량 조회
# GET
# /api/admin/usage/{user_id}
# ==========================================
@router.get(
    "/usage/{user_id}",
    summary="특정 사용자 사용량 조회",
    description="특정 사용자가 사용한 토큰량과 금액을 조회합니다."
)
async def get_user_usage(
    user_id: int,
    db:Session = Depends(get_db)
):
    service = AdminService(db)
    return service.get_user_usage(
        user_id
    )

# ==========================================
# 사용자 사용량 제한
# GET 
# /api/admin/token-limit
# ==========================================
@router.get(
    "/token-limit",
    summary="현재 사용사 사용량 제한",
    description="현재 하루 사용량 제한범위 설정."
)
async def token_limit(
    db:Session = Depends(get_db)
):
    service = AdminService(db)
    return service.get_token_limit()
    
# ==========================================
# 사용자 사용량 변경
# PATCH 
# /api/admin/token-limit
# ==========================================
@router.patch(
    "/token-limit",
    summary="현재 사용사 사용량 제한범위 변경",
    description="현재 하루 사용량 제한범위 설정 변경함."
)
async def update_limit(
    body : TokenLimitUpdateRequest,
    db: Session = Depends(get_db)
):
    service = AdminService(db)
    return service.update_token_limit(
        body.daily_token_limit
    )