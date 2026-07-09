# ============================================================
# 파일 위치: app/services/user_risk_context_service.py
# 역할:
#   - 사용자 투자성향을 조회/정규화합니다.
#   - 팀원 사용자 자산 프로필 기능과 연결하기 전까지는 NORMAL 기본값을 사용합니다.
#   - 리포트, 알림, 챗봇에서 공통으로 재사용할 투자성향별 해석 문구를 제공합니다.
# ============================================================

from typing import Optional

from sqlalchemy.orm import Session


class UserRiskContextService:
    """
    사용자 투자성향 context를 제공하는 service입니다.

    투자성향 값:
    - SAFE: 안전형
    - NORMAL: 보통형
    - AGGRESSIVE: 위험형
    """

    DEFAULT_RISK_TYPE = "NORMAL"

    def __init__(self, db: Session):
        self.db = db

    def get_user_risk_type(self, user_id: int) -> str:
        """
        user_id 기준 사용자 투자성향을 반환합니다.

        현재는 팀원 파트의 사용자/자산 프로필 테이블 구조가 확정되기 전이므로
        기본값 NORMAL을 반환합니다.

        나중에 finance_profiles, user_profiles, user_settings 등 실제 테이블이 확정되면
        이 함수 내부에서 DB 조회 로직만 교체하면 됩니다.
        """
        # TODO:
        # 팀원 파트 투자성향 컬럼 확정 후 연결
        # 예시:
        # profile = self.db.query(FinanceProfile).filter(FinanceProfile.user_id == user_id).first()
        # return self._normalize_risk_type(profile.risk_type if profile else None)
        # 추후 확인해야 할 것 :
        # 투자성향 저장 테이블명
        # 투자성향 컬럼명
        # 저장 값 예시: 안전형/보통형/위험형 또는 SAFE/NORMAL/AGGRESSIVE

        return self.DEFAULT_RISK_TYPE

    def _normalize_risk_type(self, risk_type: Optional[str]) -> str:
        """
        DB에 저장된 투자성향 값을 SAFE / NORMAL / AGGRESSIVE 중 하나로 정규화합니다.
        """
        if not risk_type:
            return self.DEFAULT_RISK_TYPE

        normalized = str(risk_type).strip().upper()

        mapping = {
            "SAFE": "SAFE",
            "안전형": "SAFE",
            "STABLE": "SAFE",
            "CONSERVATIVE": "SAFE",

            "NORMAL": "NORMAL",
            "보통형": "NORMAL",
            "MODERATE": "NORMAL",
            "BALANCED": "NORMAL",

            "AGGRESSIVE": "AGGRESSIVE",
            "위험형": "AGGRESSIVE",
            "RISK": "AGGRESSIVE",
            "HIGH_RISK": "AGGRESSIVE",
        }

        return mapping.get(normalized, self.DEFAULT_RISK_TYPE)

    def get_risk_label(self, risk_type: str) -> str:
        """
        투자성향 영문 코드를 화면 표시용 한글 라벨로 변환합니다.
        """
        labels = {
            "SAFE": "안전형",
            "NORMAL": "보통형",
            "AGGRESSIVE": "위험형",
        }

        return labels.get(risk_type, "보통형")

    def get_interpretation_guide(self, risk_type: str) -> str:
        """
        투자성향별 뉴스/섹터/챗봇 해석 기준 문구를 반환합니다.
        """
        normalized = self._normalize_risk_type(risk_type)

        if normalized == "SAFE":
            return (
                "안전형 사용자는 변동성과 손실 가능성을 우선적으로 확인해야 합니다. "
                "부정 뉴스, 고위험 섹터, 급격한 가격 변동이 있는 경우 보수적으로 해석합니다."
            )

        if normalized == "AGGRESSIVE":
            return (
                "위험형 사용자는 이슈 집중도와 성장 가능성을 함께 참고할 수 있습니다. "
                "다만 긍정 요인이 있더라도 투자 권유가 아니며, 변동성과 손실 가능성을 함께 확인해야 합니다."
            )

        return (
            "보통형 사용자는 긍정 요인과 위험 요인을 균형 있게 확인해야 합니다. "
            "뉴스 흐름, 섹터 이슈, 가격 변동을 함께 참고합니다."
        )

    def get_risk_warning_level(self, risk_type: str) -> str:
        """
        투자성향별 위험 안내 수준을 반환합니다.

        리포트/알림/챗봇에서 문구 강도를 조절할 때 사용합니다.
        """
        normalized = self._normalize_risk_type(risk_type)

        if normalized == "SAFE":
            return "HIGH"

        if normalized == "AGGRESSIVE":
            return "MEDIUM"

        return "NORMAL"