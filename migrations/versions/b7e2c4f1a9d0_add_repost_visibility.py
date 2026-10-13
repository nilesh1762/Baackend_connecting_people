"""add visibility to post reposts

Revision ID: b7e2c4f1a9d0
Revises: a6d7c91e4b20
Create Date: 2026-10-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e2c4f1a9d0"
down_revision: Union[str, None] = "a6d7c91e4b20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "POST_REPOSTS_TABLE",
        sa.Column(
            "VISIBILITY",
            sa.String(length=20),
            server_default="anyone",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("POST_REPOSTS_TABLE", "VISIBILITY")
