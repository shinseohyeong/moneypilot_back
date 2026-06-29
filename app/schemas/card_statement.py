# ==========================================
# 파일 위치 : moneypilot_back/app/schemas/card_statement.py
# 역할 : API 요청과 응답에 사용되는 카드 명세서 관련 스키마 정의
#        DB 모델과 분리함으로써 api 응답형태를 독립적으로 관리
# ==========================================

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field

class CardStatementResponse(BaseModel):
    id: int = Field(..., description="카드 명세서 ID")
    user_id: int = Field(..., description="사용자 ID")

    file_name: str = Field(..., description="업로드된 파일 이름")
    file_url: str = Field(..., description="저장된 파일 경로")
    file_type: str = Field(..., description="파일 형식(XLSX, XLS, CSV, PDF)")

    status: str = Field(..., description="처리 상태")
    error_message: Optional[str] = Field(
        None,
        description="처리 실패 시 오류 메시지"
    )

    card_name: Optional[str] = Field(
        None,
        description="카드사 또는 카드명"
    )

    uploaded_at: datetime = Field(
        ...,
        description="파일 업로드 시각"
    )

    processed_at: Optional[datetime] = Field(
        None,
        description="파일 처리 완료 시각"
    )

    updated_at: datetime = Field(
        ...,
        description="마지막 수정 시각"
    )

    class Config:
        from_attributes = True