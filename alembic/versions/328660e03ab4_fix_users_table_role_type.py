"""fix_users_table_role_type

Revision ID: 328660e03ab4
Revises: a2f1c3d4e5b6
Create Date: 2026-06-30 21:05:09.875723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '328660e03ab4'
down_revision: Union[str, Sequence[str], None] = 'a2f1c3d4e5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cast the role column to use the existing userrole ENUM type."""
    # Alter the role column to use the userrole ENUM type (cast VARCHAR to ENUM)
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")


def downgrade() -> None:
    """Revert role column back to VARCHAR."""
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20)")
