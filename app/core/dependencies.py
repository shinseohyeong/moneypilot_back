"""
core/dependencies.py — get_current_user (JWT 검증 버전)
"""

import logging

from jose import ExpiredSignatureError, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token, get_token_type, TOKEN_TYPE_ACCESS
from app.models.user_model import User

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "토큰이 만료되었습니다. 다시 로그인해주세요.")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않은 토큰입니다.")

    if get_token_type(payload) != TOKEN_TYPE_ACCESS:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "access_token이 아닙니다.")

    raw_user_id = payload.get("sub")
    if raw_user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "토큰에 사용자 정보가 없습니다.")

    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "토큰의 사용자 식별자 형식이 올바르지 않습니다.")

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "존재하지 않거나 비활성화된 사용자입니다.")

    return user

def admin_required(
    current_user=Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="관리자만 접근 가능합니다."
        )

    return current_user