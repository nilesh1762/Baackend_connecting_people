"""add post moderation status

Revision ID: f3b8c91a62d4
Revises: e42b106c9381
Create Date: 2026-10-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3b8c91a62d4"
down_revision: Union[str, None] = "e42b106c9381"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "POSTS_TABLE",
        sa.Column(
            "MODERATION_STATUS",
            sa.String(length=20),
            server_default="approved",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("POSTS_TABLE", "MODERATION_STATUS")
