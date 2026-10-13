"""make post shares event-based

Revision ID: d38b6e92f4a1
Revises: b17e4a92c631
Create Date: 2026-10-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d38b6e92f4a1"
down_revision: Union[str, None] = "b17e4a92c631"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "_USER_POST_SHARE_UC",
        "POST_SHARES_TABLE",
        type_="unique",
    )
    op.add_column(
        "POST_SHARES_TABLE",
        sa.Column("IDEMPOTENCY_KEY", sa.String(length=128), nullable=True),
    )
    op.create_unique_constraint(
        "USER_SHARE_IDEMPOTENCY_UC",
        "POST_SHARES_TABLE",
        ["USER_ID", "IDEMPOTENCY_KEY"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "USER_SHARE_IDEMPOTENCY_UC",
        "POST_SHARES_TABLE",
        type_="unique",
    )
    op.drop_column("POST_SHARES_TABLE", "IDEMPOTENCY_KEY")
    op.create_unique_constraint(
        "USER_POST_SHARE_UC",
        "POST_SHARES_TABLE",
        ["USER_ID", "POST_ID"],
    )
