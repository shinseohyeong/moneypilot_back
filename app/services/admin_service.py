# ==========================================
# 파일 위치 : moneypilot_back/app/services/admin_service.py
# 역할 : 관리자 계정 관련 비즈니스 로직
# 담당:
# 1. 관리자 계정 로그인
# 2. 사용자 사용량 및 비용 조회
# 3. 이용한도 조절
# ==========================================
from datetime import date
from sqlalchemy import func

from app.models.user_model import User
from app.models.admin_model import TokenUsageLog

from app.schemas.admin_schema import TokenUsageLogResponse, TokenLimitSettingResponse
from app.repositories.admin_repository import AdminRepository
    
class AdminService:
  def __init__(self, db):
    self.db = db
    self.repository = AdminRepository(db)
    
  # ==========================================
  # 관리자 대시보드
  # ==========================================
  def get_dashboard(self):
    return {
        "total_users": self.repository.count_users(),
        "today_tokens": self.repository.get_today_token_sum(),
        "today_cost": float(self.repository.get_today_cost()),
        "monthly_cost": float(self.repository.get_total_cost()),
    }
  
  # ==========================================
  # 사용자 사용량 조회
  # 역할 : 사용자가 사용한 토큰량과 금액을 조회
  # return:
  # 사용자 이름과 사용량, 비용 정보
  # ==========================================
  def get_usage_list(self):
    # DB에서 모든 사용량 로그 조회
    usage_logs = (self.repository.get_usage_list())
    # Pydantic 모델로 변환하여 반환
    return [TokenUsageLogResponse.model_validate(log) for log in usage_logs]
  
  # ==========================================
  # 특정 사용자 사용량 조회
  # 역할 : 특정 사용자가 사용한 토큰량과 금액을 조회
  # return:
  # 사용자 이름과 사용량, 비용 정보
  # ==========================================
  def token_usage(self, user_id: int):
    # DB에서 특정 사용자의 사용량 로그 조회
    usage_logs = self.repository.get_user_usage(user_id)
    # Pydantic 모델로 변환하여 반환
    return [TokenUsageLogResponse.model_validate(log) for log in usage_logs]
  
  # ==========================================
  # 사용자 사용량 제한
  # 역할 : 하루 사용량 제한 설정
  # return:
  # 현재 하루 사용량 제한 범위
  # ==========================================
  def get_token_limit(self):
    # DB에서 사용량 제한 설정 조회
    limit_setting = self.repository.get_token_limit()
    if limit_setting:
      return TokenLimitSettingResponse.model_validate(limit_setting)
    else:
      return None
    
  # ==========================================
  # 사용자 사용량 변경
  # 역할 : 하루 사용량 제한 설정 변경
  # return:
  # 변경된 하루 사용량 제한 범위
  # ==========================================
  def update_token_limit(self, daily_token_limit: int):
    limit = self.repository.update_token_limit(daily_token_limit)
    self.db.commit()
    self.db.refresh(limit)
    return TokenLimitSettingResponse.model_validate(limit)