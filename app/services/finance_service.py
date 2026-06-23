"""
services/finance_service.py — 금융 프로필 도메인 비즈니스 로직

팀 모델 기준:
  - FinanceProfile: age_group, income_level, investment_type, financial_goal (전부 문자열)
  - 월급/연봉 숫자 컬럼이 없으므로 '연봉 자동계산' 같은 수치 로직은 없음.
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import FinanceProfile
from app.schemas.finance_profile import FinanceProfileCreate, FinanceProfileUpdate

logger = logging.getLogger(__name__)


def _get_profile_or_404(db: Session, user_id: int) -> FinanceProfile:
    profile = db.query(FinanceProfile).filter(
        FinanceProfile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="금융 프로필이 없습니다. 먼저 등록해주세요.",
        )
    return profile


def create_profile(db: Session, user_id: int, body: FinanceProfileCreate) -> FinanceProfile:
    """
    mp_finance_001 — 금융 프로필 최초 등록.

    Raises:
        HTTPException(409): 이미 프로필이 존재할 때.
    """
    existing = db.query(FinanceProfile).filter(
        FinanceProfile.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 금융 프로필이 존재합니다. 수정은 PATCH /api/finance/profile 를 사용하세요.",
        )

    profile = FinanceProfile(
        user_id=user_id,
        age_group=body.age_group,
        income_level=body.income_level,
        investment_type=body.investment_type,
        financial_goal=body.financial_goal,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    logger.info(f"금융 프로필 등록 완료 — user_id={user_id}, investment_type={body.investment_type}")
    return profile


def get_profile(db: Session, user_id: int) -> FinanceProfile:
    """mp_finance_002 — 금융 프로필 조회."""
    return _get_profile_or_404(db, user_id)


def update_profile(db: Session, user_id: int, body: FinanceProfileUpdate) -> FinanceProfile:
    """mp_finance_003 — 금융 프로필 부분 수정."""
    profile = _get_profile_or_404(db, user_id)

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    logger.info(f"금융 프로필 수정 완료 — user_id={user_id}, fields={list(update_data.keys())}")
    return profile