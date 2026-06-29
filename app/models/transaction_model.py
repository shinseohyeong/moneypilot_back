# ==========================================
# 파일 위치 : app/models/transaction_model.py
# 역할 : 거래내역 테이블 ORM 모델
# 파일 업로드 + 수기 입력 거래 저장
# ==========================================

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Date,
    Numeric,
    Boolean,
    ForeignKey,
    TIMESTAMP
)

from sqlalchemy.sql import func

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    # 거래내역 ID
    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    # 사용자 ID
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    # 명세서 ID
    # 파일 업로드 : 값 존재
    # 수기 입력 : NULL
    statement_id = Column(
        BigInteger,
        ForeignKey("card_statements.id"),
        nullable=True
    )

    # 거래일
    transaction_date = Column(
        Date,
        nullable=False
    )

    # 거래 월
    # 예: 2026-06
    month = Column(
        String(7),
        nullable=False
    )

    # 가맹점명
    merchant_name = Column(
        String(100),
        nullable=False
    )

    # 결제 설명
    # 예: 친구 카톡 정산
    description = Column(
        String(255),
        nullable=True
    )

    # 결제 금액
    amount = Column(
        Numeric(15,2),
        nullable=False
    )

    # 소비 카테고리
    category = Column(
        String(50),
        nullable=True
    )

    # 반복 결제 여부
    is_recurring = Column(
        Boolean,
        default=False
    )

    # 고정/변동 지출
    # FIXED / VARIABLE
    expense_type = Column(
        String(20),
        default="VARIABLE"
    )

    # 생성 시간
    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    # 수정 시간
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )