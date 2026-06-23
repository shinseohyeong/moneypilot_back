"""
services/finance_service.py — 금융 프로필 도메인 비즈니스 로직
<<<<<<< Updated upstream
팀 모델 기준: age_group, income_level, investment_type, financial_goal (문자열)
=======

실제 팀 모델 기준 (숫자 필드):
  monthly_salary / annual_salary 는 NOT NULL → 등록 시 필수.
  annual_salary 미입력 시 monthly_salary × 12 로 자동 계산.
>>>>>>> Stashed changes
"""

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import FinanceProfile
from app.schemas.finance_profile import FinanceProfileCreate, FinanceProfileUpdate

logger = logging.getLogger(__name__)

MONTHS_PER_YEAR = 12


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
<<<<<<< Updated upstream
=======
    """
    mp_finance_001 — 금융 프로필 최초 등록.
    annual_salary 미입력 시 monthly_salary × 12 로 자동 계산.

    Raises:
        HTTPException(409): 이미 프로필이 존재할 때.
    """
>>>>>>> Stashed changes
    existing = db.query(FinanceProfile).filter(
        FinanceProfile.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 금융 프로필이 존재합니다. 수정은 PATCH를 사용하세요.",
        )

    annual_salary = body.annual_salary or body.monthly_salary * MONTHS_PER_YEAR

    profile = FinanceProfile(
        user_id=user_id,
        monthly_salary=body.monthly_salary,
        annual_salary=annual_salary,
        fixed_expense=body.fixed_expense or 0,
        risk_type=body.risk_type,
        investment_goal=body.investment_goal,
        target_saving_amount=body.target_saving_amount or 0,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
<<<<<<< Updated upstream
    logger.info(f"금융 프로필 등록 완료 — user_id={user_id}")
=======

    logger.info(f"금융 프로필 등록 완료 — user_id={user_id}, risk_type={body.risk_type}")
>>>>>>> Stashed changes
    return profile


def get_profile(db: Session, user_id: int) -> FinanceProfile:
    return _get_profile_or_404(db, user_id)


def update_profile(db: Session, user_id: int, body: FinanceProfileUpdate) -> FinanceProfile:
<<<<<<< Updated upstream
=======
    """
    mp_finance_003 — 금융 프로필 부분 수정.
    monthly_salary만 바뀌고 annual_salary가 함께 안 오면 연봉도 자동 재계산.
    """
>>>>>>> Stashed changes
    profile = _get_profile_or_404(db, user_id)
    update_data = body.model_dump(exclude_unset=True)
<<<<<<< Updated upstream
    for key, value in update_data.items():
        setattr(profile, key, value)
=======

    if "monthly_salary" in update_data and "annual_salary" not in update_data:
        update_data["annual_salary"] = update_data["monthly_salary"] * MONTHS_PER_YEAR

    for field, value in update_data.items():
        setattr(profile, field, value)

>>>>>>> Stashed changes
    db.commit()
    db.refresh(profile)
    logger.info(f"금융 프로필 수정 완료 — user_id={user_id}")
    return profile