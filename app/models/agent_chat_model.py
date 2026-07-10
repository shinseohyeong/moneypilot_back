from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)

from app.core.database import Base


class AgentChatSession(Base):
    """
    Agent 대화방 정보를 저장하는 모델.
    ChatGPT처럼 하나의 대화 흐름을 session 단위로 관리한다.
    """

    __tablename__ = "agent_chat_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # 대화방 제목
    title = Column(String(255), nullable=True)

    # consumption | finance | stock | mixed 등
    chat_type = Column(String(30), nullable=False, default="consumption")

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AgentChatMessage(Base):
    """
    Agent 대화방 안의 개별 메시지를 저장하는 모델.
    user / assistant 메시지를 각각 한 row로 저장한다.
    """

    __tablename__ = "agent_chat_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

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
    role = Column(String(20), nullable=False)

    # 실제 메시지 내용
    content = Column(Text, nullable=False)

    # spending_summary | spending_rag | unknown 등
    intent = Column(String(50), nullable=True)

    # 사용한 tool 목록을 JSON 문자열 형태로 저장
    used_tools = Column(Text, nullable=True)

    # 참고한 월별 소비 요약 데이터
    referenced_summary_id = Column(
        BigInteger,
        ForeignKey("monthly_spending_summaries.id"),
        nullable=True,
    )

    # 금융/투자 유의 문구
    disclaimer = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())