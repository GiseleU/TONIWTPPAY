"""update_event_type_enum

Revision ID: 19ed919b4789
Revises: 253401148d8c
Create Date: 2026-02-27 13:04:08.133551

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19ed919b4789'
down_revision: Union[str, Sequence[str], None] = '253401148d8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new enum values to eventtype
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'INQUIRY_CONFIRMED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'ORDER_CREATION_FAILED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'PAYMENT_RECORDED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'PAYMENT_FAILED'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'OPT_OUT'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'BLOCKED_SEND'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'FAILED_SEND'")
    op.execute("ALTER TYPE eventtype ADD VALUE IF NOT EXISTS 'QUALITY_WARNING'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values easily
    # This would require recreating the enum without the values
    pass
