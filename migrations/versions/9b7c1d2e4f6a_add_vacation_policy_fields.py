"""add_vacation_policy_fields

Revision ID: 9b7c1d2e4f6a
Revises: 8f6d5a1c3e2b
Create Date: 2026-06-05 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b7c1d2e4f6a"
down_revision: str | Sequence[str] | None = "8f6d5a1c3e2b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("user_settings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("holiday_state", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("employment_start_date", sa.Date(), nullable=True))

    with op.batch_alter_table("time_entries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("vacation_days", sa.Numeric(precision=4, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("time_entries", schema=None) as batch_op:
        batch_op.drop_column("vacation_days")

    with op.batch_alter_table("user_settings", schema=None) as batch_op:
        batch_op.drop_column("employment_start_date")
        batch_op.drop_column("holiday_state")
