"""update user and oauth account schema

Revision ID: ac2d7fc1fdb2
Revises: 4b3aa61dd089
Create Date: 2026-06-30 15:20:40.992004
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ac2d7fc1fdb2"
down_revision: Union[str, Sequence[str], None] = "4b3aa61dd089"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # oauth_accounts.provider: VARCHAR(50) -> VARCHAR(30)
    op.alter_column(
        "oauth_accounts",
        "provider",
        existing_type=sa.String(length=50),
        type_=sa.String(length=30),
        existing_nullable=False,
    )

    # oauth_accounts: provider + provider_user_id 조합 중복 방지
    op.create_unique_constraint(
        "uq_oauth_accounts_provider_user_id",
        "oauth_accounts",
        ["provider", "provider_user_id"],
    )

    # users: 생년월일
    op.add_column(
        "users",
        sa.Column("birth_date", sa.Date(), nullable=True),
    )

    # users: 성별
    op.add_column(
        "users",
        sa.Column("gender", sa.String(length=10), nullable=True),
    )

    # users: 일반 사용자 / 관리자 구분
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'USER'"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("users", "role")
    op.drop_column("users", "gender")
    op.drop_column("users", "birth_date")

    op.drop_constraint(
        "uq_oauth_accounts_provider_user_id",
        "oauth_accounts",
        type_="unique",
    )

    op.alter_column(
        "oauth_accounts",
        "provider",
        existing_type=sa.String(length=30),
        type_=sa.String(length=50),
        existing_nullable=False,
    )