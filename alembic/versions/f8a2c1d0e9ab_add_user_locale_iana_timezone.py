"""add user locale and iana_timezone

Revision ID: f8a2c1d0e9ab
Revises: 3bd9db164fbf
Create Date: 2026-04-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f8a2c1d0e9ab"
down_revision: Union[str, Sequence[str], None] = "3bd9db164fbf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("locale", sa.String(length=16), server_default="es", nullable=False),
        )
        batch_op.add_column(
            sa.Column("iana_timezone", sa.String(length=64), nullable=True),
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("iana_timezone")
        batch_op.drop_column("locale")
