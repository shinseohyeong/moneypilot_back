# ==========================================
# 파일 위치 :
# app/models/card_statement_model.py
# 역할 :
# card_statements 테이블 ORM 모델
# ==========================================
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    TIMESTAMP,
    ForeignKey
)
from sqlalchemy.sql import func

from app.core.database import Base

# ==========================================
# 카드 명세서 파일 테이블
# ==========================================
class CardStatement(Base):
    __tablename__ = "card_statements"

    # PK
    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
        autoincrement=True
    )

    # 사용자 ID
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False
    )

    # 파일명
    # ex) samsung_card.xlsx
    file_name = Column(
        String(255),
        nullable=False
    )

    # 저장 경로
    file_url = Column(
        String(500),
        nullable=False
    )

    # 파일 타입
    # XLSX / XLS / CSV / PDF
    file_type = Column(
        String(20),
        nullable=False
    )

    # 처리 상태
    # PROCESSING
    # COMPLETED
    # FAILED
    status = Column(
        String(20),
        default="PROCESSING"
    )

    # 카드명
    # 카드사별 거래내역 분리 목적
    # ex) 삼성카드, 현대카드
    card_name = Column(
        String(20),
        nullable=False
    )

    # 에러메세지
    error_message = Column(
        Text
    )

    # 업로드 시간
    uploaded_at = Column(
        TIMESTAMP,
        default=func.now()
    )

    # 처리 완료 시간
    processed_at = Column(
        TIMESTAMP,
        nullable=True
    )
    
    # 수정 시간
    updated_at = Column(
        TIMESTAMP,
        default=func.now(),
        onupdate=func.now()
    )