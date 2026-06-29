# app/core/disclaimer.py

INVESTMENT_DISCLAIMER = (
    "본 서비스의 정보는 투자 권유가 아니며, "
    "주식 시세와 뉴스 기반 참고 정보입니다. "
    "투자 판단과 책임은 사용자 본인에게 있습니다."
)


def get_investment_disclaimer() -> str:
    """
    주식/뉴스/챗봇/리포트/알림에서 공통으로 사용하는 투자 유의 문구를 반환합니다.
    """
    return INVESTMENT_DISCLAIMER