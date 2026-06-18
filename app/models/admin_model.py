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
)

from app.core.database import Base


class TokenUsageLog(Base):
    __tablename__ = "token_usage_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    # consumption | finance | stock | news | chatbot | summary 등
    feature_type = Column(String(50), nullable=False)

    # 예: gpt-4o-mini, text-embedding-3-small 등
    model_name = Column(String(100), nullable=False)

    prompt_tokens = Column(Integer, nullable=False, default=0)

    completion_tokens = Column(Integer, nullable=False, default=0)

    embedding_tokens = Column(Integer, nullable=False, default=0)

    total_tokens = Column(Integer, nullable=False, default=0)

    estimated_cost = Column(DECIMAL(12, 6), nullable=False, default=0)

    usage_date = Column(Date, nullable=False)

    created_at = Column(DateTime, server_default=func.now())


class TokenLimitSetting(Base):
    __tablename__ = "token_limit_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    daily_token_limit = Column(Integer, nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )