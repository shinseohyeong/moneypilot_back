"""
services/user_service.py — 사용자 프로필 비즈니스 로직
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user_model import User, RefreshToken
from app.schemas.user import UserProfileUpdate
from app.rag.retrievers.user_profile_retriever import UserProfileRetriever

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


def withdraw_user(db: Session, user_id: int) -> None:
    """
    회원 탈퇴 (soft delete).

    계정을 비활성화하고 발급된 refresh token을 폐기한 뒤,
    RAG에 저장된 개인 문서를 삭제한다. (mp_rag_003)
    비활성 계정은 로그인 시 차단된다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    # 1. 계정 비활성화
    user.is_active = False

    # 2. refresh token 폐기 (토큰 갱신 차단)
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
    ).update({"is_revoked": True})

    db.commit()
    logger.info(f"회원 탈퇴 처리 완료 — user_id={user_id}")

    # 3. RAG 개인 문서 삭제 (DB 처리 완료 후 실행)
    try:
        retriever = UserProfileRetriever()
        # user_id를 명시적으로 인자로 전달하여 해당 유저의 프로필 RAG 문서를 일괄 삭제
        retriever.delete_user_profile_docs(user_id=user_id)
        logger.info(f"RAG 문서 삭제 완료 — user_id={user_id}")
    except Exception as e:
        # RAG 서버 호출 실패 등이 실제 DB의 탈퇴 처리까지 트랜잭션 롤백시키지 않도록 로깅만 수행
        logger.exception(f"RAG 문서 삭제 실패 — user_id={user_id}: {e}")