# ==========================================
# 파일 위치 : app/schemas/card_statement.py
# 역할 : API 요청/응답 스키마 정의
#       DB모델과 분리함으로써 API 응답 형태를 독립적으로 관리
# ==========================================
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# ==========================================
# 카드 명세서 조회 응답 Schema
# 사용자가 파일 업로드 후
# 서버가 반환할 데이터 형태 정의
# DB Model과 분리하는 이유:
# DB 컬럼 변경이 API에 바로 영향을 주지 않게 하기 위함
# ==========================================
class CardStatementResponse(BaseModel):
    # 카드 명세서 고유 ID
    # DB PK
    id: int = Field(..., description="명세서 ID")
    # 업로드한 사용자
    user_id: int = Field(..., description="사용자 ID")
    # 실제 업로드한 파일명
    # 예: shinhan_202606.xlsx
    file_name: str = Field(
        ...,
        description="업로드 파일명"
    )
    # 서버에 저장된 위치
    # 예: uploads/shinhan.xlsx
    file_url: str = Field(
        ...,
        description="저장 파일 경로"
    )
    # 파일 확장자: XLSX, CSV
    file_type: str = Field(
        ...,
        description="파일 형식"
    )
    # 파일 처리 상태
    # 업로드 직후: PROCESSING
    # 파싱 완료: COMPLETED
    # 실패: FAILED
    status: str = Field(
        ...,
        description="처리 상태"
    )
    # 실패 원인 저장
    # 예:컬럼명이 맞지 않습니다
    error_message: Optional[str] = Field(
        None,
        description="실패 이유"
    )
    # 카드명
    # 예 : 신한카드, 국민카드
    card_name: str = Field(
        ...,
        description="카드명"
    )
    # 업로드 시간
    uploaded_at: datetime = Field(
        ...,
        description="업로드 시간"
    )
    # 처리 완료 시간
    processed_at: Optional[datetime] = Field(
        None,
        description="처리 완료 시간"
    )
    # 수정 시간
    updated_at: datetime = Field(
        ...,
        description="수정 시간"
    )
    # SQLAlchemy Model 데이터를 Pydantic 객체로 변환 허용
    class Config:
        from_attributes = True