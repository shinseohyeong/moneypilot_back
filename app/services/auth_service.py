import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from jose import ExpiredSignatureError, JWTError

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_token_type, TOKEN_TYPE_REFRESH,
)
from app.models.user_model import User, RefreshToken
from app.schemas.auth import SignupRequest, LoginRequest

logger = logging.getLogger(__name__)


def signup(db: Session, body: SignupRequest) -> User:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 사용 중인 이메일입니다.")

    user = User(
        email=body.email,
        password=hash_password(body.password),
        username=body.username,
        login_type="LOCAL",
        birth_date=body.birth_date,
        gender=body.gender,
        role="USER",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"회원가입 완료 — user_id={user.id}")
    return user


def login(db: Session, body: LoginRequest) -> dict:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.password or not verify_password(body.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다.")
    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "비활성화된 계정입니다.")

    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token(user.id)

    db.add(RefreshToken(
        user_id=user.id,
        refresh_token=refresh_token_str,
        is_revoked=False,
    ))
    db.commit()
    logger.info(f"로그인 성공 — user_id={user.id}")
    return {"access_token": access_token, "refresh_token": refresh_token_str, "role": user.role,}


def refresh_access_token(db: Session, refresh_token_str: str) -> str:
    try:
        payload = decode_token(refresh_token_str)
    except ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh_token이 만료되었습니다. 다시 로그인해주세요.")
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않은 토큰입니다.")

    if get_token_type(payload) != TOKEN_TYPE_REFRESH:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "refresh_token이 아닙니다.")

    stored = db.query(RefreshToken).filter(
        RefreshToken.refresh_token == refresh_token_str
    ).first()
    if not stored:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않은 토큰입니다.")
    if stored.is_revoked:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "이미 로그아웃된 토큰입니다. 다시 로그인해주세요.")

    user_id = int(payload.get("sub"))
    return create_access_token(user_id)


def logout(db: Session, refresh_token_str: str) -> None:
    stored = db.query(RefreshToken).filter(
        RefreshToken.refresh_token == refresh_token_str
    ).first()
    if stored and not stored.is_revoked:
        stored.is_revoked = True
        db.commit()
    else:
        logger.info("로그아웃 요청 — 이미 취소되었거나 존재하지 않는 토큰")