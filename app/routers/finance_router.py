"""
routers/finance_router.py — 금융 프로필 API

prefix(/api/finance)와 tags는 main.py의 include_router에서 부여하므로
이 파일에서는 경로만 정의한다.

엔드포인트:
  POST  /profile   금융 프로필 등록
  GET   /profile   금융 프로필 조회
  PATCH /profile   금융 프로필 수정
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services import finance_service
from app.models.user_model import User
from app.schemas.finance_profile import (
    FinanceProfileCreate,
    FinanceProfileUpdate,
    FinanceProfileResponse,
)

router = APIRouter()


@router.post(
    "/profile",
    response_model=FinanceProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="금융 프로필 등록",
    responses={409: {"description": "이미 금융 프로필이 존재함"}},
)
def create_finance_profile(
    body: FinanceProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinanceProfileResponse:
    return finance_service.create_profile(db, current_user.id, body)


@router.get(
    "/profile",
    response_model=FinanceProfileResponse,
    summary="금융 프로필 조회",
    responses={404: {"description": "금융 프로필 없음"}},
)
def get_finance_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinanceProfileResponse:
    return finance_service.get_profile(db, current_user.id)


@router.patch(
    "/profile",
    response_model=FinanceProfileResponse,
    summary="금융 프로필 수정",
    responses={404: {"description": "금융 프로필 없음"}},
)
def update_finance_profile(
    body: FinanceProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinanceProfileResponse:
    return finance_service.update_profile(db, current_user.id, body)