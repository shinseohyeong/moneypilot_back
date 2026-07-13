"""add agent chat tables

Revision ID: 696816428afc
Revises: 54aae840dcb3
Create Date: 2026-07-10 10:24:56.262973
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "696816428afc"
down_revision: Union[str, Sequence[str], None] = "54aae840dcb3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agent 채팅 세션 및 메시지 테이블을 생성합니다."""

    op.create_table(
        "agent_chat_sessions",
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
            "title",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "chat_type",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_agent_chat_sessions_user_id"),
        "agent_chat_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "agent_chat_messages",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "session_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "intent",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "used_tools",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "referenced_summary_id",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "disclaimer",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["referenced_summary_id"],
            ["monthly_spending_summaries.id"],
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["agent_chat_sessions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_agent_chat_messages_session_id"),
        "agent_chat_messages",
        ["session_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_agent_chat_messages_user_id"),
        "agent_chat_messages",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Agent 채팅 세션 및 메시지 테이블을 삭제합니다."""

    op.drop_index(
        op.f("ix_agent_chat_messages_user_id"),
        table_name="agent_chat_messages",
    )

    op.drop_index(
        op.f("ix_agent_chat_messages_session_id"),
        table_name="agent_chat_messages",
    )

    op.drop_table("agent_chat_messages")

    op.drop_index(
        op.f("ix_agent_chat_sessions_user_id"),
        table_name="agent_chat_sessions",
    )

    op.drop_table("agent_chat_sessions")