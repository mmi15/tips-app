"""add deliveries table

Revision ID: 3bd9db164fbf
Revises: ccab0f3f17f1
Create Date: 2025-09-27 12:19:47.689839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bd9db164fbf'
down_revision: Union[str, Sequence[str], None] = 'ccab0f3f17f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
