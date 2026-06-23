"""
core/dependencies.py — get_db, get_current_user
임시 버전: 인증(JWT) 구현 전까지 더미 유저를 반환한다.
auth 기능 완성되면 get_current_user 내부만 실제 JWT 검증으로 교체.
"""

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user_model import User

logger = logging.getLogger(__name__)

DUMMY_USER_ID = 1


def get_current_user(db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.id == DUMMY_USER_ID).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"더미 유저(id={DUMMY_USER_ID})가 DB에 없습니다.",
        )

    return user