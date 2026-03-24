"""add last_message_at to conversation_state

Revision ID: a1b2c3d4e5f6
Revises: 5dd6ac3fefb8
Create Date: 2026-03-24 00:00:00.000000

"""
from typing import Union, Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '5dd6ac3fefb8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'conversation_states',
        sa.Column('last_message_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('conversation_states', 'last_message_at')
