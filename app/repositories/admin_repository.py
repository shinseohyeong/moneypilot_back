# ==========================================
# 파일 위치 : app/repositories/admin_repository.py
# 역할 : admin 관련 DB 접근 담당
# 담당:
# 1. 관리자 계정 로그인
# 2. 사용자 사용량 조회
# 3. 사용자 사용량 제한
# Service에서 비즈니스 로직을 처리하고
# Repository는 DB CRUD만 담당
# ==========================================
from datetime import date
from sqlalchemy import func

from app.models.user_model import User
from app.models import (TokenUsageLog, TokenLimitSetting)

class AdminRepository:
    def __init__(self, db):
        self.db = db
        
    # ======================================
    # token_usage_logs 테이블 조회
    # ======================================
    def get_usage_list(self):
        return self.db.query(TokenUsageLog).order_by(TokenUsageLog.created_at.desc()).all()
      
    # ======================================
    # token_usage_logs 테이블에서 특정 사용자 조회
    # ======================================
    def get_user_usage(self, user_id: int):
        return (
        self.db.query(TokenUsageLog)
        .filter(TokenUsageLog.user_id == user_id)
        .order_by(TokenUsageLog.created_at.desc())
        .all()
    )
      
    # ======================================
    # 사용량 제한 설정
    # ======================================
    def get_token_limit(self):
        return self.db.query(TokenLimitSetting).first()
    
    # ======================================
    # 사용량 제한 변경
    # ======================================
    def update_token_limit(self, daily_token_limit: int):
        limit_setting = self.db.query(TokenLimitSetting).first()
        if limit_setting:
            limit_setting.daily_token_limit = (daily_token_limit)
        else:
            limit_setting = TokenLimitSetting(daily_token_limit=daily_token_limit)
            self.db.add(limit_setting)
        self.db.flush()
        return limit_setting
    
    # ======================================
    # 전체 사용자 수
    # ======================================
    def count_users(self):
        return (
            self.db.query(User)
            .count()
        )


    # ======================================
    # 오늘 사용된 총 토큰
    # ======================================
    def get_today_token_sum(self):
        return (
            self.db.query(
                func.coalesce(
                    func.sum(TokenUsageLog.total_tokens),
                    0
                )
            )
            .filter(
                TokenUsageLog.usage_date == date.today()
            )
            .scalar()
        )


    # ======================================
    # 오늘 발생한 API 비용
    # ======================================
    def get_today_cost(self):
        return (
            self.db.query(
                func.coalesce(
                    func.sum(TokenUsageLog.estimated_cost),
                    0
                )
            )
            .filter(
                TokenUsageLog.usage_date == date.today()
            )
            .scalar()
        )


    # ======================================
    # 전체 누적 API 비용
    # ======================================
    def get_total_cost(self):
        return (
            self.db.query(
                func.coalesce(
                    func.sum(TokenUsageLog.estimated_cost),
                    0
                )
            )
            .scalar()
        )