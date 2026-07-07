# ==========================================
# 파일 위치 : app/schemas/admin_schema.py
# 역할 : API 요청/응답 스키마 정의
#       DB모델과 분리함으로써 API 응답 형태를 독립적으로 관리
# ==========================================
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, Field
# ==========================================
# 사용자 사용량 조회 응답 Schema
# 사용자가 챗봇 사용량 조회 및 사용량 제한 부여, 사용비용 알려줌
# ==========================================
class TokenUsageLogResponse(BaseModel):
  # 사용자 사용량 조회 테이블 고유 ID
  # DB PK
  id: int = Field(..., description="사용량 로그 ID")
  # 사용자 ID
  user_id: int = Field(..., description="사용자 ID")
  # 어떤 요청에서 발생했는지
  # consumption | finance | stock | news | chatbot | summary 등
  feature_type : str= Field(..., description="AI 사용 기능")
  # 예: gpt-4o-mini, text-embedding-3-small 등
  model_name : str= Field(..., description="사용한 AI 모델명")
  # 입력 토큰
  prompt_tokens: int = Field(0, description="입력 토큰 수")
  # 출력 토큰
  completion_tokens : int = Field(0, description="출력 토큰 수")
  # 질문을 vector로 바꾼 토큰
  embedding_tokens : int = Field(0, description="임베딩 생성 토큰 수")
  # 총합
  total_tokens : int = Field(0, description="총 사용 토큰 수")
  # 비용 계산용
  estimated_cost : Decimal=Field(0, description="예상 AI 사용 비용")
  # 사용 날짜
  usage_date : datetime = Field(..., description="사용 날짜")
   # 생성 시간
  created_at : datetime = Field(..., description="로그 생성 시간")
  
  class Config:
        from_attributes = True
        
class TokenLimitSettingResponse(BaseModel):
  # 사용자 사용량 제한 테이블 고유 ID
  # DB PK
  id: int = Field(..., description="사용량 제한 ID")
  # 하루 사용 가능량
  daily_token_limit : int = Field(..., gt=0, description="하루 사용 한도")
  # 사용 제한 여부
  is_active : bool = Field(..., description="사용 제한 활성화 여부")
  # 설정만든 날짜
  created_at :datetime= Field(..., description="설정 만든 날짜")
  # 재한 수정 날짜
  updated_at :datetime= Field(..., description="제한 수정한 날짜")
  
  class Config:
        from_attributes = True

# ==========================================
# 토큰 제한 변경 Request
# PATCH /api/admin/token-limit
# ==========================================        
class TokenLimitUpdateRequest(BaseModel):
  daily_token_limit: int

# ==========================================
# 관리자 대시보드 응답
# ==========================================  
class DashboardResponse(BaseModel):
    total_users: int
    today_tokens: int
    today_cost: float
    monthly_cost: float