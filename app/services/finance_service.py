"""
services/finance_service.py — 금융 프로필 도메인 비즈니스 로직
팀 모델 기준: age_group, income_level, investment_type, financial_goal (문자열)
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
    existing = db.query(FinanceProfile).filter(
        FinanceProfile.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 금융 프로필이 존재합니다. 수정은 PATCH를 사용하세요.",
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
    logger.info(f"금융 프로필 등록 완료 — user_id={user_id}")
    return profile


def get_profile(db: Session, user_id: int) -> FinanceProfile:
    return _get_profile_or_404(db, user_id)


def update_profile(db: Session, user_id: int, body: FinanceProfileUpdate) -> FinanceProfile:
    profile = _get_profile_or_404(db, user_id)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    logger.info(f"금융 프로필 수정 완료 — user_id={user_id}")
    return profile