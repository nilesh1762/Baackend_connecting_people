"""add education  to UserModel

Revision ID: 8df55eb1d028
Revises: c22d5ec009b4
Create Date: 2026-07-19 18:41:45.670999

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8df55eb1d028'
down_revision: Union[str, None] = 'c22d5ec009b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This manually appends the education column to your live Oracle table
    op.add_column('USER_TABLE', sa.Column('education', sa.String(length=1000), nullable=True))


def downgrade() -> None:
    # This drops the column if you ever need to rollback the changes
    op.drop_column('USER_TABLE', 'education')
