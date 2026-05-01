"""add status column to tips

Revision ID: 5f4b2e9d1a3c
Revises: f8a2c1d0e9ab
Create Date: 2026-04-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5f4b2e9d1a3c"
down_revision: Union[str, Sequence[str], None] = "f8a2c1d0e9ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("tips", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default="published",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("tips", schema=None) as batch_op:
        batch_op.drop_column("status")
