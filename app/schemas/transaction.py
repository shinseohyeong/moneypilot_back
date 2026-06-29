# ==========================================
# 파일 위치 : app/schemas/transaction.py
# 역할 : API 요청/응답 스키마 정의
#       DB모델과 분리함으로써 API 응답 형태를 독립적으로 관리
# ==========================================
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

# ==========================================
# 수기 입력 받을 때 사용하는 Schema
# 사용자 -> 서버
# 예:
# 카카오톡 정산
# 현금 사용
# ==========================================
class TransactionCreate(BaseModel):
    # 거래 날짜
    transaction_date: date
   
    # 가맹점명
    # 카드:
    # 스타벅스
    # 수기:
    # 친구 정산
    merchant_name: str

    # 상세 설명
    # 예:
    # 생일 케이크
    description: Optional[str] = None

    # 금액
    amount: Decimal

    # 소비 카테고리
    # 식비
    # 쇼핑
    category: Optional[str] = None

    # 반복 결제 여부
    # OTT 같은 구독 서비스
    is_recurring: bool = False

    # 고정/변동 지출
    # FIXED
    # VARIABLE
    expense_type: str = "VARIABLE"

# ==========================================
# 조회 응답 Schema
# 서버 -> 사용자
# ==========================================
class TransactionResponse(BaseModel):
    # 거래 ID
    id:int
    # 사용자 ID
    user_id:int

    # 카드 명세서 ID
    # 파일 업로드:
    # 값 존재
    # 수기 입력:
    # NULL
    statement_id:Optional[int]

    transaction_date:date
    # 2026-06 형태
    month:str
    # 가맹점명
    merchant_name:str
    # 설명
    description:Optional[str]
    # 가격
    amount:Decimal
    # 소비 카테고리
    category:Optional[str]
    # 반복 결제 여부
    is_recurring:bool
    # 고정비/ 변동비
    expense_type:str
    # 등록일
    created_at:datetime
    # 수정일
    updated_at:datetime

    class Config:
        from_attributes=True