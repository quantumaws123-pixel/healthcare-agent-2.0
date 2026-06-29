"""Initial database schema with patient_records and ml_models tables

Revision ID: b1e039b53fc2
Revises: 
Create Date: 2026-06-29 11:27:09.086909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1e039b53fc2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Create patient_records and ml_models tables.
    
    This migration creates the initial database schema for Healthcare Agent 2.0:
    - patient_records: Time-series patient monitoring data with composite primary key
    - ml_models: ML model versioning and metadata tracking
    
    Includes all indexes for query optimization per Requirements 2.1, 2.6.
    """
    
    # Create patient_records table
    op.create_table(
        'patient_records',
        # Composite Primary Key
        sa.Column('patient_id', sa.String(length=50), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        
        # Demographics
        sa.Column('patient_name', sa.String(length=100), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(length=10), nullable=True),
        sa.Column('bmi', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('smoking_status', sa.String(length=20), nullable=True),
        sa.Column('alcohol_consumption', sa.String(length=20), nullable=True),
        sa.Column('disease_type', sa.String(length=50), nullable=True),
        
        # Clinical Vitals
        sa.Column('heart_rate', sa.Integer(), nullable=True),
        sa.Column('systolic_bp', sa.Integer(), nullable=True),
        sa.Column('diastolic_bp', sa.Integer(), nullable=True),
        sa.Column('spo2', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('respiratory_rate', sa.Integer(), nullable=True),
        sa.Column('body_temperature', sa.DECIMAL(precision=4, scale=2), nullable=True),
        
        # Ideal Twin (Prescribed Plan)
        sa.Column('expected_steps', sa.Integer(), nullable=True),
        sa.Column('expected_sleep_hours', sa.DECIMAL(precision=4, scale=2), nullable=True),
        sa.Column('water_intake_goal', sa.Integer(), nullable=True),
        
        # Real Twin (Actual Behavior)
        sa.Column('actual_steps', sa.Integer(), nullable=True),
        sa.Column('actual_sleep_hours', sa.DECIMAL(precision=4, scale=2), nullable=True),
        sa.Column('water_intake', sa.Integer(), nullable=True),
        sa.Column('medication_taken', sa.String(length=3), nullable=True),
        sa.Column('exercise_completed', sa.String(length=3), nullable=True),
        sa.Column('diet_compliance', sa.DECIMAL(precision=5, scale=2), nullable=True),
        
        # Computed Scores
        sa.Column('compliance_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('ideal_health_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('real_health_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('deviation_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('recovery_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        
        # AI Predictions
        sa.Column('readmission_probability', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=True),
        sa.Column('health_trend', sa.String(length=20), nullable=True),
        sa.Column('recovery_status', sa.String(length=50), nullable=True),
        sa.Column('doctor_recommendation', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('patient_id', 'day', name='pk_patient_records')
    )
    
    # Create indexes for patient_records (Requirement 2.6)
    op.create_index('idx_patient_id', 'patient_records', ['patient_id'])
    op.create_index('idx_day', 'patient_records', ['day'])
    op.create_index('idx_disease_type', 'patient_records', ['disease_type'])
    op.create_index('idx_risk_level', 'patient_records', ['risk_level'])
    op.create_index('idx_recovery_status', 'patient_records', ['recovery_status'])
    
    # Create ml_models table
    op.create_table(
        'ml_models',
        # Primary Key
        sa.Column('model_id', sa.Integer(), autoincrement=True, nullable=False),
        
        # Model Identification
        sa.Column('model_version', sa.String(length=20), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('model_path', sa.String(length=255), nullable=False),
        
        # Training Metadata
        sa.Column('training_date', sa.TIMESTAMP(), nullable=False),
        sa.Column('dataset_size', sa.Integer(), nullable=False),
        
        # Evaluation Metrics
        sa.Column('accuracy', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('precision', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('recall', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('f1_score', sa.DECIMAL(precision=5, scale=4), nullable=True),
        sa.Column('auc_roc', sa.DECIMAL(precision=5, scale=4), nullable=True),
        
        # Deployment Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('model_id', name='pk_ml_models'),
        sa.UniqueConstraint('model_version', name='uq_ml_models_model_version')
    )


def downgrade() -> None:
    """Downgrade schema - Drop patient_records and ml_models tables."""
    
    # Drop indexes first
    op.drop_index('idx_recovery_status', table_name='patient_records')
    op.drop_index('idx_risk_level', table_name='patient_records')
    op.drop_index('idx_disease_type', table_name='patient_records')
    op.drop_index('idx_day', table_name='patient_records')
    op.drop_index('idx_patient_id', table_name='patient_records')
    
    # Drop tables
    op.drop_table('ml_models')
    op.drop_table('patient_records')
