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
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func

from app.models.user_model import User
from app.models.card_statement_model import CardStatement
from app.models.transaction_model import Transaction
from app.models.admin_model import (TokenUsageLog, TokenLimitSetting)
from app.models.financial_product_model import (DepositProduct, SavingProduct, InsuranceProduct)

KST = ZoneInfo("Asia/Seoul")

class AdminRepository:
    def __init__(self, db):
        self.db = db
        
    # ==========================================
    # 토큰 사용량 저장
    # ==========================================
    def create_token_usage_log(
        self,
        *,
        user_id: int,
        feature_type: str,
        model_name: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        embedding_tokens: int = 0,
        estimated_cost: Decimal = Decimal("0"),
    ):
        prompt_tokens = int(prompt_tokens or 0)
        completion_tokens = int(completion_tokens or 0)
        embedding_tokens = int(embedding_tokens or 0)

        usage_log = TokenUsageLog(
            user_id=user_id,
            feature_type=feature_type,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            embedding_tokens=embedding_tokens,
            total_tokens=(
                prompt_tokens
                + completion_tokens
                + embedding_tokens
            ),
            estimated_cost=estimated_cost,
            usage_date=datetime.now(KST).date(),
        )

        try:
            self.db.add(usage_log)
            self.db.commit()
            self.db.refresh(usage_log)

            return usage_log

        except Exception:
            self.db.rollback()
            raise
    
    # ==========================================
    # 전체 회원 수
    # ==========================================
    def count_users(self):
        return self.db.query(func.count(User.id)).scalar() or 0
    
    # 오늘 사용 토큰량
    def get_today_token_sum(self):
        today = date.today()
        result = (
            self.db.query(func.sum(TokenUsageLog.total_tokens))
            .filter(TokenUsageLog.usage_date == today)
            .scalar()
        )

        return result or 0
    
    # 오늘 사용된 비용
    def get_today_cost(self):
        today = date.today()
        result = (
            self.db.query(
                func.sum(TokenUsageLog.estimated_cost)
            )
            .filter(TokenUsageLog.usage_date == today)
            .scalar()
        )

        return result or 0
    
    # 이번달 비용
    def get_monthly_cost(self):
        month = date.today().strftime("%Y-%m")
        result = (
            self.db.query(
                func.sum(TokenUsageLog.estimated_cost)
            )
            .filter(
                func.date_format(
                    TokenUsageLog.usage_date,
                    "%Y-%m"
                ) == month
            )
            .scalar()
        )

        return result or 0
    
    # 총 비용
    def get_total_cost(self):
        result = (
            self.db.query(
                func.sum(TokenUsageLog.estimated_cost)
            )
            .scalar()
        )

        return result or 0
    
    # 명세서 개수
    def count_statements(self):
        return self.db.query(CardStatement).count()
    
    # OCR 성공
    def count_completed_statements(self):
        return (
            self.db.query(CardStatement)
            .filter(
                CardStatement.status == "COMPLETED"
            )
            .count()
        )
        
    # 오늘 거래량
    def count_today_transactions(self):
        today = date.today()
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.transaction_date == today
            )
            .count()
        )
        
    # 이번달 거래량
    def count_month_transactions(self):
        month = date.today().strftime("%Y-%m")
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.month == month
            )
            .count()
        )
        
    # 사용자 사용량 조회
    def get_user_token_usage(self):
        return (
            self.db.query(
                User.id,
                User.username,
                func.sum(TokenUsageLog.total_tokens),
                func.sum(TokenUsageLog.estimated_cost),
            )
            .join(
                TokenUsageLog,
                User.id == TokenUsageLog.user_id,
            )
            .group_by(
                User.id,
                User.username,
            )
            .all()
        )
        
    # 기능별 토큰 사용량 조회
    def get_feature_token_usage(self):
        return (
            self.db.query(
                TokenUsageLog.feature_type,
                func.sum(TokenUsageLog.total_tokens),
                func.sum(TokenUsageLog.estimated_cost),
            )
            .group_by(
                TokenUsageLog.feature_type
            )
            .all()
        )
        
    # 토큰량 제한 설정
    def update_token_limit(self, limit):
        setting = (
            self.db.query(TokenLimitSetting)
            .first()
        )
        if setting is None:
            setting = TokenLimitSetting(
                daily_token_limit=limit,
                is_active=True,
            )
            self.db.add(setting)
        else:
            setting.daily_token_limit = limit

        self.db.commit()
        self.db.refresh(setting)

        return setting
    
    # 금융상품 마지막 갱신 조회
    def get_financial_product_last_update(self):

        deposit_updated = (
            self.db.query(func.max(DepositProduct.updated_at))
            .scalar()
        )

        saving_updated = (
            self.db.query(func.max(SavingProduct.updated_at))
            .scalar()
        )

        insurance_updated = (
            self.db.query(func.max(InsuranceProduct.updated_at))
            .scalar()
        )

        return {
            "deposit_updated_at": deposit_updated,
            "saving_updated_at": saving_updated,
            "insurance_updated_at": insurance_updated,
        }
    
    # ==========================================
    # 일별 비용 조회
    # ==========================================
    def get_daily_cost(self):
        return (
            self.db.query(
                TokenUsageLog.usage_date,
                func.sum(TokenUsageLog.estimated_cost),
            )
            .group_by(TokenUsageLog.usage_date)
            .order_by(TokenUsageLog.usage_date.desc())
            .all()
        )
        
    # ==========================================
    # 토큰 제한 조회
    # ==========================================
    def get_token_limit(self):
        return (
            self.db.query(TokenLimitSetting)
            .order_by(TokenLimitSetting.id.desc())
            .first()
        )