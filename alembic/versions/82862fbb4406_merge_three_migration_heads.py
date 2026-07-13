"""merge three migration heads

Revision ID: 82862fbb4406
Revises: 696816428afc, 86369419f544, b87821ea3883
Create Date: 2026-07-13 17:08:05.320451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82862fbb4406'
down_revision: Union[str, Sequence[str], None] = ('696816428afc', '86369419f544', 'b87821ea3883')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
