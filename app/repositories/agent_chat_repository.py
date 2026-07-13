from datetime import datetime

from sqlalchemy.orm import Session

from app.models.agent_chat_model import (
    AgentChatMessage,
    AgentChatSession,
)


class AgentChatRepository:
    """
    Agent 대화방과 메시지 저장/조회 Repository.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        user_id: int,
        title: str | None = None,
        chat_type: str = "general",
    ) -> AgentChatSession:
        session = AgentChatSession(
            user_id=user_id,
            title=title,
            chat_type=chat_type,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session_by_id(
        self,
        session_id: int,
        user_id: int,
    ) -> AgentChatSession | None:
        return (
            self.db.query(AgentChatSession)
            .filter(
                AgentChatSession.id == session_id,
                AgentChatSession.user_id == user_id,
            )
            .first()
        )

    def list_sessions_by_user(
        self,
        user_id: int,
        limit: int = 20,
    ) -> list[AgentChatSession]:
        return (
            self.db.query(AgentChatSession)
            .filter(
                AgentChatSession.user_id == user_id
            )
            .order_by(
                AgentChatSession.updated_at.desc()
            )
            .limit(limit)
            .all()
        )

    def get_last_message(
        self,
        session_id: int,
    ) -> AgentChatMessage | None:
        return (
            self.db.query(AgentChatMessage)
            .filter(
                AgentChatMessage.session_id == session_id
            )
            .order_by(
                AgentChatMessage.created_at.desc(),
                AgentChatMessage.id.desc(),
            )
            .first()
        )

    def create_message(
        self,
        session_id: int,
        user_id: int,
        role: str,
        content: str,
        intent: str | None = None,
        used_tools: str | None = None,
        referenced_summary_id: int | None = None,
        disclaimer: str | None = None,
    ) -> AgentChatMessage:
        message = AgentChatMessage(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            intent=intent,
            used_tools=used_tools,
            referenced_summary_id=referenced_summary_id,
            disclaimer=disclaimer,
        )

        session = (
            self.db.query(AgentChatSession)
            .filter(
                AgentChatSession.id == session_id
            )
            .first()
        )

        if session:
            session.updated_at = datetime.now()
            self.db.add(session)

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message

    def list_recent_messages(
        self,
        session_id: int,
        limit: int = 10,
    ) -> list[AgentChatMessage]:
        messages = (
            self.db.query(AgentChatMessage)
            .filter(
                AgentChatMessage.session_id == session_id
            )
            .order_by(
                AgentChatMessage.created_at.desc(),
                AgentChatMessage.id.desc(),
            )
            .limit(limit)
            .all()
        )

        return list(reversed(messages))

    def update_session_title(
        self,
        session: AgentChatSession,
        title: str,
    ) -> AgentChatSession:
        session.title = title
        session.updated_at = datetime.now()

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def update_session_chat_type(
        self,
        session: AgentChatSession,
        chat_type: str,
    ) -> AgentChatSession:
        session.chat_type = chat_type
        session.updated_at = datetime.now()

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session