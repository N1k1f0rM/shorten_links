"""Add server_default to registered_at

Revision ID: 899902ac0fe9
Revises: 027846c25d35
Create Date: 2025-03-23 13:12:40.817708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '899902ac0fe9'
down_revision: Union[str, None] = '027846c25d35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
