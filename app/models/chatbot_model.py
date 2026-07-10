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

from app.models.chatbot_conversation_model import ChatbotConversation


class ChatbotMessage(Base):
    __tablename__ = "chatbot_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # consumption | finance | stock | news 등
    chat_type = Column(String(30), nullable=False)

    user_message = Column(Text, nullable=False)

    agent_response = Column(Text, nullable=False)

    referenced_summary_id = Column(
        BigInteger,
        ForeignKey("monthly_spending_summaries.id"),
        nullable=True,
    )

    referenced_stock_id = Column(
        BigInteger,
        ForeignKey("stocks.id"),
        nullable=True,
    )

    referenced_news_id = Column(
        BigInteger,
        ForeignKey("news_articles.id"),
        nullable=True,
    )

    referenced_sector_id = Column(
        BigInteger,
        ForeignKey("stock_sectors.id"),
        nullable=True,
    )

    referenced_recommendation_id = Column(
        BigInteger,
        ForeignKey("financial_product_recommendations.id"),
        nullable=True,
    )

    conversation_id = Column(
        BigInteger,
        ForeignKey("chatbot_conversations.id"),
        nullable=True,
        index=True,
    )

    # 예: 사용한 tool 목록을 JSON 문자열 형태로 저장
    used_tools = Column(Text, nullable=True)

    disclaimer = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())