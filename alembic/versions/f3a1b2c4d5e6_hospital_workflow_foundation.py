"""hospital_workflow_foundation

Adds the hospital entity, extends doctor/patient profiles, adds care_plans,
patient_vitals_daily, and medical_history tables.

Revision ID: f3a1b2c4d5e6
Revises: e26b3a01b64a
Create Date: 2026-07-01 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f3a1b2c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e26b3a01b64a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. hospitals                                                         #
    # ------------------------------------------------------------------ #
    op.create_table(
        'hospitals',
        sa.Column('id',           sa.String(50),  primary_key=True, nullable=False),
        sa.Column('name',         sa.String(200), nullable=False),
        sa.Column('code',         sa.String(20),  nullable=False, unique=True),
        sa.Column('address',      sa.Text(),      nullable=True),
        sa.Column('city',         sa.String(100), nullable=True),
        sa.Column('state',        sa.String(100), nullable=True),
        sa.Column('country',      sa.String(100), nullable=True, server_default='India'),
        sa.Column('phone',        sa.String(20),  nullable=True),
        sa.Column('email',        sa.String(255), nullable=True),
        sa.Column('departments',  sa.Text(),      nullable=True),   # comma-separated
        sa.Column('is_active',    sa.Boolean(),   nullable=False, server_default=sa.text('true')),
        sa.Column('created_at',   sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at',   sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_hospital_code', 'hospitals', ['code'])

    # ------------------------------------------------------------------ #
    # 2. Extend doctor_profiles                                            #
    # ------------------------------------------------------------------ #
    op.add_column('doctor_profiles', sa.Column('hospital_id',     sa.String(50),  nullable=True))
    op.add_column('doctor_profiles', sa.Column('license_number',  sa.String(50),  nullable=True))
    op.add_column('doctor_profiles', sa.Column('department',      sa.String(100), nullable=True))
    op.add_column('doctor_profiles', sa.Column('qualification',   sa.String(200), nullable=True))
    op.add_column('doctor_profiles', sa.Column('phone',           sa.String(20),  nullable=True))
    op.add_column('doctor_profiles', sa.Column('availability',    sa.String(20),  nullable=True, server_default='Available'))
    op.add_column('doctor_profiles', sa.Column('working_hours',   sa.String(100), nullable=True))
    op.add_column('doctor_profiles', sa.Column('avatar_url',      sa.String(500), nullable=True))

    # ------------------------------------------------------------------ #
    # 3. Extend patient_profiles — full clinical demographics              #
    # ------------------------------------------------------------------ #
    op.add_column('patient_profiles', sa.Column('hospital_id',          sa.String(50),  nullable=True))
    op.add_column('patient_profiles', sa.Column('disease_type',         sa.String(50),  nullable=True))
    op.add_column('patient_profiles', sa.Column('height_cm',            sa.Integer(),   nullable=True))
    op.add_column('patient_profiles', sa.Column('weight_kg',            sa.DECIMAL(5,2),nullable=True))
    op.add_column('patient_profiles', sa.Column('bmi',                  sa.DECIMAL(5,2),nullable=True))
    op.add_column('patient_profiles', sa.Column('blood_group',          sa.String(5),   nullable=True))
    op.add_column('patient_profiles', sa.Column('allergies',            sa.Text(),      nullable=True))
    op.add_column('patient_profiles', sa.Column('existing_conditions',  sa.Text(),      nullable=True))
    op.add_column('patient_profiles', sa.Column('smoking_status',       sa.String(20),  nullable=True))
    op.add_column('patient_profiles', sa.Column('alcohol_consumption',  sa.String(20),  nullable=True))
    op.add_column('patient_profiles', sa.Column('emergency_contact_name',  sa.String(100), nullable=True))
    op.add_column('patient_profiles', sa.Column('emergency_contact_phone', sa.String(20),  nullable=True))
    op.add_column('patient_profiles', sa.Column('current_medication',   sa.Text(),      nullable=True))
    op.add_column('patient_profiles', sa.Column('admission_date',       sa.String(20),  nullable=True))
    op.add_column('patient_profiles', sa.Column('discharge_date',       sa.String(20),  nullable=True))
    op.add_column('patient_profiles', sa.Column('monitoring_start_date',sa.String(20),  nullable=True))
    op.add_column('patient_profiles', sa.Column('monitoring_end_date',  sa.String(20),  nullable=True))
    op.add_column('patient_profiles', sa.Column('patient_status',       sa.String(20),  nullable=True, server_default='Monitoring'))
    op.add_column('patient_profiles', sa.Column('onboarding_completed', sa.Boolean(),   nullable=False, server_default=sa.text('false')))

    # ------------------------------------------------------------------ #
    # 4. care_plans — Doctor's prescribed Ideal Twin targets               #
    # ------------------------------------------------------------------ #
    op.create_table(
        'care_plans',
        sa.Column('id',                   sa.String(50),  primary_key=True, nullable=False),
        sa.Column('patient_user_id',      sa.String(50),  nullable=False),
        sa.Column('doctor_user_id',       sa.String(50),  nullable=False),
        sa.Column('daily_steps_goal',     sa.Integer(),   nullable=True, server_default='8000'),
        sa.Column('sleep_hours_goal',     sa.DECIMAL(4,2),nullable=True, server_default='8.0'),
        sa.Column('water_intake_goal_ml', sa.Integer(),   nullable=True, server_default='2000'),
        sa.Column('medication_schedule',  sa.Text(),      nullable=True),
        sa.Column('exercise_plan',        sa.Text(),      nullable=True),
        sa.Column('diet_plan',            sa.Text(),      nullable=True),
        sa.Column('followup_frequency_days', sa.Integer(),nullable=True, server_default='7'),
        sa.Column('monitoring_duration_days',sa.Integer(),nullable=True, server_default='30'),
        sa.Column('risk_threshold',       sa.DECIMAL(4,3),nullable=True, server_default='0.5'),
        sa.Column('emergency_threshold',  sa.DECIMAL(4,3),nullable=True, server_default='0.75'),
        sa.Column('notes',                sa.Text(),      nullable=True),
        sa.Column('is_active',            sa.Boolean(),   nullable=False, server_default=sa.text('true')),
        sa.Column('created_at',           sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at',           sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_care_plan_patient', 'care_plans', ['patient_user_id'])
    op.create_index('idx_care_plan_doctor',  'care_plans', ['doctor_user_id'])

    # ------------------------------------------------------------------ #
    # 5. patient_vitals_daily — Real Twin daily submissions by patient     #
    # ------------------------------------------------------------------ #
    op.create_table(
        'patient_vitals_daily',
        sa.Column('id',                  sa.String(50),  primary_key=True, nullable=False),
        sa.Column('patient_user_id',     sa.String(50),  nullable=False),
        sa.Column('log_date',            sa.String(20),  nullable=False),   # YYYY-MM-DD
        sa.Column('heart_rate',          sa.Integer(),   nullable=True),
        sa.Column('systolic_bp',         sa.Integer(),   nullable=True),
        sa.Column('diastolic_bp',        sa.Integer(),   nullable=True),
        sa.Column('spo2',                sa.DECIMAL(5,2),nullable=True),
        sa.Column('body_temperature',    sa.DECIMAL(4,2),nullable=True),
        sa.Column('weight_kg',           sa.DECIMAL(5,2),nullable=True),
        sa.Column('actual_steps',        sa.Integer(),   nullable=True),
        sa.Column('actual_sleep_hours',  sa.DECIMAL(4,2),nullable=True),
        sa.Column('water_intake_ml',     sa.Integer(),   nullable=True),
        sa.Column('medication_taken',    sa.String(3),   nullable=True),
        sa.Column('exercise_completed',  sa.String(3),   nullable=True),
        sa.Column('diet_compliance',     sa.DECIMAL(5,2),nullable=True),
        sa.Column('pain_level',          sa.Integer(),   nullable=True),   # 0-10
        sa.Column('mood',                sa.String(20),  nullable=True),
        sa.Column('symptoms',            sa.Text(),      nullable=True),
        sa.Column('notes',               sa.Text(),      nullable=True),
        sa.Column('created_at',          sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_vitals_patient_date', 'patient_vitals_daily', ['patient_user_id', 'log_date'])
    op.create_index('idx_vitals_patient',      'patient_vitals_daily', ['patient_user_id'])

    # ------------------------------------------------------------------ #
    # 6. medical_history — Doctor-managed clinical records                 #
    # ------------------------------------------------------------------ #
    op.create_table(
        'medical_history',
        sa.Column('id',                    sa.String(50),  primary_key=True, nullable=False),
        sa.Column('patient_user_id',       sa.String(50),  nullable=False),
        sa.Column('created_by_doctor_id',  sa.String(50),  nullable=True),
        sa.Column('past_diseases',         sa.Text(),      nullable=True),
        sa.Column('previous_admissions',   sa.Text(),      nullable=True),
        sa.Column('previous_surgeries',    sa.Text(),      nullable=True),
        sa.Column('family_history',        sa.Text(),      nullable=True),
        sa.Column('current_medications',   sa.Text(),      nullable=True),
        sa.Column('medication_history',    sa.Text(),      nullable=True),
        sa.Column('allergies',             sa.Text(),      nullable=True),
        sa.Column('lifestyle_smoking',     sa.String(20),  nullable=True),
        sa.Column('lifestyle_alcohol',     sa.String(20),  nullable=True),
        sa.Column('lifestyle_exercise',    sa.String(50),  nullable=True),
        sa.Column('lifestyle_diet',        sa.String(50),  nullable=True),
        sa.Column('doctor_notes',          sa.Text(),      nullable=True),
        sa.Column('discharge_summary',     sa.Text(),      nullable=True),
        sa.Column('created_at',            sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at',            sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_medical_history_patient', 'medical_history', ['patient_user_id'])


def downgrade() -> None:
    op.drop_index('idx_medical_history_patient',  table_name='medical_history')
    op.drop_table('medical_history')

    op.drop_index('idx_vitals_patient',       table_name='patient_vitals_daily')
    op.drop_index('idx_vitals_patient_date',  table_name='patient_vitals_daily')
    op.drop_table('patient_vitals_daily')

    op.drop_index('idx_care_plan_doctor',   table_name='care_plans')
    op.drop_index('idx_care_plan_patient',  table_name='care_plans')
    op.drop_table('care_plans')

    for col in ['onboarding_completed','patient_status','monitoring_end_date',
                'monitoring_start_date','discharge_date','admission_date',
                'current_medication','emergency_contact_phone','emergency_contact_name',
                'alcohol_consumption','smoking_status','existing_conditions',
                'allergies','blood_group','bmi','weight_kg','height_cm',
                'disease_type','hospital_id']:
        op.drop_column('patient_profiles', col)

    for col in ['avatar_url','working_hours','availability','phone',
                'qualification','department','license_number','hospital_id']:
        op.drop_column('doctor_profiles', col)

    op.drop_index('idx_hospital_code', table_name='hospitals')
    op.drop_table('hospitals')
