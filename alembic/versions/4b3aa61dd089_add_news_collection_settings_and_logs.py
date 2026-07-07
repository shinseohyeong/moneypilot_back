"""add news collection settings and logs

Revision ID: 4b3aa61dd089
Revises: 53d66f7337b7
Create Date: 2026-06-29 17:33:32.552390

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4b3aa61dd089"
down_revision: Union[str, Sequence[str], None] = "53d66f7337b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "news_collection_settings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("keyword", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column(
            "provider",
            sa.String(length=50),
            server_default=sa.text("'NAVER'"),
            nullable=False,
        ),
        sa.Column(
            "interval_minutes",
            sa.Integer(),
            server_default=sa.text("60"),
            nullable=False,
        ),
        sa.Column(
            "display_count",
            sa.Integer(),
            server_default=sa.text("10"),
            nullable=False,
        ),
        sa.Column(
            "sort",
            sa.String(length=20),
            server_default=sa.text("'date'"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("last_collected_at", sa.DateTime(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "keyword",
            "provider",
            name="uk_news_collection_keyword_provider",
        ),
    )

    op.create_table(
        "news_collection_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("setting_id", sa.BigInteger(), nullable=True),
        sa.Column("keyword", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "requested_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "saved_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "duplicated_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["setting_id"],
            ["news_collection_settings.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("news_collection_logs")
    op.drop_table("news_collection_settings")