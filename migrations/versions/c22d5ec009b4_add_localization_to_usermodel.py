"""add localization to UserModel

Revision ID: c22d5ec009b4
Revises: None
Create Date: 2026-07-19 17:35:53.180396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c22d5ec009b4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This manually appends the localization column to your live Oracle table
    op.add_column('USER_TABLE', sa.Column('localization', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    # This drops the column if you ever need to rollback the changes
    op.drop_column('USER_TABLE', 'localization')
