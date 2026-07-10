# app/models/chatbot_conversation_model.py

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    func,
)

from app.core.database import Base


class ChatbotConversation(Base):
    __tablename__ = "chatbot_conversations"

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

    # stock | finance | consumption 등
    chat_type = Column(
        String(30),
        nullable=False,
        index=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )