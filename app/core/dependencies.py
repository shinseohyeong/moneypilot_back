"""
core/dependencies.py — get_db, get_current_user

※ 임시 버전: 인증(JWT) 구현 전까지 더미 유저를 반환한다.
   auth 기능 완성되면 get_current_user 내부만 실제 JWT 검증으로 교체.
"""

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user_model import User

logger = logging.getLogger(__name__)

# 더미 유저 ID — DB에 넣은 테스트 유저의 id로 맞출 것
DUMMY_USER_ID = 1


def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    임시 인증 — DB에서 DUMMY_USER_ID 유저를 반환한다.
    실제 JWT 인증은 auth 기능 구현 시 이 함수 내부를 교체.
    """