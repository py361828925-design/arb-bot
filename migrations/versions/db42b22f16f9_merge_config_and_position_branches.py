"""merge config and position branches

Revision ID: db42b22f16f9
Revises: c89f7f098ca4, 7f0e4f4b4a2b
Create Date: 2025-10-25 07:38:01.138174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db42b22f16f9'
down_revision: Union[str, Sequence[str], None] = ('c89f7f098ca4', '7f0e4f4b4a2b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
