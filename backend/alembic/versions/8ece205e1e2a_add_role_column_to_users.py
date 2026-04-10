"""Add role column to users

Revision ID: 8ece205e1e2a
Revises: fb79bf2f350b
Create Date: 2026-04-10 22:03:10.978071

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ece205e1e2a'
down_revision: Union[str, None] = 'fb79bf2f350b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='recruiter'))


def downgrade() -> None:
    op.drop_column('users', 'role')
