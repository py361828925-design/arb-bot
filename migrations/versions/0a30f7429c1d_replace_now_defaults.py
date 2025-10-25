"""replace now() defaults with CURRENT_TIMESTAMP

Revision ID: 0a30f7429c1d
Revises: db42b22f16f9
Create Date: 2025-10-25 08:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a30f7429c1d"
down_revision: Union[str, Sequence[str], None] = "db42b22f16f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CURRENT_TIMESTAMP = sa.text("CURRENT_TIMESTAMP")
NOW_FUNC = sa.text("now()")


def upgrade() -> None:
    """Switch timestamp defaults to CURRENT_TIMESTAMP for SQLite compatibility."""
    timestamp_columns = {
        "config_audit_logs": ["created_at"],
        "config_profiles": ["created_at"],
        "position_groups": ["created_at", "updated_at"],
        "position_events": ["created_at"],
        "stats_snapshots": ["created_at"],
    }

    for table_name, columns in timestamp_columns.items():
        with op.batch_alter_table(table_name) as batch_ops:
            for column_name in columns:
                batch_ops.alter_column(
                    column_name,
                    existing_type=sa.DateTime(timezone=True),
                    server_default=CURRENT_TIMESTAMP,
                )


def downgrade() -> None:
    """Revert timestamp defaults back to now()."""
    timestamp_columns = {
        "config_audit_logs": ["created_at"],
        "config_profiles": ["created_at"],
        "position_groups": ["created_at", "updated_at"],
        "position_events": ["created_at"],
        "stats_snapshots": ["created_at"],
    }

    for table_name, columns in timestamp_columns.items():
        with op.batch_alter_table(table_name) as batch_ops:
            for column_name in columns:
                batch_ops.alter_column(
                    column_name,
                    existing_type=sa.DateTime(timezone=True),
                    server_default=NOW_FUNC,
                )
