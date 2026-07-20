import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user_model import FinanceProfile
from app.schemas.finance_profile import FinanceProfileCreate, FinanceProfileUpdate

from app.rag.ingestors.finance_profile_ingestor import ingest_finance_profile

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
    existing = db.query(FinanceProfile).filter(
        FinanceProfile.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 금융 프로필이 존재합니다. 수정은 PATCH /api/finance/profile 를 사용하세요.",
        )

    # 연봉 자동 계산 로직 복원
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
    logger.info(f"금융 프로필 등록 완료 — user_id={user_id}")

    # mp_rag_001 — 금융 프로필 RAG 저장
    try:
        ingest_finance_profile(profile.user_id, profile)
        logger.info(f"금융 프로필 RAG 저장 완료 — user_id={user_id}")
    except Exception as e:
        logger.error(f"금융 프로필 RAG 저장 실패 — user_id={user_id}: {e}")

    return profile


def get_profile(db: Session, user_id: int) -> FinanceProfile:
    """금융 프로필 조회."""
    return _get_profile_or_404(db, user_id)


def update_profile(db: Session, user_id: int, body: FinanceProfileUpdate) -> FinanceProfile:
    """금융 프로필 부분 수정."""
    profile = _get_profile_or_404(db, user_id)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)
    logger.info(f"금융 프로필 수정 완료 — user_id={user_id}, fields={list(update_data.keys())}")

    # mp_rag_001 — 수정 시 RAG 재저장 (upsert라 덮어씀)
    try:
        ingest_finance_profile(profile.user_id, profile)
        logger.info(f"금융 프로필 RAG 재저장 완료 — user_id={user_id}")
    except Exception as e:
        logger.error(f"금융 프로필 RAG 재저장 실패 — user_id={user_id}: {e}")

    return profile

# ==========================================
# 에이전트 툴(Tool) 연동용 핵심 DB 조회 함수들
# ==========================================

def get_user_finance_profile(db: Session, user_id: int) -> dict | None:
    """
    mp_agent_001 — 에이전트가 유저의 금융 프로필을 조회할 때 사용하는 Tool.
    """
    profile = db.query(FinanceProfile).filter(
        FinanceProfile.user_id == user_id
    ).first()

    if not profile:
        return None

    return {
        "monthly_salary": float(profile.monthly_salary),
        "fixed_expense": float(profile.fixed_expense) if profile.fixed_expense else 0.0,
        "risk_type": profile.risk_type,
        "investment_goal": profile.investment_goal,
        "target_saving_amount": float(profile.target_saving_amount) if profile.target_saving_amount else 0.0,
    }


def get_risk_profile(db: Session, user_id: int) -> str | None:
    """
    mp_agent_002 — 에이전트가 유저의 위험성향을 빠르게 조회할 때 사용하는 Tool.
    """
    result = db.query(FinanceProfile.risk_type).filter(
        FinanceProfile.user_id == user_id
    ).first()

    if not result:
        return None

    risk_type = result[0]

    RISK_TYPE_MAP = {
        "안정형": "conservative",
        "중립형": "neutral",
        "공격형": "aggressive",
    }

    return RISK_TYPE_MAP.get(risk_type, risk_type)