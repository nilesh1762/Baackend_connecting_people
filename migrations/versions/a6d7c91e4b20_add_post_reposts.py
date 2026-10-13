"""add post reposts

Revision ID: a6d7c91e4b20
Revises: e42b106c9381
Create Date: 2026-10-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6d7c91e4b20"
down_revision: Union[str, None] = "e42b106c9381"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "POST_REPOSTS_TABLE",
        sa.Column("ID", sa.Integer(), sa.Identity(start=1), primary_key=True),
        sa.Column(
            "USER_ID",
            sa.Integer(),
            sa.ForeignKey("USER_TABLE.ID", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "POST_ID",
            sa.Integer(),
            sa.ForeignKey("POSTS_TABLE.ID", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "CREATED_AT",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "USER_ID",
            "POST_ID",
            name="POST_REPOST_USER_POST_UQ",
        ),
    )
    op.create_index(
        "ix_POST_REPOSTS_TABLE_USER_ID",
        "POST_REPOSTS_TABLE",
        ["USER_ID"],
    )
    op.create_index(
        "ix_POST_REPOSTS_TABLE_POST_ID",
        "POST_REPOSTS_TABLE",
        ["POST_ID"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_POST_REPOSTS_TABLE_POST_ID",
        table_name="POST_REPOSTS_TABLE",
    )
    op.drop_index(
        "ix_POST_REPOSTS_TABLE_USER_ID",
        table_name="POST_REPOSTS_TABLE",
    )
    op.drop_table("POST_REPOSTS_TABLE")
