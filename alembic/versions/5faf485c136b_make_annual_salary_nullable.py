"""make annual salary nullable

Revision ID: 5faf485c136b
Revises: ac2d7fc1fdb2
Create Date: 2026-07-01 16:27:22.645848

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = "5faf485c136b"
down_revision: Union[str, Sequence[str], None] = "ac2d7fc1fdb2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "finance_profiles",
        "annual_salary",
        existing_type=mysql.DECIMAL(precision=15, scale=2),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "finance_profiles",
        "annual_salary",
        existing_type=mysql.DECIMAL(precision=15, scale=2),
        nullable=False,
    )