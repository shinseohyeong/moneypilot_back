"""
services/user_service.py — 사용자 프로필 비즈니스 로직
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user_model import User
from app.schemas.user import UserProfileUpdate

logger = logging.getLogger(__name__)


def update_profile(db: Session, current_user: User, body: UserProfileUpdate) -> User:
    """내 정보 수정 (username / phone / password 부분 수정)"""
    update_data = body.model_dump(exclude_unset=True, exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="변경할 필드가 없습니다.",
        )

    if "password" in update_data:
        update_data["password"] = hash_password(update_data["password"])
        logger.info(f"비밀번호 변경 — user_id={current_user.id}")

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user