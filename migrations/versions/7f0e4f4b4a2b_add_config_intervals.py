"""add interval columns to config profiles

Revision ID: 7f0e4f4b4a2b
Revises: 4eefa1ce1f7a
Create Date: 2025-10-24 18:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f0e4f4b4a2b"
down_revision: Union[str, Sequence[str], None] = "4eefa1ce1f7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add scheduling interval columns."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("config_profiles")}

    if "scan_interval_seconds" not in existing_columns:
        op.add_column(
            "config_profiles",
            sa.Column(
                "scan_interval_seconds",
                sa.Float(),
                nullable=False,
                server_default="10.0",
            ),
        )

    if "close_interval_seconds" not in existing_columns:
        op.add_column(
            "config_profiles",
            sa.Column(
                "close_interval_seconds",
                sa.Float(),
                nullable=False,
                server_default="5.0",
            ),
        )

    if "open_interval_seconds" not in existing_columns:
        op.add_column(
            "config_profiles",
            sa.Column(
                "open_interval_seconds",
                sa.Float(),
                nullable=False,
                server_default="5.0",
            ),
        )

    if bind.dialect.name != "sqlite":
        # remove server defaults when backend supports ALTER COLUMN
        op.alter_column(
            "config_profiles",
            "scan_interval_seconds",
            server_default=None,
        )
        op.alter_column(
            "config_profiles",
            "close_interval_seconds",
            server_default=None,
        )
        op.alter_column(
            "config_profiles",
            "open_interval_seconds",
            server_default=None,
        )


def downgrade() -> None:
    """Drop scheduling interval columns."""
    op.drop_column("config_profiles", "open_interval_seconds")
    op.drop_column("config_profiles", "close_interval_seconds")
    op.drop_column("config_profiles", "scan_interval_seconds")
