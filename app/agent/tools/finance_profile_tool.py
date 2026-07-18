from sqlalchemy.orm import Session
from app.services import finance_service

def get_user_finance_profile_tool(db: Session, user_id: int) -> dict:
    """
    유저의 금융 프로필(연령대, 소득 수준, 투자 성향, 재무 목표)을 조회합니다. (mp_agent_001)
    """
    profile = finance_service.get_user_finance_profile(db, user_id)
    if not profile:
        return {
            "success": False,
            "data": None,
            "message": "등록된 금융 프로필이 없습니다."
        }
    
    return {
        "success": True,
        "data": profile,
        "message": "금융 프로필 조회가 완료되었습니다."
    }


def get_risk_profile_tool(db: Session, user_id: int) -> dict:
    """
    유저의 투자 위험성향(conservative, neutral, aggressive)을 빠르게 조회합니다. (mp_agent_002)
    """
    risk_type = finance_service.get_risk_profile(db, user_id)
    if not risk_type:
        return {
            "success": False,
            "data": None,
            "message": "등록된 투자 성향 정보가 없습니다."
        }
        
    return {
        "success": True,
        "data": {"risk_type": risk_type},
        "message": "투자 위험성향 조회가 완료되었습니다."
    }