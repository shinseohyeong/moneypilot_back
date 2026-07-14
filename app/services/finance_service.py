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

from app.rag.rag_service import upsert_rag_document
from app.rag.rag_constants import RagDomain, RagSourceTable
from app.rag.builders.finance_profile_builder import build_finance_profile_documents

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
    '''
    Raises:
        HTTPException(409): # 이미 프로필이 존재할 때.
    '''
    
    existing = db.query(FinanceProfile).filter(
        FinanceProfile.user_id == user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 금융 프로필이 존재합니다. 수정은 PATCH /api/finance/profile 를 사용하세요.",
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
    logger.info(f"금융 프로필 등록 완료 — user_id={user_id}")

    # mp_rag_001 — 금융 프로필 RAG 저장
    try:
        documents = build_finance_profile_documents(profile)
        for doc in documents :
            upsert_rag_document(
                user_id=profile.user_id,
                domain=RagDomain.USER_PROFILE,
                source_type=RagSourceTable.FINANCE_PROFILES,
                source_id=profile.user_id,
                document_key=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"],
            )
        logger.info(f"금융 프로필 RAG 저장 완료 — user_id={user_id}")
    except Exception as e:
        logger.error(f"금융 프로필 RAG 저장 실패 — user_id={user_id}: {e}")

    return profile


def get_profile(db: Session, user_id: int) -> FinanceProfile:
    """mp_finance_002 — 금융 프로필 조회."""
    return _get_profile_or_404(db, user_id)


def update_profile(db: Session, user_id: int, body: FinanceProfileUpdate) -> FinanceProfile:
    """mp_finance_003 — 금융 프로필 부분 수정."""
    profile = _get_profile_or_404(db, user_id)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    logger.info(f"금융 프로필 수정 완료 — user_id={user_id}, fields={list(update_data.keys())}")

    # mp_rag_001 — 수정 시 RAG 재저장 (upsert라 덮어씀)
    try:
        documents = build_finance_profile_documents(profile)
        for doc in documents:
            upsert_rag_document(
                user_id=profile.user_id,
                domain=RagDomain.USER_PROFILE,
                source_type=RagSourceTable.FINANCE_PROFILES,
                source_id=profile.user_id,
                document_key=doc["id"],
                content=doc["content"],
                metadata=doc["metadata"],
            )
        logger.info(f"금융 프로필 RAG 재저장 완료 — user_id={user_id}")
    except Exception as e:
        logger.error(f"금융 프로필 RAG 재저장 실패 — user_id={user_id}: {e}")

    return profile

def get_user_finance_profile(db: Session, user_id: int) -> dict | None:
    """
    mp_agent_001 — 에이전트가 유저의 금융 프로필을 조회할 때 사용하는 Tool.

    LangGraph 에이전트가 추천 계산 전 유저의 금융 정보를 가져올 때 호출한다.
    4번 담당의 recommend_portfolio_tool과 5번 담당의 에이전트 graph.py에서
    import하여 사용한다.

    Args:
        db: DB 세션
        user_id: 조회할 유저 ID

    Returns:
        dict with monthly_salary, fixed_expense, risk_type,
              investment_goal, target_saving_amount
        프로필이 없으면 None
    """
    profile = db.query(FinanceProfile).filter(
        FinanceProfile.user_id == user_id
    ).first()

    if not profile:
        return None

    return {
        "monthly_salary": profile.monthly_salary,
        "fixed_expense": profile.fixed_expense,
        "risk_type": profile.risk_type,
        "investment_goal": profile.investment_goal,
        "target_saving_amount": profile.target_saving_amount,
    }

def get_risk_profile(db: Session, user_id: int) -> str | None:
    """
    mp_agent_002 — 에이전트가 유저의 위험성향을 빠르게 조회할 때 사용하는 Tool.

    에이전트가 포트폴리오 배분 비율을 결정하기 직전 위험성향만 빠르게 확인할 때 호출한다.
    finance_profiles 테이블의 risk_type 단일 컬럼만 조회하여 응답 속도를 최소화한다.

    Args:
        db: DB 세션
        user_id: 조회할 유저 ID

    Returns:
        'conservative', 'neutral', 'aggressive' 중 하나
        프로필이 없으면 None
    """
    # risk_type 컬럼만 조회 (속도 최적화)
    result = db.query(FinanceProfile.risk_type).filter(
        FinanceProfile.user_id == user_id
    ).first()

    if not result:
        return None

    risk_type = result[0]  # 튜플의 첫 번째 값

    # 한글 → 영문 변환 (명세 준수)
    RISK_TYPE_MAP = {
        "안정형": "conservative",
        "중립형": "neutral",
        "공격형": "aggressive",
    }

    return RISK_TYPE_MAP.get(risk_type, risk_type)