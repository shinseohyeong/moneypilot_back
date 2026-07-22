"""add insurance product rate columns

Revision ID: 23820d230543
Revises: 82862fbb4406
Create Date: 2026-07-22 12:09:29.433950
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "23820d230543"
down_revision: Union[str, Sequence[str], None] = "82862fbb4406"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """보험 상품 컬럼 3개 추가."""

    op.add_column(
        "insurance_products",
        sa.Column(
            "age",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "insurance_products",
        sa.Column(
            "male_insurance_rate",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.add_column(
        "insurance_products",
        sa.Column(
            "female_insurance_rate",
            sa.String(length=50),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """보험 상품 컬럼 3개 제거."""

    op.drop_column(
        "insurance_products",
        "female_insurance_rate",
    )

    op.drop_column(
        "insurance_products",
        "male_insurance_rate",
    )

    op.drop_column(
        "insurance_products",
        "age",
    )