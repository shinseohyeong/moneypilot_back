# ============================================================
# 파일 위치: app/repositories/stock_chatbot_repository.py
# 역할:
#   - 주식 챗봇 답변 생성에 필요한 DB 데이터를 조회합니다.
#   - 챗봇 질문과 답변을 저장하고 대화기록을 조회합니다.
#   - repository 단에서는 commit/rollback을 처리하지 않습니다.
# ============================================================

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chatbot_conversation_model import ChatbotConversation
from app.models.chatbot_model import ChatbotMessage
from app.repositories.stock_report_repository import StockReportRepository


class StockChatbotRepository:
    """
    주식 챗봇 전용 repository입니다.
    """

    def __init__(self, db: Session):
        self.db = db
        self.stock_report_repository = StockReportRepository(db)

    def list_user_watchlist_stocks(self, user_id: int):
        """
        사용자의 관심종목 목록을 조회합니다.
        """
        return self.stock_report_repository.list_user_watchlist_stocks(
            user_id=user_id,
        )

    def get_latest_price(self, stock_id: int):
        """
        종목의 최신 시세를 조회합니다.
        """
        return self.stock_report_repository.get_latest_price(
            stock_id=stock_id,
        )

    def list_recent_news_summaries_by_stock(
        self,
        stock_id: int,
        limit: int = 3,
    ):
        """
        종목과 연결된 최근 뉴스 요약을 조회합니다.
        """
        return self.stock_report_repository.list_recent_news_summaries_by_stock(
            stock_id=stock_id,
            limit=limit,
        )

    def list_sector_insights_by_stock(
        self,
        stock_id: int,
        limit: int = 2,
    ):
        """
        종목과 연결된 섹터 인사이트를 조회합니다.
        """
        return self.stock_report_repository.list_sector_insights_by_stock(
            stock_id=stock_id,
            limit=limit,
        )

    # ------------------------------------------------------------
    # ChatbotMessage 저장
    # ------------------------------------------------------------
    def create_chatbot_message(
        self,
        conversation_id: int,
        user_id: int,
        chat_type: str,
        user_message: str,
        agent_response: str,
        referenced_stock_id: Optional[int] = None,
        used_tools: Optional[str] = None,
        disclaimer: Optional[str] = None,
    ) -> ChatbotMessage:
        """
        사용자 질문과 챗봇 최종 답변을 저장합니다.

        주의:
        - repository에서는 commit하지 않습니다.
        - commit/rollback은 service에서 처리합니다.
        """
        chatbot_message = ChatbotMessage(
            conversation_id=conversation_id,
            user_id=user_id,
            chat_type=chat_type,
            user_message=user_message,
            agent_response=agent_response,
            referenced_stock_id=referenced_stock_id,
            used_tools=used_tools,
            disclaimer=disclaimer,
        )

        self.db.add(chatbot_message)
        self.db.flush()

        return chatbot_message

    # ------------------------------------------------------------
    # ChatbotMessage 조회
    # ------------------------------------------------------------
    def list_stock_chat_history(
        self,
        user_id: int,
        limit: int = 30,
    ):
        """
        사용자의 최근 주식 챗봇 대화기록을 조회합니다.

        DB에서는 최신순으로 제한한 후,
        화면 표시를 위해 오래된 대화부터 반환합니다.
        """
        rows = (
            self.db.query(ChatbotMessage)
            .filter(
                ChatbotMessage.user_id == user_id,
                ChatbotMessage.chat_type == "stock",
            )
            .order_by(
                ChatbotMessage.created_at.desc(),
                ChatbotMessage.id.desc(),
            )
            .limit(limit)
            .all()
        )

        return list(reversed(rows))

    def count_stock_chat_history(
        self,
        user_id: int,
    ) -> int:
        """
        사용자의 전체 주식 챗봇 대화 수를 조회합니다.
        """
        return (
            self.db.query(ChatbotMessage)
            .filter(
                ChatbotMessage.user_id == user_id,
                ChatbotMessage.chat_type == "stock",
            )
            .count()
        )

    # ------------------------------------------------------------
    # ChatbotConversation
    # ------------------------------------------------------------
    def create_conversation(
        self,
        user_id: int,
        chat_type: str,
        title: str,
    ) -> ChatbotConversation:
        conversation = ChatbotConversation(
            user_id=user_id,
            chat_type=chat_type,
            title=title,
        )

        self.db.add(conversation)
        self.db.flush()

        return conversation


    def get_conversation(
        self,
        conversation_id: int,
        user_id: int,
    ) -> Optional[ChatbotConversation]:
        return (
            self.db.query(ChatbotConversation)
            .filter(
                ChatbotConversation.id == conversation_id,
                ChatbotConversation.user_id == user_id,
                ChatbotConversation.chat_type == "stock",
            )
            .first()
        )


    def touch_conversation(
        self,
        conversation: ChatbotConversation,
    ) -> None:
        """
        마지막 대화 시간을 갱신합니다.
        """
        conversation.updated_at = func.now()
        self.db.flush()


    def list_stock_conversations(
        self,
        user_id: int,
        limit: int = 30,
    ):
        return (
            self.db.query(ChatbotConversation)
            .filter(
                ChatbotConversation.user_id == user_id,
                ChatbotConversation.chat_type == "stock",
            )
            .order_by(
                ChatbotConversation.updated_at.desc(),
                ChatbotConversation.id.desc(),
            )
            .limit(limit)
            .all()
        )


    def count_stock_conversations(
        self,
        user_id: int,
    ) -> int:
        return (
            self.db.query(ChatbotConversation)
            .filter(
                ChatbotConversation.user_id == user_id,
                ChatbotConversation.chat_type == "stock",
            )
            .count()
        )


    def list_conversation_messages(
        self,
        conversation_id: int,
        user_id: int,
    ):
        return (
            self.db.query(ChatbotMessage)
            .filter(
                ChatbotMessage.conversation_id == conversation_id,
                ChatbotMessage.user_id == user_id,
                ChatbotMessage.chat_type == "stock",
            )
            .order_by(
                ChatbotMessage.created_at.asc(),
                ChatbotMessage.id.asc(),
            )
            .all()
        )