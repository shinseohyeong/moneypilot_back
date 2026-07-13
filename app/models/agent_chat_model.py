from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)

from app.core.database import Base


class AgentChatSession(Base):
    """
    Agent 대화방 정보를 저장한다.

    chat_type은 프론트에서 전달받지 않는다.
    Router가 판단한 intent를 기준으로 백엔드에서 결정한다.
    """

    __tablename__ = "agent_chat_sessions"

    __table_args__ = (
        Index(
            "ix_agent_chat_sessions_user_updated",
            "user_id",
            "updated_at",
        ),
    )

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title = Column(
        String(255),
        nullable=True,
    )

    # general | consumption | finance | stock | mixed
    chat_type = Column(
        String(30),
        nullable=False,
        default="general",
        server_default="general",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AgentChatMessage(Base):
    """
    Agent 대화방 안의 개별 메시지를 저장한다.
    """

    __tablename__ = "agent_chat_messages"

    __table_args__ = (
        Index(
            "ix_agent_chat_messages_session_created",
            "session_id",
            "created_at",
        ),
    )

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    session_id = Column(
        BigInteger,
        ForeignKey("agent_chat_sessions.id"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # user | assistant | system | tool
    role = Column(
        String(20),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    # Router가 판단한 action
    intent = Column(
        String(50),
        nullable=True,
    )

    # 사용된 Tool 이름을 JSON 문자열로 저장
    used_tools = Column(
        Text,
        nullable=True,
    )

    # 소비 분석 답변이 참고한 월별 요약 ID
    # 백엔드 내부 추적용으로 유지한다.
    referenced_summary_id = Column(
        BigInteger,
        ForeignKey("monthly_spending_summaries.id"),
        nullable=True,
    )

    # 투자 및 금융상품 관련 유의 문구
    disclaimer = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )