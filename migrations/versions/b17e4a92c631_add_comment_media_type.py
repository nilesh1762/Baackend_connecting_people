"""add media type to post comments

Revision ID: b17e4a92c631
Revises: 8df55eb1d028
Create Date: 2026-10-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b17e4a92c631"
down_revision: Union[str, None] = "8df55eb1d028"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "POST_COMMENTS_TABLE",
        sa.Column("MEDIA_TYPE", sa.String(length=20), nullable=True),
    )
    op.execute(
        "UPDATE POST_COMMENTS_TABLE "
        "SET MEDIA_TYPE = 'image' "
        "WHERE MEDIA_URL IS NOT NULL AND MEDIA_TYPE IS NULL"
    )


def downgrade() -> None:
    op.drop_column("POST_COMMENTS_TABLE", "MEDIA_TYPE")
