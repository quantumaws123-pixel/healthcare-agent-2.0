"""add_user_status_and_profile_tables

Revision ID: e26b3a01b64a
Revises: 328660e03ab4
Create Date: 2026-06-30 22:18:38.044872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e26b3a01b64a'
down_revision: Union[str, Sequence[str], None] = '328660e03ab4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add status column to users table
    op.add_column('users', sa.Column('status', sa.String(20), nullable=False, server_default='approved'))
    
    # Create doctor_profiles table
    op.create_table(
        'doctor_profiles',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('user_id', sa.String(50), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('specialization', sa.String(100), nullable=True),
        sa.Column('hospital', sa.String(200), nullable=True),
        sa.Column('experience_years', sa.Integer, nullable=True),
        sa.Column('approved_by', sa.String(50), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_doctor_user_id', 'doctor_profiles', ['user_id'])
    
    # Create patient_profiles table  
    op.create_table(
        'patient_profiles',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('user_id', sa.String(50), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('patient_id', sa.String(50), nullable=True),  # Links to patient_records.patient_id
        sa.Column('assigned_doctor_id', sa.String(50), sa.ForeignKey('doctor_profiles.id', ondelete='SET NULL'), nullable=True),
        sa.Column('age', sa.Integer, nullable=True),
        sa.Column('gender', sa.String(10), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    )
    op.create_index('idx_patient_user_id', 'patient_profiles', ['user_id'])
    op.create_index('idx_patient_patient_id', 'patient_profiles', ['patient_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_patient_patient_id', table_name='patient_profiles')
    op.drop_index('idx_patient_user_id', table_name='patient_profiles')
    op.drop_table('patient_profiles')
    
    op.drop_index('idx_doctor_user_id', table_name='doctor_profiles')
    op.drop_table('doctor_profiles')
    
    op.drop_column('users', 'status')
