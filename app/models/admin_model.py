from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)

from app.core.database import Base

class TokenUsageLog(Base):
    __tablename__ = "token_usage_logs"
    # 사용량 기록 id
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 어떤 사용자인지
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False, # 누가 얼마나 사용했는지 알아야해서 False로 바꿈
    )
    # 어떤 요청에서 발생했는지
    # consumption | finance | stock | news | chatbot | summary 등
    feature_type = Column(String(50), nullable=False)

    # 예: gpt-4o-mini, text-embedding-3-small 등
    model_name = Column(String(100), nullable=False)
    # 입력 토큰
    prompt_tokens = Column(Integer, nullable=False, server_default=text("0"))
    # 출력 토큰
    completion_tokens = Column(Integer, nullable=False, server_default=text("0"))
    # 질문을 vector로 바꾼 토큰
    embedding_tokens = Column(Integer, nullable=False, server_default=text("0"))
    # 총합
    total_tokens = Column(Integer, nullable=False, server_default=text("0"))
    # 비용 계산용
    estimated_cost = Column(DECIMAL(12, 6), nullable=False, server_default=text("0"))

    usage_date = Column(Date, nullable=False)

    created_at = Column(DateTime, server_default=func.now())


class TokenLimitSetting(Base):
    __tablename__ = "token_limit_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 하루 사용 가능량
    daily_token_limit = Column(Integer, nullable=False)
    # 사용 제한 여부
    is_active = Column(Boolean, nullable=False, default=True)
    # 설정만든 날짜
    created_at = Column(DateTime, server_default=func.now())
    # 재헌 수정 날짜
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )