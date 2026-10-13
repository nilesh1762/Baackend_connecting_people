"""add in-app post share recipients

Revision ID: e42b106c9381
Revises: d38b6e92f4a1
Create Date: 2026-10-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e42b106c9381"
down_revision: Union[str, None] = "d38b6e92f4a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "POST_SHARE_RECIPIENTS",
        sa.Column(
            "ID",
            sa.Integer(),
            sa.Identity(start=1),
            primary_key=True,
        ),
        sa.Column(
            "SHARE_ID",
            sa.Integer(),
            sa.ForeignKey("POST_SHARES_TABLE.ID", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "RECIPIENT_ID",
            sa.Integer(),
            sa.ForeignKey("USER_TABLE.ID", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "CREATED_AT",
            sa.DateTime(),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "SHARE_ID",
            "RECIPIENT_ID",
            name="POST_SHARE_RECIPIENT_UQ",
        ),
    )
    op.create_index(
        "POST_SHARE_RECIPIENT_RCP_IX",
        "POST_SHARE_RECIPIENTS",
        ["RECIPIENT_ID"],
    )


def downgrade() -> None:
    op.drop_index(
        "POST_SHARE_RECIPIENT_RCP_IX",
        table_name="POST_SHARE_RECIPIENTS",
    )
    op.drop_table("POST_SHARE_RECIPIENTS")
