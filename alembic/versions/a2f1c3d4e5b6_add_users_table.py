"""Add users table for auth system

Revision ID: a2f1c3d4e5b6
Revises: b1e039b53fc2
Create Date: 2026-07-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a2f1c3d4e5b6'
down_revision: Union[str, Sequence[str], None] = 'b1e039b53fc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id',              sa.String(50),  primary_key=True,  nullable=False),
        sa.Column('email',           sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=True),
        sa.Column('google_id',       sa.String(255), nullable=True),
        sa.Column('name',            sa.String(100), nullable=True),
        sa.Column('avatar_url',      sa.String(500), nullable=True),
        sa.Column('role',            sa.String(20),  nullable=False, server_default='patient'),
        sa.Column('is_active',       sa.Boolean(),   nullable=False, server_default=sa.text('true')),
        sa.Column('created_at',      sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at',      sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('email',     name='uq_users_email'),
        sa.UniqueConstraint('google_id', name='uq_users_google_id'),
    )
    op.create_index('idx_users_email',     'users', ['email'])
    op.create_index('idx_users_google_id', 'users', ['google_id'])


def downgrade() -> None:
    op.drop_index('idx_users_google_id', table_name='users')
    op.drop_index('idx_users_email',     table_name='users')
    op.drop_table('users')
