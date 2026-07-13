# ==========================================
# 파일 위치 : app/schemas/admin_schema.py
# 역할 : API 요청/응답 스키마 정의
#       DB모델과 분리함으로써 API 응답 형태를 독립적으로 관리
# ==========================================
from datetime import datetime

from pydantic import BaseModel, Field
# ==========================================
# 관리자 대시보드
# ==========================================
class DashboardResponse(BaseModel):
    total_users: int = Field(..., description="전체 회원 수")
    today_tokens: int = Field(..., description="오늘 사용 토큰 수")
    today_cost: float = Field(..., description="오늘 발생 비용")
    monthly_cost: float = Field(..., description="이번 달 발생 비용")
    total_cost: float = Field(..., description="누적 비용")
    statement_count: int = Field(..., description="업로드된 명세서 개수")
    ocr_success_rate: float = Field(..., description="OCR 성공률")
    today_transaction: int = Field(..., description="오늘 거래내역 수")
    month_transaction: int = Field(..., description="이번 달 거래내역 수")

# ==========================================
# 사용자별 토큰 사용량
# ==========================================
class UserTokenUsageResponse(BaseModel):
    user_id: int
    username: str
    total_tokens: int
    estimated_cost: float

# ==========================================
# 기능별 토큰 사용량
# ==========================================
class FeatureTokenUsageResponse(BaseModel):
    feature_type: str
    total_tokens: int
    estimated_cost: float

# ==========================================
# 일별 비용
# ==========================================
class DailyCostResponse(BaseModel):
    date: datetime
    cost: float

# ==========================================
# 토큰 제한 조회
# ==========================================
class TokenLimitResponse(BaseModel):
    daily_token_limit: int
    is_active: bool

# ==========================================
# 토큰 제한 수정
# ==========================================
class TokenLimitUpdateRequest(BaseModel):
    daily_token_limit: int = Field(..., gt=0)

# ==========================================
# 시스템 상태
# ==========================================
class SystemStatusResponse(BaseModel):
    cpu_usage: float
    ram_usage: float

# ==========================================
# 금융상품 마지막 갱신
# ==========================================
class ProductLastUpdateResponse(BaseModel):
    deposit_updated_at: datetime | None
    saving_updated_at: datetime | None
    insurance_updated_at: datetime | None