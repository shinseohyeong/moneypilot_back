"""add chatbot conversations

Revision ID: b87821ea3883
Revises: 54aae840dcb3
Create Date: 2026-07-10 11:27:22.850201

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b87821ea3883"
down_revision: Union[str, Sequence[str], None] = "54aae840dcb3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """챗봇 대화방 테이블과 메시지 연결 컬럼을 추가합니다."""

    op.create_table(
        "chatbot_conversations",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "chat_type",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_chatbot_conversations_user_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_chatbot_conversations_user_id",
        "chatbot_conversations",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_chatbot_conversations_chat_type",
        "chatbot_conversations",
        ["chat_type"],
        unique=False,
    )

    op.add_column(
        "chatbot_messages",
        sa.Column(
            "conversation_id",
            sa.BigInteger(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_chatbot_messages_conversation_id",
        "chatbot_messages",
        ["conversation_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_chatbot_messages_conversation_id",
        "chatbot_messages",
        "chatbot_conversations",
        ["conversation_id"],
        ["id"],
    )


def downgrade() -> None:
    """챗봇 대화방 관련 변경을 제거합니다."""

    op.drop_constraint(
        "fk_chatbot_messages_conversation_id",
        "chatbot_messages",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_chatbot_messages_conversation_id",
        table_name="chatbot_messages",
    )

    op.drop_column(
        "chatbot_messages",
        "conversation_id",
    )

    op.drop_index(
        "ix_chatbot_conversations_chat_type",
        table_name="chatbot_conversations",
    )

    op.drop_index(
        "ix_chatbot_conversations_user_id",
        table_name="chatbot_conversations",
    )

    op.drop_table("chatbot_conversations")