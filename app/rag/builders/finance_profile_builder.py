"""
금융 프로필 데이터를 RAG 문서로 변환하는 builder 모듈
변환 대상: FinanceProfile (monthly_salary, fixed_expense, risk_type, investment_goal, target_saving_amount)
"""
from app.models.user_model import FinanceProfile
from app.rag.metadata import RagDomain, RagSourceType, RagCreatedBy


def build_finance_profile_documents(
    profile: FinanceProfile,
) -> list[dict]:
    """
    FinanceProfile 객체를 Chroma에 저장할 RAG 문서 목록으로 변환. (mp_rag_001)
    """
    parts = []
    if getattr(profile, "monthly_salary", None) is not None:
        parts.append(f"월 소득: {int(profile.monthly_salary):,}원")
    if getattr(profile, "annual_salary", None) is not None:
        parts.append(f"연 소득: {int(profile.annual_salary):,}원")
    if getattr(profile, "fixed_expense", None) is not None:
        parts.append(f"월 고정 지출: {int(profile.fixed_expense):,}원")
    if getattr(profile, "risk_type", None):
        parts.append(f"투자 성향: {profile.risk_type}")
    if getattr(profile, "investment_goal", None):
        parts.append(f"투자 목표: {profile.investment_goal}")
    if getattr(profile, "target_saving_amount", None) is not None:
        parts.append(f"목표 저축액: {int(profile.target_saving_amount):,}원")

    if not parts:
        return []

    rag_content = f"""
[사용자 금융 프로필 요약 정보]
{', '.join(parts)}
    """.strip()

    vector_id = build_finance_profile_vector_id(
        user_id=profile.user_id,
    )
    profile_id = getattr(profile, "id", None) or profile.user_id

    return [{
        "id": vector_id,
        "content": rag_content,
        "metadata": {
            "user_id": int(profile.user_id),
            "domain": RagDomain.FINANCE_PROFILE,
            "source_type": RagSourceType.FINANCE_PROFILE,
            "source_id": int(profile_id),
            "document_type": "summary",
            "created_by": RagCreatedBy.USER,
        },
    }]


def build_finance_profile_vector_id(
    user_id: int,
) -> str:
    """금융 프로필 RAG 문서의 고유 vector_id를 생성."""
    return (
        f"{RagDomain.FINANCE_PROFILE}:"
        f"{user_id}:"
        f"summary"
    )
