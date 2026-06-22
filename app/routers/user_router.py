"""
routers/user_router.py — 사용자 프로필 API
prefix(/api/users)는 main.py에서 부여
GET   /api/users/me
PATCH /api/users/me
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.services import user_service
from app.models.user_model import User
from app.schemas.user import UserProfileUpdate, UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="내 정보 조회",
)
def get_my_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="내 정보 수정",
    responses={400: {"description": "변경할 필드 없음"}},
)
def update_my_info(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    return user_service.update_profile(db, current_user, body)