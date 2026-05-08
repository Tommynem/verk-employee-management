"""add_employee_profile_settings

Revision ID: 8f6d5a1c3e2b
Revises: 3c6492af3a32
Create Date: 2026-05-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8f6d5a1c3e2b"
down_revision: Union[str, Sequence[str], None] = "3c6492af3a32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("user_settings", schema=None) as batch_op:
        batch_op.add_column(sa.Column("employee_first_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("employee_last_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("employee_job_role", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("employee_number", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("show_employee_id", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("employee_id_source", sa.String(), nullable=True))

    with op.batch_alter_table("user_settings", schema=None) as batch_op:
        batch_op.alter_column("show_employee_id", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("user_settings", schema=None) as batch_op:
        batch_op.drop_column("employee_id_source")
        batch_op.drop_column("show_employee_id")
        batch_op.drop_column("employee_number")
        batch_op.drop_column("employee_job_role")
        batch_op.drop_column("employee_last_name")
        batch_op.drop_column("employee_first_name")
