"""
금융 프로필 데이터를 RAG 문서로 변환하는 builder 모듈
변환 대상: FinanceProfile (monthly_salary, risk_type 등)
"""
from app.models.user_model import FinanceProfile
from app.rag.rag_constants import RagDomain, RagFeature, RagSourceTable


def build_finance_profile_documents(
    profile: FinanceProfile,
) -> list[dict]:
    """
    FinanceProfile 객체를 Chroma에 저장할 RAG 문서 목록으로 변환.

    프로필 정보를 자연어 텍스트로 변환하여 하나의 문서로 저장한다.
    에이전트가 유저 관련 문맥이 필요할 때 이 문서를 검색하여 활용한다.
    """
    parts = []

    if profile.monthly_salary:
        parts.append(f"월 소득 {profile.monthly_salary:,}원")
    if profile.annual_salary:
        parts.append(f"연 소득 {profile.annual_salary:,}원")
    if profile.fixed_expense:
        parts.append(f"고정 지출 {profile.fixed_expense:,}원")
    if profile.risk_type:
        parts.append(f"위험성향 {profile.risk_type}")
    if profile.investment_goal:
        parts.append(f"투자 목표 {profile.investment_goal}")
    if profile.target_saving_amount:
        parts.append(f"목표 저축액 {profile.target_saving_amount:,}원")

    if not parts:
        return []

    rag_content = f"""
    [사용자 금융 프로필]

    {', '.join(parts)}
    """.strip()

    vector_id = build_finance_profile_vector_id(
        user_id=profile.user_id,
    )

    return [{
        "id": vector_id,
        "content": rag_content,
        "metadata": {
            "user_id": int(profile.user_id),
            "domain": RagDomain.USER_PROFILE,
            "feature": RagFeature.FINANCE_PROFILE,
            "source_table": RagSourceTable.FINANCE_PROFILES,
            "source_id": int(profile.id),
            "document_type": "summary",
        },
    }]


def build_finance_profile_vector_id(
    user_id: int,
) -> str:
    """
    금융 프로필 RAG 문서의 고유 vector_id를 생성.
    유저당 하나의 문서라 user_id로 유니크.
    """
    return (
        f"{RagDomain.USER_PROFILE}:"
        f"{RagFeature.FINANCE_PROFILE}:"
        f"{user_id}:"
        f"summary"
    )